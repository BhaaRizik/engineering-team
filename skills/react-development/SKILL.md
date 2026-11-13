---
name: react-development
description: Modern React and TypeScript engineering — function components and hooks, component composition, strict TypeScript typing for props and events, React Router and Vite SPAs, Next.js when SSR/SEO is needed, Styled Components theming (preferred; never Tailwind), semantic HTML5 and accessibility (WCAG), error boundaries, Suspense and lazy loading, and evidence-based performance optimization. Use when building, refactoring, or reviewing React components, hooks, pages, routing, styling, or frontend performance.
---

# React Development

## Purpose
Give `frontend` concrete practices for writing React components and pages. Folder structure and feature boundaries are in `frontend-architecture`; state, data fetching, and forms in `frontend-state-forms`; API contracts in `api-design`; frontend tests in `test-automation`.

## When to use
- Writing or refactoring components, hooks, pages, layouts, routes.
- Setting up a Vite or Next.js project, TypeScript config, theme, or lint rules.
- Accessibility or performance work.
- Reviewing React code.

## Version policy
- Detect versions from `package.json`/lockfile (React, TypeScript, router, Next.js, styled-components) before writing code. Use APIs available in those versions.
- New projects: current stable React and TypeScript; Vite + React Router for SPAs; Next.js (App Router) when SSR, SEO, or server rendering is required.
- React 19+ features (Actions, `useActionState`, `useOptimistic`, `use`, `ref` as a prop) and the React Compiler are available in modern projects — use them only if the project's version supports them.

## Core principles
1. **Components are functions of props and state.** Keep render pure; side-effects in event handlers first, `useEffect` only to synchronize with external systems.
2. **Composition over configuration.** `children`, slots, and compound components instead of 20 boolean props.
3. **Strict TypeScript.** `strict: true`, `noUncheckedIndexedAccess` where practical; no `any`; type props explicitly; let inference handle the rest.
4. **Semantic HTML first, ARIA second.**
5. **Presentation separate from logic.** Components render; hooks hold logic; services talk to APIs.
6. **Measure before optimizing.**

## Best practices
**Components**
- One component per file for exported components; small private subcomponents may live alongside.
- Props: `type ButtonProps = { variant?: 'primary' | 'secondary' } & React.ComponentPropsWithoutRef<'button'>` to inherit native attributes.
- Derive values during render instead of syncing them into state; avoid `useEffect` for derived data.
- Keys: stable IDs, never array index for reorderable lists.
- Custom hooks (`useXxx`) to extract reusable logic; they return data and callbacks, not JSX.
- Error boundaries around route segments and risky widgets (`react-error-boundary` or a class boundary); show recovery UI.
- `Suspense` + `React.lazy` for route-level code splitting.

**Styling — Styled Components (preferred for new projects)**
- Never Tailwind. Don't add CSS frameworks without a clear reason. In existing projects, follow the established styling approach.
- Theme tokens in `shared/theme/` (colors, spacing, typography, radii, breakpoints, shadows, z-index); typed via `styled.d.ts` (`DefaultTheme` augmentation); provided once by `ThemeProvider`.
- Light/dark/system: separate token sets, select via `prefers-color-scheme` + user preference persisted; avoid flash with an initial theme decision before render where possible.
- Transient props (`$variant`) so styling props don't reach the DOM.
- Primitives (`Button`, `Stack`, `Text`, `Card`, `Input`) in `shared/components/ui/`; feature components compose them.
- Responsive via theme breakpoint helpers; mobile-first.
- Use `css` helper for shared fragments; avoid dynamic interpolation creating many classes in hot lists.
- Trade-off to state when relevant: styled-components is a runtime CSS-in-JS library; in Next.js App Router it requires a style registry and client components. If a project needs heavy React Server Components usage, raise the trade-off with the user rather than switching silently. Check the library's current maintenance status when starting a new long-lived project.

**Accessibility**
- Native elements (`button`, `a`, `label`, `nav`, `main`, `dialog`) before divs with handlers.
- Every input has a label; errors linked with `aria-describedby`; `aria-invalid` on invalid fields.
- Keyboard: everything clickable is focusable and operable; visible focus styles; focus trap and return in modals; move focus on route change for SPAs.
- Color contrast ≥ WCAG AA; don't convey meaning by color alone; respect `prefers-reduced-motion`.
- Images have meaningful `alt` (or `alt=""` if decorative).

**Routing**
- React Router: route objects with lazy-loaded route modules; layouts with `<Outlet />`; protected routes check auth state but **the server still authorizes**.
- Next.js: thin `app/` route files importing from `features/`; Server Components by default; `'use client'` only where interactivity requires it.

