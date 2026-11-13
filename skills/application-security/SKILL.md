---
name: application-security
description: Practical secure-coding guidance for backend (Java/Spring) and frontend (React) applications — OWASP Top 10 and OWASP API Security Top 10, authentication, session management, JWT and OAuth2/OIDC handling, RBAC/ABAC authorization and object-level access control, input validation, XSS, CSRF, SQL/NoSQL injection, SSRF, CORS, security headers and CSP, secrets management, rate limiting, secure file uploads, and dependency vulnerability management. Use when implementing or changing anything touching auth, permissions, user input, sensitive data, secrets, file handling, outbound requests, or security configuration.
---

# Application Security

## Purpose
Give every agent concrete, correct defaults for building secure software. This skill is about **building it right**; the review process for finding problems is `engineering-security-review`. Endpoint contract rules are in `api-design`.

## When to use
- Login, registration, password reset, sessions, tokens, OAuth2/OIDC.
- Roles/permissions, multi-tenant data access.
- Handling user input, file uploads, HTML rendering, URLs supplied by users.
- Secrets, configuration, CORS/CSP/headers.
- Adding or updating dependencies.

## Core principles
1. **Never trust input** — from users, other services, files, headers, or tokens until verified.
2. **Deny by default; least privilege** — for endpoints, roles, DB users, cloud IAM, CI tokens.
3. **Authorize every request at the object level** (who can access *this* record), not just by role.
4. **Use proven frameworks; don't roll your own crypto, JWT parsing, or auth protocols.**
5. **Defense in depth** — validation + parameterized queries + output encoding + CSP + least privilege.
6. **Secrets never in code, images, logs, or frontend bundles.**
7. **Fail securely** — errors don't leak internals; failures deny access.

## Best practices

### Threat-by-threat guidance
| Threat | Backend (Spring) | Frontend (React) |
|---|---|---|
| **Broken access control / BOLA (IDOR)** | Check ownership/tenant in service layer or `@PreAuthorize("@orderAccess.canRead(#id, authentication)")`; scope queries by owner (`findByIdAndOwnerId`); 404 for others' resources | Hide UI by permission only for UX; never rely on it |
| **Broken authentication** | Spring Security; OAuth2 Resource Server for JWT; MFA where valuable; lockout/rate limit login; generic login errors | No credentials in storage; redirect flows via library (Authorization Code + PKCE) |
| **Injection (SQL/NoSQL/LDAP/OS)** | Parameterized queries/JPA params; never concatenate into JPQL/SQL/Mongo queries; whitelist sort fields; avoid `Runtime.exec` with input | — |
| **XSS** | Return JSON with correct content type; encode in server-rendered templates | React escapes by default; avoid `dangerouslySetInnerHTML` (if required, sanitize with DOMPurify); validate URLs (block `javascript:`) before `href`; strict CSP |
| **CSRF** | Needed when auth uses cookies: keep Spring Security CSRF protection (cookie-to-header token for SPAs) + `SameSite` cookies. Not needed for pure bearer-token APIs | Send CSRF token header from cookie when using cookie sessions |
| **SSRF** | Validate/allow-list outbound hosts for user-supplied URLs; block private/link-local ranges and cloud metadata IPs; disable redirects or re-validate; resolve DNS and check IP | — |
| **Mass assignment** | Separate request DTOs with only writable fields; never bind directly to entities | — |
| **Security misconfiguration** | Minimal Actuator exposure; no default creds; disable stack traces in errors; prod profiles reviewed | No debug flags or source maps with secrets in prod |
| **Vulnerable dependencies** | Dependabot/Renovate + OWASP Dependency-Check or equivalent in CI; patch criticals promptly | `npm audit`/`pnpm audit`, Dependabot; review new packages (maintenance, popularity, install scripts) |
| **Sensitive data exposure** | TLS everywhere; encrypt sensitive data at rest where required; DTOs exclude sensitive fields; mask in logs | Don't log tokens/PII to console or analytics |
| **Unrestricted resource consumption** | Rate limiting (gateway or Bucket4j/Resilience4j), pagination caps, request size limits, timeouts | Debounce search; don't hammer APIs |

### Authentication & sessions
- **Passwords**: bcrypt (cost ≥ 10) or Argon2id via Spring Security `DelegatingPasswordEncoder`; enforce length (≥ 8, allow long passphrases), check against breached-password lists where feasible; never log or return passwords.
- **Password reset**: single-use, short-lived (≤ 30–60 min), high-entropy tokens stored hashed; same response whether the email exists or not.
- **Session cookies**: `HttpOnly`, `Secure`, `SameSite=Lax` (or `Strict`); rotate session ID on login; server-side invalidation on logout.
- **JWT**: validate signature with an expected algorithm (reject `none` and algorithm confusion), `iss`, `aud`, `exp`, `nbf`; short-lived access tokens (5–15 min); refresh tokens rotated, stored server-side/hashed or bound, revocable; prefer asymmetric keys (RS256/ES256) with JWKS from the IdP; keep claims minimal (no PII/secrets — JWTs are only encoded, not encrypted).
- **Token storage in browsers**: prefer HttpOnly cookies (BFF pattern) or in-memory access token + HttpOnly refresh cookie. Avoid `localStorage` for tokens (XSS-exfiltratable).
- **OAuth2/OIDC**: Authorization Code + PKCE for SPAs/mobile; no implicit flow; exact redirect URI matching; validate `state`/`nonce`.

