---
name: engineering-code-review
description: Structured engineering code-review method and checklist — correctness, architecture consistency, SOLID and maintainability, readability and naming, error handling, performance, security, testing quality, and technical debt — with severity-ranked findings that explain impact. Use when reviewing a diff, pull request, specialist agent output, or existing module for quality before merging or sign-off. (Separate from Claude Code's built-in /code-review command.)
---

# Engineering Code Review

## Purpose
Find **real problems** — bugs, design flaws, risks, and maintainability costs — and explain their impact so they get fixed. Not a style linter. Deep security review is in `engineering-security-review`; test design in `testing-strategy`.

## When to use
- Reviewing a PR/diff or a specialist agent's changes before reporting to the user.
- Phase 5/6 quality gates in the architect's workflow.
- Assessing an unfamiliar module before changing it.

## Core principles
1. **Correctness over style.** A missed bug costs more than a hundred naming nits.
2. **Every finding states impact.** "X causes Y under condition Z" — not "consider X".
3. **Evidence-based.** Cite `file:line`; reproduce or reason concretely; mark uncertainty.
4. **Review against intent.** Compare with the requirement, the agreed architecture, and the API contract.
5. **Respect project conventions.** Consistency with the codebase beats personal preference.
6. **Cosmetic feedback only when it affects consistency or maintainability**, and label it as such.

## Best practices

### Review checklist
**Correctness**
- Does it do what the requirement says, including edge cases (empty, null, max sizes, duplicates, concurrency, time zones)?
- Error paths: are exceptions caught at the right level, mapped to correct responses, not swallowed?
- Transactions: correct boundaries, no remote calls inside, no self-invocation bypassing proxies.
- Concurrency: shared mutable state, race conditions, idempotency of retries.
- Resource handling: streams/connections closed, timeouts set.

**Architecture & design**
- Follows the agreed architecture (module boundaries, feature-first placement, dependency direction).
- Business logic in the right layer (not in controllers/components).
- No new cross-module/feature coupling without reason; no logic dumped into `shared/`.
- Abstractions justified (see `design-patterns`); no duplicated logic.

**API & data**
- Matches the contract in `api-design` (status codes, errors, DTOs, pagination).
- Migrations safe and backward compatible (`database-design`); no N+1, unbounded queries.

**Security (quick pass; escalate to `security`)**
- Input validation, authorization per resource, no secrets/PII in code or logs, no injection, safe HTML rendering.

**Performance**
- Algorithmic complexity on realistic data; unnecessary queries/renders; missing pagination; blocking calls in hot paths. Only flag with a plausible impact.

**Readability & maintainability**
- Names reveal intent; functions do one thing; dead code removed; comments explain *why*.
- Consistency with existing code patterns.

**Tests**
- New behavior covered at the right level; tests assert behavior, not implementation; failure paths tested; tests deterministic.
- Tests actually ran and passed (evidence).

**Technical debt**
- Shortcuts are explicit (TODO with ticket/reason) and not hidden; note debt introduced vs. paid down.

### Severity levels
| Severity | Meaning | Action |
|---|---|---|
| **Blocker** | Bug, data loss/corruption, security hole, broken contract, failing build/tests | Must fix before merge |
| **Major** | Likely bug under realistic conditions, architecture violation, missing critical tests, significant performance risk | Fix before merge unless explicitly accepted |
| **Minor** | Maintainability/readability issue with real cost | Fix now or ticket |
| **Nit** | Optional, consistency-only | Author's choice |

## Implementation workflow
1. Read the requirement/brief and the agreed design/contract.
2. Get the full diff (`git diff <base>...HEAD`) and the list of files; read surrounding code, not just changed lines.
3. Build and run the tests (or verify the evidence provided).
4. Walk the checklist; trace at least one main flow and one error flow end-to-end.
5. Write findings: severity, `file:line`, problem, impact, concrete fix.
6. Summarize: verdict (approve / approve with changes / request changes), top risks, and what was not reviewed.

## Decision-making guidelines
- Unsure if it's a bug? Write a failing test or a concrete scenario; if you can't, label it a question, not a finding.
- Conflict between "better" design and existing convention → follow convention unless the convention causes a defect; raise the convention separately.
- Large refactor suggestions belong in a follow-up, not as blockers on a feature PR.

## Anti-patterns
- Dozens of nits that bury one real bug.
- "LGTM" without running anything.
- Vague comments ("this could be cleaner").
- Reviewing only the diff, missing broken callers.
- Demanding personal style preferences.
- Rewriting the author's code in review instead of explaining the issue.

## Quality checklist (for the review itself)
- [ ] Requirement and contract consulted.
- [ ] Build/tests executed or evidence verified.
- [ ] Every finding has severity, location, impact, fix.
- [ ] Main and error paths traced.
- [ ] Security-sensitive changes flagged for `security`.
- [ ] Clear verdict and list of anything not reviewed.

## Examples
**Good finding**
> **Major** — `OrderService.java:88`: `paymentClient.charge()` is called inside the `@Transactional` method. If the DB commit fails after a successful charge, the customer is charged with no order recorded. **Fix:** persist the order as `PENDING`, commit, then charge; or use an outbox to trigger payment after commit.

**Poor finding**
> "Maybe refactor this method." (no location, no impact, no fix)

**Review summary format**
```markdown
Verdict: Request changes
Blockers (1): ...
Major (2): ...
Minor (3): ...
Tests: `./mvnw verify` — 142 passed, 0 failed
Not reviewed: generated OpenAPI client code
```

## References
- Google Engineering Practices — Code Review: https://google.github.io/eng-practices/review/
- Conventional Comments: https://conventionalcomments.org/
- SonarSource rules (Java/TS quality rules): https://rules.sonarsource.com/
- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/
