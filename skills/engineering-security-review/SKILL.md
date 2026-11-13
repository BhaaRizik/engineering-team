---
name: engineering-security-review
description: Structured security review process — scoping, threat modeling (STRIDE, data-flow and trust boundaries), attack-surface analysis, security architecture review, code and API security review, authentication-flow and authorization testing, data-exposure analysis, vulnerability assessment, severity and business-impact risk rating, and actionable remediation reporting. Use when auditing a system, feature, PR, or design for security, assessing a security-sensitive change, or prioritizing vulnerabilities. (Separate from Claude Code's built-in /security-review command.)
---

# Engineering Security Review

## Purpose
Give `security` (and any agent asked to assess security) a repeatable process that finds real, exploitable weaknesses, rates them by severity and business impact, and produces fixable recommendations. Secure-coding defaults and threat specifics live in `application-security`.

## When to use
- Reviewing a design or ADR with security implications.
- Reviewing a PR touching auth, permissions, input handling, secrets, file handling, payment, or PII.
- Periodic audit of a service or repository.
- Triage of reported vulnerabilities or scanner output.

## Core principles
1. **Think like an attacker, report like an engineer.** Each finding is a concrete attack path with impact and a fix.
2. **Evidence over assumption.** Cite `file:line`, config, request/response; mark unverified items clearly.
3. **Risk = likelihood × impact**, adjusted for business context (data sensitivity, exposure, compliance).
4. **A passing checklist is not proof of security.** State scope, method, and limits; never declare a system "secure".
5. **Read-only and non-destructive.** No exploitation against shared/production systems; no exfiltration of real data; redact secrets in reports.
6. **Prioritize.** A short list of critical, fixable issues beats an unranked wall of findings.

## Implementation workflow (review process)
**1. Scope**
- What's in/out (components, endpoints, commits, environments). Assets (PII, credentials, money, admin actions). Actors (anonymous, user, admin, service, attacker). Compliance context if any.

**2. Model the system**
- Data-flow sketch: clients → edge → services → datastores → third parties. Mark trust boundaries (internet ↔ app, app ↔ DB, service ↔ service, app ↔ third party).
- List entry points (attack surface): HTTP endpoints, message consumers, file uploads, webhooks, scheduled jobs, admin consoles, CI/CD.

**3. Threat model (STRIDE per boundary/entry point)**
| Threat | Ask |
|---|---|
| **S**poofing | Can someone act as another user/service? (auth, token validation, webhook signatures) |
| **T**ampering | Can data/requests be modified? (mass assignment, unsigned data, integrity checks) |
| **R**epudiation | Can actions be denied? (audit logs for sensitive actions) |
| **I**nformation disclosure | Can data leak? (IDOR, verbose errors, logs, over-fetching DTOs, caching) |
| **D**enial of service | Can resources be exhausted? (rate limits, pagination, upload size, regex, timeouts) |
| **E**levation of privilege | Can a user gain more rights? (role checks, admin endpoints, path traversal, deserialization) |

**4. Targeted review**
- **Authentication flows**: login, logout, registration, reset, MFA, token issuance/refresh/revocation, session fixation, brute-force protections.
- **Authorization**: enumerate endpoints × roles × ownership; check each for object-level checks; look for missing checks on secondary paths (export, bulk, search, GraphQL/batch).
- **Input handling**: injection sinks (queries, shell, templates, file paths, URLs for SSRF, deserialization).
- **Data exposure**: response DTOs, logs, error messages, analytics, caches, frontend bundles, source maps.
- **Configuration**: security headers, CORS, CSRF vs. auth model, Actuator exposure, debug modes, default credentials, TLS.
- **Secrets**: repository history (`git log -p`/secret scanner), CI variables, Docker images, env files.
- **Dependencies**: known CVEs (`./mvnw dependency:tree`, `npm audit`, existing scanners); reachability of the vulnerable code.
- **Infrastructure touchpoints** (if in scope): IAM least privilege, public buckets, open ports, CI token permissions.

**5. Verify**
- Confirm findings by code tracing, running existing tests, or crafting safe requests against **local/test** environments only.
- Specify a failing test that demonstrates the authorization or validation gap (exact request, expected vs. actual) so `qa` or `backend` can add it — reviewers without write access describe it rather than write it.

**6. Rate and report** (below).

## Risk classification
| Severity | Typical criteria | Expected action |
|---|---|---|
| **Critical** | Remote, unauthenticated or trivially exploitable; full data breach, account takeover at scale, RCE, payment fraud | Fix immediately; block release |
| **High** | Authenticated exploitation leading to other users' data (IDOR), privilege escalation, stored XSS, secret exposure | Fix before release |
| **Medium** | Requires specific conditions; limited data exposure; missing rate limiting on sensitive actions; weak config | Fix in near term; may ship with accepted risk |
| **Low** | Defense-in-depth gaps, minor info leaks (versions), hardening | Backlog |
| **Info** | Observations, good practices noted | — |
Adjust by business impact (PII/regulatory data, financial loss, reputation). CVSS v4 may be used for external reporting; business severity governs prioritization.

## Best practices
- Review the diff **and** the surrounding code paths (callers, configs, filters).
- Check denial paths as carefully as allow paths.
- Prefer remediation that eliminates a class (parameterized queries everywhere, central authorization policy) over one-off patches.
- Re-test fixes; confirm no regression in adjacent endpoints.
- Record accepted risks explicitly with owner and rationale.

## Decision-making guidelines
- **Block vs. accept**: Critical/High block release unless the user explicitly accepts the risk with documented mitigation.
- **Finding vs. question**: if exploitability can't be determined from evidence, report as "Needs verification" with what would confirm it.
- **Scanner results**: triage for reachability and context; don't forward raw scanner output as findings.

## Anti-patterns
- Declaring "no vulnerabilities found, system is secure".
- Checklist-only reviews with no data-flow or authorization analysis.
- Unprioritized lists mixing headers nits with IDORs.
- Findings without reproduction or fix.
- Running intrusive scans or exploits against production or third-party systems.
- Printing discovered secrets in the report.

## Quality checklist
- [ ] Scope, assets, actors, and trust boundaries documented.
- [ ] Entry points enumerated; STRIDE applied to each boundary.
- [ ] AuthN flows and AuthZ (endpoint × role × ownership) reviewed.
- [ ] Input sinks, data exposure, configuration, secrets, dependencies reviewed.
- [ ] Findings verified or marked "needs verification".
- [ ] Each finding: severity, location, attack scenario, impact, remediation.
- [ ] Limitations and residual risk stated; no "secure" claim.

## Examples
**Finding format**
```markdown
### [High] IDOR on order details
- Location: OrderController.java:42 → OrderService.java:67 (`findById(id)` without owner check)
- Scenario: Authenticated user A requests GET /api/v1/orders/{B's order id} and receives B's address and items.
- Impact: Exposure of other customers' PII and order history (GDPR-relevant).
- Evidence: Service queries by id only; no @PreAuthorize; test `OrderAccessTest` reproduces (200 instead of 404).
- Remediation: Scope the query `findByIdAndCustomerId(id, currentUserId)`; add ADMIN path separately; add negative tests for every order endpoint.
```

**Report skeleton**
```markdown
Scope & method · Summary (top risks) · Findings by severity · Accepted risks · Limitations · Recommended next steps
```

## References
- OWASP Threat Modeling: https://owasp.org/www-community/Threat_Modeling
- OWASP Threat Modeling Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
- Microsoft STRIDE: https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/
- OWASP API Security Top 10: https://owasp.org/API-Security/
- FIRST CVSS v4.0: https://www.first.org/cvss/