**Performance**
- Code-split by route; lazy-load heavy, rarely used components.
- Virtualize long lists (e.g. TanStack Virtual) when rendering hundreds+ rows.
- `React.memo`/`useMemo`/`useCallback` only for measured problems or referential-stability requirements (memoized children, effect deps). With the React Compiler enabled, manual memoization is mostly unnecessary.
- Images: explicit dimensions, lazy loading, modern formats; `next/image` in Next.js.
- Watch bundle size (`vite-bundle-visualizer`, `@next/bundle-analyzer`); prefer tree-shakable imports.

**Tooling**
- ESLint with `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`; Prettier for formatting; `tsc --noEmit` in CI.
- Path aliases (`@/features/...`) configured in both `tsconfig` and Vite/Next.

## Implementation workflow
1. Inspect `package.json`, tsconfig, lint config, theme, existing components and conventions.
2. Locate the feature (see `frontend-architecture`); reuse existing shared primitives.
3. Define types (props, view models; API types from OpenAPI).
4. Build the component tree: page → feature components → shared primitives; logic in hooks.
5. Handle all states: loading, empty, error, success.
6. Accessibility pass (keyboard, labels, focus, contrast).
7. Tests with Vitest + React Testing Library (behavior, roles/labels).
8. Run typecheck, lint, tests, build with the project's package manager.

## Decision-making guidelines
- **Vite SPA vs. Next.js**: authenticated dashboards/internal tools → Vite + React Router. Public, SEO-sensitive, or content-heavy sites, or a need for server rendering/edge → Next.js.
- **New component vs. extending existing**: extend when the concept is the same; create new when variants would require conditionals for unrelated use cases.
- **Context vs. props**: props for 1–2 levels; context for cross-cutting, rarely changing values (theme, auth user, locale); store (`frontend-state-forms`) for frequently changing shared state.
- **Effect vs. event handler**: if it happens because the user did something → handler. If it must stay in sync with something external → effect.

## Anti-patterns
- Giant components (>200–300 lines) mixing fetching, state, and markup.
- `useEffect` chains to sync state from props/other state.
- `any`, non-null assertions everywhere, `as` casts hiding real type errors.
- `div onClick` without role/keyboard support.
- Inline style objects and duplicated styled blocks instead of theme tokens and primitives.
- Tailwind or a new CSS framework introduced without approval.
- Memoizing everything "for performance".
- `dangerouslySetInnerHTML` with untrusted content.

## Quality checklist
- [ ] Versions respected; no unsupported APIs.
- [ ] Strict typing; no `any`; props typed.
- [ ] Composition used; components focused; logic in hooks.
- [ ] Styling via theme tokens and shared primitives (or project convention).
- [ ] Loading/empty/error/success states handled; error boundary present for the route.
- [ ] Keyboard and screen-reader accessible; contrast OK.
- [ ] Route-level code splitting; no unjustified memoization.
- [ ] Typecheck, lint, tests, and build pass (output captured).

## Examples
```tsx
// shared/components/ui/Button.tsx
import styled, { css } from 'styled-components';

type Variant = 'primary' | 'secondary';
type ButtonProps = { variant?: Variant } & React.ComponentPropsWithoutRef<'button'>;

const StyledButton = styled.button<{ $variant: Variant }>`
  padding: ${({ theme }) => `${theme.space[2]} ${theme.space[4]}`};
  border-radius: ${({ theme }) => theme.radii.md};
  font: inherit;
  ${({ theme, $variant }) => $variant === 'primary'
    ? css`background: ${theme.colors.primary}; color: ${theme.colors.onPrimary};`
    : css`background: transparent; color: ${theme.colors.text}; border: 1px solid ${theme.colors.border};`}
  &:focus-visible { outline: 2px solid ${({ theme }) => theme.colors.focus}; outline-offset: 2px; }
  &:disabled { opacity: .5; cursor: not-allowed; }
`;

export function Button({ variant = 'primary', type = 'button', ...rest }: ButtonProps) {
  return <StyledButton $variant={variant} type={type} {...rest} />;
}
```
```tsx
// app/router/routes.tsx — route-level splitting
const ProductDetailsPage = lazy(() => import('@/features/products/pages/ProductDetailsPage'));
```

## References
- React documentation: https://react.dev/
- React — You Might Not Need an Effect: https://react.dev/learn/you-might-not-need-an-effect
- React Compiler: https://react.dev/learn/react-compiler
- TypeScript handbook & tsconfig reference: https://www.typescriptlang.org/docs/ · https://www.typescriptlang.org/tsconfig/
- Vite guide: https://vite.dev/guide/
- React Router: https://reactrouter.com/
- Next.js docs: https://nextjs.org/docs
- styled-components docs: https://styled-components.com/docs
- WCAG 2.2 quick reference: https://www.w3.org/WAI/WCAG22/quickref/
- WAI-ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
- MDN HTML elements: https://developer.mozilla.org/en-US/docs/Web/HTML/Element
- typescript-eslint: https://typescript-eslint.io/
