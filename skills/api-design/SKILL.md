---
name: api-design
description: REST API design standards shared by backend and frontend — resource modeling, HTTP methods and status codes, request/response DTOs, pagination/filtering/sorting, versioning, RFC 9457 problem-details error format, validation, idempotency, authentication on endpoints, OpenAPI 3.x / Swagger documentation, backward compatibility, and contract testing. Use when designing or changing an HTTP API, defining a contract between frontend and backend, reviewing an endpoint, writing an OpenAPI spec, or consuming an API from the frontend.
---

# API Design

## Purpose
Define one consistent API contract standard so `backend` implements, `frontend` consumes, `qa` tests, and `security` reviews against the **same** rules. Spring-specific implementation is in `spring-boot-development`; deep security guidance in `application-security`.

## When to use
- Designing a new endpoint or resource.
- Changing an existing response/request (compatibility check needed).
- Writing or reviewing an OpenAPI document.
- Building a frontend API layer against a backend contract.
- Defining error handling, pagination, or idempotency behavior.

## Core principles
1. **Contract first.** Agree on the contract (OpenAPI or a written spec) before parallel frontend/backend work.
2. **Resources, not RPC.** Model nouns (`/orders/{id}`), use HTTP semantics for verbs. Use action sub-resources only for true state transitions (`POST /orders/{id}/cancel`).
3. **Consistency beats cleverness.** Same naming, pagination, errors, and date formats everywhere.
4. **DTOs are the contract; entities are not.** Never expose persistence models.
5. **Backward compatibility by default.** Additive changes only, unless a new version is introduced.
6. **The server is the authority.** Validate and authorize every request server-side.

## Standards (defaults — follow the project's existing conventions if they differ)
**URLs & naming**
- Plural nouns, kebab-case paths: `/api/v1/purchase-orders/{orderId}/items`.
- JSON fields camelCase. IDs as strings in JSON if they could exceed JS safe integers (or are UUIDs).
- Timestamps ISO-8601 UTC (`2026-03-01T12:00:00Z`); money as `{ "amount": "12.50", "currency": "EUR" }` (decimal string or minor units integer — pick one, document it).

**Methods & status codes**
| Operation | Method | Success | Notes |
|---|---|---|---|
| List | GET `/items` | 200 | Paginated |
| Read | GET `/items/{id}` | 200 / 404 | |
| Create | POST `/items` | 201 + `Location` header + body | 409 on uniqueness conflict |
| Full replace | PUT `/items/{id}` | 200 / 204 | Idempotent |
| Partial update | PATCH `/items/{id}` | 200 | JSON Merge Patch (`application/merge-patch+json`) semantics |
| Delete | DELETE `/items/{id}` | 204 | Idempotent; 404 or 204 for missing — be consistent |
| Async job | POST | 202 + status URL | |

Errors: 400 malformed/validation, 401 unauthenticated, 403 authenticated but forbidden, 404 not found (also for resources the caller may not know exist), 409 conflict/optimistic lock, 412 precondition failed (ETag), 415, 422 (if the project distinguishes semantic validation from 400 — choose one and be consistent), 429 rate limited (+ `Retry-After`), 500 unexpected, 503 unavailable.

**Error format — RFC 9457 Problem Details** (`application/problem+json`)
```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation failed",
  "status": 400,
  "detail": "Request contains invalid fields",
  "instance": "/api/v1/orders",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "errors": [{ "field": "email", "message": "must be a valid email" }]
}
```
Never leak stack traces, SQL, or internal class names.

**Pagination, filtering, sorting**
- Offset: `?page=0&size=20&sort=createdAt,desc` → response `{ "content": [...], "page": { "number":0, "size":20, "totalElements":135, "totalPages":7 } }`.
- Cursor (large/real-time datasets): `?limit=20&cursor=eyJ...` → `{ "content": [...], "nextCursor": "..." }`.
- Cap `size`/`limit` server-side (e.g. max 100). Whitelist sortable/filterable fields.
- Filters as explicit query params (`?status=OPEN&createdAfter=...`).

**Versioning**
- Default: URI major version (`/api/v1`). Header/media-type versioning is acceptable if the project already uses it.
- Non-breaking (no new version): adding optional request fields, adding response fields, adding endpoints, adding enum values *only if clients tolerate unknown values*.
- Breaking (new version or coordinated migration): removing/renaming fields, changing types/semantics, making optional fields required, changing status codes or error format.
- Deprecate with `Deprecation`/`Sunset` headers and documentation before removal.

**Idempotency**
- GET/PUT/DELETE are idempotent by definition; implement them that way.
- For POST that creates side-effects (payments, orders): accept `Idempotency-Key` header; store key + request hash + response; replay the stored response for duplicates; 409/422 if same key with different payload.

**Concurrency**
- Optimistic locking via `ETag`/`If-Match` (→ 412) or a `version` field (→ 409).

