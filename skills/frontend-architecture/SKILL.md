---
name: frontend-architecture
description: Feature-First (package-by-feature) frontend architecture for React/TypeScript apps — app/, shared/, and features/ layout, feature ownership of components/hooks/services/pages/types/schemas, public feature APIs via index.ts, rules for what belongs in shared/, routing composition, dependency direction and import boundaries, API layer placement, and scaling folder structures. Use when creating a new frontend project structure, adding a feature, deciding where code belongs, reviewing frontend organization, or refactoring a layer-based frontend.
---

# Frontend Architecture

## Purpose
Keep frontend codebases organized around business features so they scale without becoming a tangle of global folders. Component-level practices are in `react-development`; state/data/forms in `frontend-state-forms`; general architecture reasoning in `system-design`.

## When to use
- Bootstrapping a new React/Next.js codebase.
- Adding a feature or a page.
- Deciding whether code goes in a feature or `shared/`.
- Untangling cross-feature imports or a growing `components/` dump.

## Core principles
1. **Package by feature.** A feature owns everything specific to it: components, hooks, services, pages, types, schemas.
2. **`shared/` is earned.** Code moves to `shared/` only when ≥2 features genuinely need it *and* it contains no feature business rules.
3. **Explicit public APIs.** Other code imports a feature through its `index.ts`, not its internals.
4. **One-way dependencies.** `app → features → shared`. `shared` never imports from `features`; features avoid importing each other.
5. **Separate concerns inside a feature.** UI (components/pages) ← application logic (hooks) ← API communication (services).
6. **Adapt to size.** Small apps need fewer folders; never create empty folders to match a template.
7. **Respect existing structure.** In an existing project, follow its organization; propose migrations incrementally and with approval.

## Reference structure
```text
src/
├── app/                 # composition root: providers, router, layouts, app config
│   ├── providers/       # QueryClientProvider, ThemeProvider, store, auth
│   ├── router/          # route table; lazy imports of feature pages
│   ├── layouts/
│   ├── config/          # env parsing (validated), feature flags
│   └── App.tsx
├── shared/
│   ├── components/{ui,layout}/   # design-system primitives, page shells
│   ├── hooks/           # generic hooks (useDebounce, useMediaQuery)
│   ├── services/api/    # apiClient.ts — central Axios instance + interceptors
│   ├── utils/  types/  constants/
│   └── theme/           # tokens, light/dark themes, GlobalStyle, styled.d.ts
├── features/
│   └── products/
│       ├── components/  # ProductCard.tsx, ProductFilters.tsx
│       ├── hooks/       # useProducts.ts, useProduct.ts (TanStack Query)
│       ├── services/    # productService.ts (calls apiClient)
│       ├── pages/       # ProductListPage.tsx, ProductDetailsPage.tsx
│       ├── types/       # product.types.ts (or generated OpenAPI types re-exported)
│       ├── schemas/     # productFilterSchema.ts (Zod) — only if needed
│       └── index.ts     # public API: pages for the router, hooks/components others may use
└── main.tsx
```
Next.js (App Router): `app/` holds routes; keep route files thin and import pages/components from `src/features/...`; shared server utilities follow the same `shared/` rule.

## Placement rules
| Code | Location |
|---|---|
| Used by one feature | `features/<f>/...` |
| Generic UI primitive, no business meaning | `shared/components/ui` |
| Business concept used by several features (e.g. `UserAvatar` shown in orders and users) | The owning feature exports it via `index.ts`; others import that public API. Move to `shared` only if it has no feature logic. |
| Axios instance, interceptors, error normalization | `shared/services/api` |
| Feature endpoints (`getProducts`) | `features/<f>/services` |
| Query hooks wrapping endpoints | `features/<f>/hooks` |
| Zod schemas for a feature's forms | `features/<f>/schemas` |
| Routes and providers | `app/` |
| Global client state (auth session, UI prefs) | `features/auth/...` store or `app/` — not a single global mega-store |

## Best practices
- Enforce boundaries with lint rules (e.g. `eslint-plugin-boundaries`, `import/no-restricted-paths`, or `no-restricted-imports` patterns forbidding `features/*/!(index)` deep imports across features).
- Avoid barrel files that re-export everything in `shared/` (hurts tree shaking and causes cycles); keep feature `index.ts` small and intentional.
- Feature-to-feature needs: compose at the page/app level (pass data/components as props) or depend on the other feature's public API; never reach into internals.
- Keep API types generated from OpenAPI in one place (e.g. `shared/types/api.ts` generated file) and re-export the relevant ones per feature.
- Co-locate tests next to code (`ProductCard.test.tsx`) or in `__tests__` — follow project convention.
- Name files by what they are (`useProducts.ts`, `productService.ts`, `ProductCard.tsx`).

## Implementation workflow
1. Identify the business feature(s) the change belongs to.
2. Check for existing shared primitives and feature APIs to reuse.
3. Create only the folders the feature needs.
4. Implement services → hooks → components → pages; export the page (and anything deliberately public) from `index.ts`.
5. Register routes in `app/router` with lazy imports.
6. Verify no forbidden imports (lint) and no cycles (e.g. `madge --circular`).

## Decision-making guidelines
- **Feature vs. shared**: "Would this change if the feature's business rules changed?" Yes → feature. No, and used by 2+ features → shared.
- **New feature vs. sub-folder of existing feature**: separate business capability with its own pages/data → new feature; a facet of an existing capability → sub-folder.
- **Monorepo packages**: only when multiple apps share code or teams need independent release — otherwise folders suffice.
- **Migrating a layer-based project**: move one feature at a time when touching it; don't do a big-bang restructure without approval.

## Anti-patterns
- Global `components/`, `hooks/`, `services/`, `types/` holding everything.
- `shared/` or `common/` with feature business logic ("shared/utils/orderPricing.ts").
- Deep imports into another feature's internals.
- Circular feature dependencies.
- Empty scaffolding folders.
- One giant global store or one giant `api.ts` with every endpoint.
- Restructuring an existing project's folders as a side-effect of a feature task.

## Quality checklist
- [ ] Code lives in the owning feature; shared contains only generic, multi-feature code.
- [ ] Cross-feature imports go through `index.ts` (or none at all).
- [ ] Dependency direction `app → features → shared` holds; no cycles.
- [ ] Services/hooks/components separated within the feature.
- [ ] Routes registered in `app/router` with lazy loading.
- [ ] No empty folders; structure proportional to app size.
- [ ] Boundary lint rules pass.

## Examples
```ts
// features/products/index.ts — deliberate public API
export { default as ProductListPage } from './pages/ProductListPage';
export { default as ProductDetailsPage } from './pages/ProductDetailsPage';
export { useProduct } from './hooks/useProduct';
export type { Product } from './types/product.types';
```
```js
// eslint: forbid deep imports into other features
'no-restricted-imports': ['error', { patterns: [{
  group: ['@/features/*/*'],
  message: 'Import features through their public index.ts',
}]}]
```

## References
- React — Thinking in React: https://react.dev/learn/thinking-in-react
- Feature-Sliced Design (related methodology): https://feature-sliced.design/
- Bulletproof React — project structure (community reference): https://github.com/alan2207/bulletproof-react/blob/master/docs/project-structure.md
- Next.js project structure: https://nextjs.org/docs/app/getting-started/project-structure
- eslint-plugin-boundaries: https://github.com/javierbrea/eslint-plugin-boundaries
- ESLint no-restricted-imports: https://eslint.org/docs/latest/rules/no-restricted-imports
