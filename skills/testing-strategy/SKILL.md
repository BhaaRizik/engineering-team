---
name: testing-strategy
description: Deciding what to test, at which level, and why — testing pyramid/trophy trade-offs, unit vs. integration vs. API vs. contract vs. end-to-end tests, regression and smoke tests, deriving test cases from requirements and risk, coverage goals that mean something, test data management, mocking vs. real dependencies, test isolation, and CI test stages. Use when planning tests for a feature or bug fix, reviewing test suites for gaps or bloat, setting coverage policy, or designing a CI testing pipeline.
---

# Testing Strategy

## Purpose
Help agents invest testing effort where it buys the most confidence per minute of runtime and maintenance. **How** to write each kind of test with specific tools is in `test-automation`.

## When to use
- Planning tests for a new feature, API, or bug fix.
- Reviewing a test suite (gaps, flakiness, slowness, over-mocking).
- Deciding on coverage targets or CI test stages.
- QA derivation of test cases from requirements.

## Core principles
1. **Tests exist to give confidence to change.** Optimize for catching real regressions with minimal brittleness.
2. **Test behavior through public interfaces**, not implementation details.
3. **Push tests to the lowest level that can catch the bug** — but not lower than where the bug actually lives (e.g. SQL bugs need a real DB).
4. **Risk-based**: more tests where failure is costly (money, security, data integrity, core flows).
5. **Deterministic and isolated**: each test sets up its own data and can run in any order, in parallel.
6. **Every bug fix starts with a failing regression test.**

## Test levels
| Level | Scope | Speed | Catches | Typical tools |
|---|---|---|---|---|
| **Unit** | A class/function/hook in isolation | ms | Logic, edge cases, calculations, validation | JUnit + AssertJ/Mockito; Vitest |
| **Component** (frontend) | A component with its hooks, mocked network | ms–s | Rendering states, interactions, a11y roles | React Testing Library + MSW |
| **Slice / integration** | Component + real infrastructure piece (DB, broker, HTTP layer) | s | Mapping, queries, transactions, serialization, security config | `@WebMvcTest`, `@DataJpaTest`, Testcontainers |
| **API** | Running app via HTTP | s | Contract, status codes, auth, validation, end-to-end backend flow | MockMvc/RestAssured + Testcontainers |
| **Contract** | Consumer expectations vs. provider | s | Breaking API changes between teams/services | Pact, OpenAPI schema validation |
| **E2E** | Real browser + deployed stack | s–min | Critical user journeys wiring together | Playwright |
| **Smoke** | Minimal post-deploy checks | s | Broken deployment/config | Health endpoint + 1–3 critical calls |

Shape: many unit/component tests, a solid layer of integration/API tests (often the best value for Spring services), few E2E tests for critical journeys only.

## Deriving test cases (QA method)
1. **From requirements**: each acceptance criterion → at least one positive test; each business rule → boundary tests.
2. **Equivalence partitions & boundary values**: min, max, just outside, empty, null, very large, unicode, duplicates.
3. **State transitions**: valid and invalid transitions (e.g. cancel a shipped order → rejected).
4. **Error paths**: dependency failures, timeouts, validation errors, conflicts (409), not found.
5. **Security cases**: unauthenticated (401), wrong role (403), other user's resource (404/403), malicious input.
6. **Implementation risks**: concurrency (double submit, optimistic lock), transactions, pagination edges, time zones/DST, rounding/money, migrations on existing data.
7. **Regression**: the exact reported bug scenario.
Prioritize by risk (impact × likelihood) and record what is intentionally not tested.