**Security on endpoints** (details in `application-security`)
- Every endpoint declares its auth requirement in OpenAPI (`security`), including public ones explicitly.
- Authorize per resource (ownership/tenant), not only per role — prevent BOLA/IDOR.
- Don't put secrets or PII in URLs (they end up in logs).

## Best practices
- Separate request and response DTOs (`CreateOrderRequest`, `OrderResponse`); never reuse one DTO for both.
- Validate requests declaratively (Bean Validation / Zod) and return all field errors at once.
- Document every endpoint in OpenAPI 3.x: summary, parameters, schemas, examples, all response codes including errors.
- Generate frontend types/clients from OpenAPI (e.g. `openapi-typescript`) instead of hand-writing them.
- Use `Location` for created resources; return the created representation.
- Keep payloads lean; avoid deeply nested graphs — link or embed deliberately.
- Correlation: return a `traceId` (or `X-Request-Id`) and log it.

## Implementation workflow
1. Identify resources, relationships, and operations from the use cases.
2. Draft the contract (OpenAPI or a table): paths, methods, DTO schemas, status codes, errors, auth.
3. Review with consumers (`frontend`) and `security` for sensitive endpoints.
4. Check compatibility against the existing contract if modifying.
5. Implement (backend) and generate/consume types (frontend) in parallel against the agreed contract.
6. Add contract/API tests (`testing-strategy`, `test-automation`).
7. Publish updated docs; record breaking changes and migration notes.

## Decision-making guidelines
- **Offset vs. cursor pagination**: offset for admin UIs needing page numbers and small/medium data; cursor for feeds, infinite scroll, large or frequently-changing tables.
- **PUT vs. PATCH**: PATCH for partial updates from forms; PUT when the client owns the full representation.
- **400 vs. 422**: pick one convention for validation errors project-wide; document it.
- **Action endpoint vs. field update**: a state transition with rules/side-effects (`/cancel`, `/approve`) gets its own endpoint; plain attribute edits use PATCH.
- **REST vs. alternatives**: REST/JSON by default; consider GraphQL for highly variable client-driven reads across many entities, gRPC for internal high-throughput service-to-service calls — only with a clear driver.

## Anti-patterns
- Verbs in paths (`/getOrders`, `/createUser`).
- 200 OK with `{ "success": false }`.
- Exposing JPA entities / database IDs that leak internal structure without intent.
- Unbounded list endpoints.
- Different error shapes per controller.
- Silent breaking changes in "v1".
- Authorization by hiding endpoints in the frontend.
- Frontend duplicating backend business rules instead of reading results/flags from the API.

## Quality checklist
- [ ] Resource naming, methods, and status codes follow the standard.
- [ ] Request/response DTOs separate; validation constraints defined.
- [ ] Errors use the problem-details format; no internal leakage.
- [ ] Lists paginated with max size; sorting/filtering whitelisted.
- [ ] Auth and per-resource authorization defined for every endpoint.
- [ ] Idempotency/concurrency handled for unsafe operations where needed.
- [ ] OpenAPI updated with examples and all response codes.
- [ ] Compatibility assessed; breaking changes versioned and communicated.
- [ ] Contract/API tests exist.

## Examples
**Contract table (for briefs between agents)**
| Endpoint | Auth | Request | Response | Errors |
|---|---|---|---|---|
| `POST /api/v1/orders` | USER | `CreateOrderRequest { items[{productId, quantity}], shippingAddressId }`, header `Idempotency-Key` | 201 `OrderResponse`, `Location` | 400 validation, 404 product, 409 out of stock |
| `GET /api/v1/orders?status=&page=&size=&sort=` | USER (own orders), ADMIN (all) | — | 200 `Page<OrderSummary>` | 400 invalid sort |

**OpenAPI fragment**
```yaml
paths:
  /api/v1/orders/{orderId}:
    get:
      operationId: getOrder
      security: [{ bearerAuth: [] }]
      parameters:
        - { name: orderId, in: path, required: true, schema: { type: string, format: uuid } }
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: "#/components/schemas/OrderResponse" } } } }
        "404": { description: Not found, content: { application/problem+json: { schema: { $ref: "#/components/schemas/Problem" } } } }
```

## References
- RFC 9110 HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110
- RFC 9457 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457
- RFC 7396 JSON Merge Patch: https://www.rfc-editor.org/rfc/rfc7396
- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- Swagger / OpenAPI docs: https://swagger.io/docs/
- springdoc-openapi: https://springdoc.org/
- openapi-typescript: https://openapi-ts.dev/
- IETF Idempotency-Key header draft: https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/
- Microsoft REST API Guidelines: https://github.com/microsoft/api-guidelines
- Pact contract testing: https://docs.pact.io/
- OWASP API Security Top 10: https://owasp.org/API-Security/