### Authorization models
- **RBAC**: roles → permissions; check permissions (`order:read`) rather than role names in code where feasible.
- **ABAC / ownership**: attributes (owner, tenant, department, status) evaluated per request — required for object-level access.
- Centralize policy (Spring method security + dedicated authorization beans); test both allowed and denied cases.

### Headers, CORS, CSP
- CORS: explicit allowed origins (no `*` with credentials), methods, headers; configured in Spring Security's CORS config.
- Headers: `Strict-Transport-Security`, `Content-Security-Policy` (start strict: `default-src 'self'`; avoid `unsafe-inline`/`unsafe-eval`; nonces if needed — styled-components may require a nonce for injected styles), `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `frame-ancestors` via CSP.

### Secrets management
- Source from environment / secret manager (AWS Secrets Manager/SSM, Railway variables, GitHub Actions secrets/OIDC); never commit `.env` with real values; provide `.env.example`.
- Frontend env vars (`VITE_*`, `NEXT_PUBLIC_*`) are **public** — no secrets there.
- Rotate on exposure; add secret scanning (GitHub secret scanning, gitleaks) in CI.

### Secure file uploads
- Enforce size limits; validate content type by magic bytes, not extension; generate server-side file names; store outside web root (e.g. private S3 bucket); serve via pre-signed URLs with short expiry; scan for malware where risk warrants; never execute or unzip without limits (zip bombs, path traversal).

## Implementation workflow
1. Identify assets (data, actions) and actors; note trust boundaries.
2. Choose the auth mechanism and token/session storage with `security`.
3. Define authorization rules per endpoint and per object.
4. Implement with framework features; validate input via DTO constraints.
5. Configure headers, CORS, CSRF according to the auth model.
6. Externalize secrets; add dependency and secret scanning.
7. Write negative tests (unauthenticated, wrong role, other user's resource, malicious input).
8. Request review from `security` for sensitive changes.

## Decision-making guidelines
- **Session cookie vs. JWT bearer**: same-site web app with a backend → server session or BFF with HttpOnly cookie. Multiple APIs/clients, third-party IdP → OAuth2 access tokens validated by a resource server.
- **Build vs. buy identity**: prefer an IdP (Keycloak, Auth0, Cognito, Entra) over custom auth for anything beyond simple apps.
- **RBAC vs. ABAC**: RBAC for coarse capabilities; add ABAC/ownership checks wherever data belongs to users or tenants (almost always).
- **Rate limit location**: edge/gateway for global protection; application-level for per-user/business limits (login attempts, OTP sends).

## Anti-patterns
- Authorization only in the frontend or only by role.
- `permitAll()` on everything during development that ships to prod.
- Disabling CSRF while using cookie authentication.
- Custom JWT parsing; accepting tokens without audience/issuer checks; long-lived access tokens.
- Tokens or secrets in `localStorage`, URLs, logs, or frontend env vars.
- String-concatenated queries; regex-based HTML sanitization.
- `Access-Control-Allow-Origin: *` with credentials.
- Detailed error messages revealing whether a user exists.

## Quality checklist
- [ ] Every endpoint has explicit authentication and object-level authorization.
- [ ] Inputs validated; queries parameterized; sort/filter fields whitelisted.
- [ ] Passwords hashed with bcrypt/Argon2; reset flow secure.
- [ ] Tokens/sessions configured per guidance (lifetimes, storage, validation).
- [ ] CORS, CSRF, security headers, CSP set correctly for the auth model.
- [ ] No secrets in code, images, logs, or frontend bundles; scanning enabled.
- [ ] Uploads constrained and stored safely.
- [ ] Dependencies scanned; no known critical vulnerabilities unaddressed.
- [ ] Negative security tests exist.

## Examples
```java
@Bean
SecurityFilterChain api(HttpSecurity http) throws Exception {
  return http
    .authorizeHttpRequests(a -> a
        .requestMatchers("/actuator/health/**").permitAll()
        .requestMatchers(HttpMethod.GET, "/api/v1/products/**").permitAll()
        .anyRequest().authenticated())
    .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
    .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
    .csrf(c -> c.disable()) // OK only because auth is bearer-token, not cookies
    .build();
}

// Object-level authorization: scope the query to the caller
Order order = orders.findByIdAndCustomerId(orderId, currentUserId)
    .orElseThrow(() -> new OrderNotFoundException(orderId));
```

## References
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP API Security Top 10: https://owasp.org/API-Security/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
- Spring Security reference: https://docs.spring.io/spring-security/reference/
- RFC 8725 JWT Best Current Practices: https://www.rfc-editor.org/rfc/rfc8725
- RFC 9700 OAuth 2.0 Security Best Current Practice: https://www.rfc-editor.org/rfc/rfc9700
- OAuth 2.0 for Browser-Based Apps (IETF draft): https://datatracker.ietf.org/doc/draft-ietf-oauth-browser-based-apps/
- MDN Content Security Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
- MDN CORS: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- DOMPurify: https://github.com/cure53/DOMPurify
- GitHub Dependabot: https://docs.github.com/en/code-security/dependabot