## Best practices
- Arrange–Act–Assert; one behavior per test; descriptive names (`shouldRejectOrderWhenOutOfStock`).
- Mock at **architectural boundaries you don't own** (third-party HTTP → WireMock/MSW); use real implementations for your own code and real databases via Testcontainers rather than H2/in-memory fakes.
- Test data: builders/factories with sensible defaults; unique data per test; no reliance on shared seed state; clean up via transactions or fresh containers/schemas.
- Coverage: track line + branch coverage as a **signal**; set a floor that prevents erosion (e.g. no decrease on changed code) rather than a vanity target. 100% coverage ≠ correct.
- Mutation testing (PIT, Stryker) occasionally on critical modules to check assertion strength.
- Flaky tests are bugs: quarantine and fix quickly; never "retry until green" as the solution.
- CI stages: lint/typecheck → unit → integration/API (parallel) → build artifact → deploy to staging → E2E smoke/critical → deploy prod → post-deploy smoke. Fail fast; keep PR feedback under ~10 minutes where possible.

## Implementation workflow
1. Read requirements and the design/contract; list risks.
2. Derive test cases (method above); assign each to the lowest effective level.
3. Identify test data and dependencies (real via Testcontainers vs. stubbed).
4. Write/extend tests (`test-automation` patterns); make the regression test fail first for bugs.
5. Run locally and in CI; check coverage on changed code.
6. Report: cases covered, levels, results, gaps and accepted risks.

## Decision-making guidelines
- **Unit vs. integration**: pure logic → unit. Anything whose correctness depends on framework config, SQL, serialization, or security filters → integration/slice.
- **Mock vs. real**: own DB/broker → real (Testcontainers). Third-party API → stub (WireMock/MSW) + a contract or sandbox check. Own internal collaborators → real objects unless slow/non-deterministic.
- **E2E or not**: only for critical revenue/security journeys (login, checkout) and cross-system wiring that lower levels can't cover.
- **Contract tests**: when frontend and backend (or services) deploy independently or are owned by different teams.
- **Snapshot tests**: rarely; only for stable serialized outputs, never as the main UI assertion.

## Anti-patterns
- Ice-cream cone: mostly E2E/manual, few unit tests.
- Mocking everything (tests pass while the real integration is broken); verifying internal method calls instead of outcomes.
- H2 instead of the real database engine for query-heavy code.
- Shared mutable fixtures; order-dependent tests; `Thread.sleep` waits.
- Coverage targets gamed with assertion-free tests.
- Testing private methods or implementation details (CSS classes, internal state).
- Ignoring flaky tests or permanently `@Disabled` tests without tickets.

## Quality checklist
- [ ] Test cases derived from requirements and risks, including negative and security cases.
- [ ] Each case at the lowest effective level.
- [ ] Real infrastructure for persistence/messaging integration tests.
- [ ] Tests isolated, deterministic, parallel-safe.
- [ ] Regression test reproduces the bug before the fix.
- [ ] Coverage on changed code reviewed; gaps documented.
- [ ] CI runs the suite with clear stages; results captured as evidence.

## Examples
**Test plan for "Cancel order" (excerpt)**
| # | Case | Level | Expected |
|---|---|---|---|
| 1 | Owner cancels PENDING order | API | 200, status CANCELLED, stock released |
| 2 | Cancel SHIPPED order | Unit (domain) + API | 409 problem-details |
| 3 | Other user cancels | API | 404 |
| 4 | Unauthenticated | API | 401 |
| 5 | Concurrent cancel + ship | Integration (Testcontainers) | One wins; other gets 409 (optimistic lock) |
| 6 | Cancel button disabled while request in flight | Component | No double request |
| 7 | Cancel from order page | E2E (critical journey only if high value) | UI shows cancelled state |

## References
- Martin Fowler — The Practical Test Pyramid: https://martinfowler.com/articles/practical-test-pyramid.html
- Kent C. Dodds — The Testing Trophy: https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications
- Testing Library guiding principles: https://testing-library.com/docs/guiding-principles
- Spring Boot testing: https://docs.spring.io/spring-boot/reference/testing/index.html
- Pact (consumer-driven contracts): https://docs.pact.io/
- PIT mutation testing: https://pitest.org/ · Stryker: https://stryker-mutator.io/
- Google Testing Blog — Flaky tests: https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html
