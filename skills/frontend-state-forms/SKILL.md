---
name: frontend-state-forms
description: Frontend state, data fetching, and forms — choosing between local state, Context, Zustand, Redux Toolkit, URL state, and TanStack Query; server vs. client state; centralized Axios client with interceptors; query keys, caching, invalidation, pagination, and optimistic updates; React Hook Form with Zod validation; async error handling; and authentication/session state. Use when adding data fetching or mutations, introducing or reviewing a store, building or validating forms, handling auth state, or debugging stale data and re-render issues in React.
---

# Frontend State & Forms

## Purpose
Help `frontend` pick the **simplest** state solution for each kind of state, integrate APIs consistently, and build robust forms. API contract standards are in `api-design`; token storage policy in `application-security`; feature placement in `frontend-architecture`.

## When to use
- Fetching or mutating server data.
- Sharing state between distant components.
- Building forms with validation.
- Handling login/session/permissions in the UI.
- Diagnosing stale data, duplicate requests, or excessive re-renders.

## Core principles
1. **Classify state first**: local UI, shared client, server, URL, form.
2. **Server state is a cache, not app state.** TanStack Query owns it; never copy it into Zustand/Redux.
3. **Simplest tool that works.** `useState` → lift state → Context (rarely changing) → store (frequently changing, widely shared).
4. **URL is state.** Filters, sort, pagination, selected tab → search params (shareable, reload-safe).
5. **Validate at the edge.** Zod schemas for forms and, where it matters, for API responses.
6. **Frontend validation is UX; backend validation is security.**

## State decision table
| State kind | Tool | Example |
|---|---|---|
| Local UI | `useState` / `useReducer` | Dropdown open, input text, wizard step |
| Rarely-changing cross-cutting | Context | Theme, locale, current user identity |
| Frequently-changing shared client state | Zustand (light) or Redux Toolkit (if the project uses it / needs devtools-heavy workflows, complex normalized client state) | Cart before checkout, multi-panel editor state |
| Server data | TanStack Query | Product list, order details, mutations |
| URL | Router search params | `?status=open&page=2&sort=createdAt,desc` |
| Form | React Hook Form + Zod | Checkout form, profile edit |

## Best practices
**Axios client (`shared/services/api/apiClient.ts`)**
- One instance: `baseURL` from validated env config, timeout, JSON headers, `withCredentials` if using cookie sessions.
- Request interceptor: attach auth (only if bearer tokens are used in memory); correlation ID if useful.
- Response interceptor: normalize errors into one typed `ApiError` (status, problem-details `title/detail/errors`, `traceId`); on 401 trigger a single-flight token refresh or logout — avoid infinite refresh loops and concurrent duplicate refreshes.
- Feature services return typed data (`Promise<Product[]>`), not Axios responses.

**TanStack Query**
- Query key factories per feature: `productKeys.list(filters)`, `productKeys.detail(id)` — keys include every parameter.
- Set `staleTime` deliberately (default 0 refetches often); configure `retry` to skip 4xx.
- Mutations: `onSuccess` → `invalidateQueries` for affected keys, or `setQueryData` for precise updates.
- Optimistic updates for low-risk, high-frequency actions (toggle, like): snapshot in `onMutate`, rollback in `onError`, invalidate in `onSettled`. Not for payments or irreversible actions.
- Pagination: include page/cursor in key; `placeholderData: keepPreviousData` for smooth paging; `useInfiniteQuery` for cursor feeds.
- Use `select` to derive view data and limit re-renders.
- Errors: render per-query error states; use error boundaries (`throwOnError`) for unrecoverable page-level failures.

**Zustand / Redux Toolkit**
- Small, feature-scoped stores; selectors to subscribe to slices (`useCartStore(s => s.items)`) to avoid re-renders.
- Actions encapsulate updates; no direct mutation from components.
- Persist only non-sensitive state (`persist` middleware) — never tokens or PII in `localStorage`.
- Redux Toolkit: `createSlice`, RTK Query only if the project already uses it instead of TanStack Query — don't mix two server-state libraries.

**Forms (React Hook Form + Zod)**
- Schema in `features/<f>/schemas/`; types via `z.infer`; `zodResolver`.
- Map server validation errors (problem-details `errors[]`) back to fields with `setError`.
- Accessible: labels, `aria-invalid`, error text linked with `aria-describedby`, focus first invalid field on submit.
- Disable submit while submitting; prevent double submission; show success/failure feedback.
- Use controlled components (`Controller`) only for non-native inputs.

**Authentication state**
- Source of truth for "logged in" is the server (session endpoint / token validity), cached via a query (`useCurrentUser`).
- Prefer HttpOnly Secure cookies (set by backend) or in-memory access tokens + refresh via HttpOnly cookie; never long-lived tokens in `localStorage`. Coordinate with `security`.
- On logout: clear query cache (`queryClient.clear()`), stores, and redirect.
- UI permission checks are cosmetic; the API enforces authorization.

## Implementation workflow
1. Classify each piece of state using the table.
2. Confirm the API contract (types from OpenAPI where available).
3. Write the feature service (typed), then query/mutation hooks with a key factory.
4. Build forms with schema + RHF; map server errors.
5. Wire loading, empty, error, success UI states.
6. Add tests: hooks/components with MSW or mocked services; form validation behavior (see `test-automation`).
7. Verify no duplicate fetching (React Query Devtools / network tab) and no unnecessary re-renders.

## Decision-making guidelines
- **Zustand vs. Redux Toolkit**: follow the project. New project: Zustand for modest shared client state; Redux Toolkit for large teams wanting strict conventions, complex client-side domain state, or heavy devtools/middleware use.
- **Context vs. store**: value changes often and many consumers → store with selectors; otherwise Context.
- **Invalidate vs. setQueryData**: invalidate by default (simple, correct); setQueryData when the response contains the full updated entity and refetch is expensive.
- **Optimistic vs. pessimistic**: optimistic only when failure is rare and rollback is harmless.
- **React 19 Actions (`useActionState`) vs. RHF**: simple forms in frameworks built around Actions (e.g. Next.js server actions) can use Actions; complex client-side validation → RHF + Zod.

## Anti-patterns
- Fetching in `useEffect` + `useState` when TanStack Query is available.
- Copying query data into a global store.
- One giant global store for everything.
- Query keys missing parameters (stale/wrong data).
- Tokens in `localStorage`; refresh-token logic duplicated in many places.
- Hand-rolled form state and validation for complex forms.
- Swallowing API errors or showing raw error objects to users.
- Duplicating backend business rules (pricing, permissions) in the frontend.

## Quality checklist
- [ ] Each state classified and using the simplest suitable tool.
- [ ] Single Axios client with normalized errors; feature services typed.
- [ ] Query keys complete; staleTime/retry deliberate; mutations invalidate correctly.
- [ ] Loading/empty/error/success states rendered.
- [ ] Forms: Zod schema, accessible errors, server errors mapped, double-submit prevented.
- [ ] No sensitive data persisted in browser storage.
- [ ] Tests cover validation and API success/error paths.

## Examples
```ts
// features/products/hooks/useProducts.ts
export const productKeys = {
  all: ['products'] as const,
  list: (f: ProductFilters) => [...productKeys.all, 'list', f] as const,
  detail: (id: string) => [...productKeys.all, 'detail', id] as const,
};

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: productKeys.list(filters),
    queryFn: () => productService.list(filters),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}
```
```tsx
// features/auth/schemas/loginSchema.ts + form usage
export const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'At least 8 characters'),
});
type LoginForm = z.infer<typeof loginSchema>;

const { register, handleSubmit, setError, formState: { errors, isSubmitting } } =
  useForm<LoginForm>({ resolver: zodResolver(loginSchema) });
```

## References
- React — Managing state: https://react.dev/learn/managing-state
- TanStack Query: https://tanstack.com/query/latest/docs/framework/react/overview
- TanStack Query — Optimistic updates: https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates
- Zustand: https://zustand.docs.pmnd.rs/
- Redux Toolkit: https://redux-toolkit.js.org/
- React Hook Form: https://react-hook-form.com/
- Zod: https://zod.dev/
- Axios interceptors: https://axios-http.com/docs/interceptors
- OWASP — HTML5 security / storage: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html
