---
name: test-automation
description: Hands-on test automation patterns for Java/Spring and React/TypeScript — JUnit Jupiter, AssertJ, Mockito, Spring Boot test slices, Testcontainers with @ServiceConnection, WireMock, MockMvc/RestAssured API tests, Vitest, React Testing Library with user-event, MSW network mocking, Playwright browser E2E, reliable fixtures and test data builders, flaky-test prevention, and running suites in CI. Use when writing, fixing, or speeding up automated tests, setting up test infrastructure, or debugging flaky tests.
---

# Test Automation

## Purpose
Concrete, reliable patterns for implementing tests. Which tests to write and at what level is decided with `testing-strategy`.

## When to use
- Writing unit, slice, integration, API, component, or E2E tests.
- Setting up Testcontainers, WireMock, MSW, or Playwright in a project.
- Debugging flaky or slow tests.
- Wiring tests into CI.

## Core principles
1. **Reliable over clever.** Deterministic setup, explicit waits on conditions, no sleeps.
2. **Real where it matters** (DB, broker via Testcontainers), stubbed at external boundaries (WireMock/MSW).
3. **Readable tests are documentation.** Builders and helper assertions keep intent visible.
4. **Fast feedback.** Reuse Spring contexts and containers; parallelize safely.
5. **Use what the project already uses** (JUnit version, assertion library, test runner); detect versions first.

## Best practices

### Java / Spring patterns
**Unit tests (JUnit Jupiter + AssertJ + Mockito)**
- Plain constructor injection → instantiate the class with mocks; no Spring context.
- Mock only collaborators at boundaries (repositories in pure service logic tests, gateways); assert outcomes, use `verify` only for meaningful side-effects.
- `@ParameterizedTest` for boundary values.

**Slices**
- `@WebMvcTest(OrderController.class)` + `MockMvc` (or `MockMvcTester` in newer Spring versions) for request mapping, validation, error format, security rules (`@WithMockUser`, `jwt()` post-processor). Mock the service with `@MockitoBean` (Spring Framework 6.2+; `@MockBean` is deprecated/removed in newer versions — check the project version).
- `@DataJpaTest` / `@DataMongoTest` with Testcontainers for repository queries (disable embedded DB replacement for JPA: `@AutoConfigureTestDatabase(replace = NONE)` where needed).

**Integration / API (Testcontainers)**
- Spring Boot 3.1+: `@ServiceConnection` on container fields auto-configures connection properties.
- Reuse containers across test classes: static containers in a shared base/`@TestConfiguration`, or Testcontainers' singleton pattern; enable local reuse via `testcontainers.reuse.enable=true` only for local runs.
- Keep a stable set of context configurations to maximize Spring context caching (avoid many different `@MockitoBean` combinations).
- `@SpringBootTest(webEnvironment = RANDOM_PORT)` + RestAssured/`RestClient`/`WebTestClient` for full API tests, including auth.
- Data isolation: truncate tables between tests (helper), or unique data per test; avoid relying on `@Transactional` rollback for tests that cross threads/HTTP.
- Testcontainers requires a Docker-compatible runtime; if unavailable, report that tests didn't run — never claim success.

**WireMock**
- Stub third-party HTTP (`stubFor(get(...).willReturn(okJson(...)))`); simulate faults (`withFixedDelay`, `withFault(CONNECTION_RESET_BY_PEER)`) to test timeouts/circuit breakers; verify request bodies for outbound contracts.

**Async & time**
- Awaitility for eventual outcomes (`await().atMost(5, SECONDS).untilAsserted(...)`).
- Inject `Clock` instead of calling `now()` so time is controllable.

### React / TypeScript patterns
**Vitest**
- `environment: 'jsdom'` (or `happy-dom`) for components; setup file registering `@testing-library/jest-dom` matchers.
- Unit-test pure utils, Zod schemas, store logic, query-key factories.

**React Testing Library**
- Query by role/label/text (`getByRole('button', { name: /save/i })`); `findBy*` for async; `userEvent.setup()` for interactions.
- Render with the real providers via a `renderWithProviders` helper (QueryClient with `retry: false`, ThemeProvider, Router).
- Assert user-visible behavior: text, roles, disabled state, navigation — not component internals or class names.

**MSW (Mock Service Worker)**
- Define handlers per feature mirroring the API contract; override per test for error states (`server.use(http.get(..., () => HttpResponse.json(problem, { status: 409 })))`).
- `onUnhandledRequest: 'error'` to catch unmocked calls.

**Playwright**
- Locators by role/label/test id; web-first assertions (`await expect(locator).toBeVisible()`) — auto-waiting, no manual sleeps.
- Authenticate once via `storageState` setup project; isolate data per test (API-seeded via request fixture).
- Run against a production build; traces/screenshots on failure (`trace: 'on-first-retry'`).
- Keep E2E to critical journeys; run sharded in CI.

### Fixtures & test data
- Builders/factories (`anOrder().withStatus(PAID).build()`, `buildProduct({ price: 10 })`) with valid defaults.
- Unique identifiers per test (UUIDs/sequence) to allow parallel runs.
- No dependency on test execution order or on data left by other tests.

### Flaky test prevention
| Cause | Fix |
|---|---|
| Sleeps / timing assumptions | Awaitility, `findBy*`, Playwright auto-wait |
| Shared state between tests | Fresh data per test, reset stores/QueryClient, clean DB |
| Real time / time zones | Injected `Clock`, fixed TZ in CI (`TZ=UTC`), fake timers |
| Random ports/external network | Testcontainers, WireMock/MSW, no real internet |
| Order dependence | Run in random order locally; parallelize in CI |
| Animations in E2E | Disable animations / `prefers-reduced-motion` in tests |

### CI integration
- Separate fast (unit/component) and slower (integration/E2E) jobs; cache Maven/Gradle/npm dependencies; Docker available for Testcontainers.
- Publish JUnit XML / coverage (JaCoCo, Vitest coverage) and Playwright reports as artifacts.
- Fail the build on test failure; no automatic retries hiding flakiness (Playwright `retries` only in CI, and track flaky reports).

## Implementation workflow
1. Detect frameworks and versions; reuse existing test helpers and base classes.
2. Write the test plan (`testing-strategy`).
3. Create/extend fixtures and builders.
4. Implement tests per level using the patterns above.
5. Run locally: `./mvnw test` / `./mvnw verify`, `./gradlew test`, `npm run test -- --run`, `npx playwright test`.
6. Run each new test multiple times (or in random order) to check stability.
7. Report exact commands, pass/fail counts, and coverage.

## Decision-making guidelines
- **MockMvc vs. RestAssured on a real port**: MockMvc for controller/security slices and speed; real-port tests when filters, serialization, or the full stack matter.
- **MSW vs. mocking service modules**: MSW for component/integration-style frontend tests (exercises Axios client and interceptors); module mocks for isolated hook logic.
- **Testcontainers vs. Docker Compose for tests**: Testcontainers for test-owned lifecycle; Compose only if the project already uses it for an integration environment.

## Anti-patterns
- `Thread.sleep` / `waitForTimeout` in tests.
- H2/in-memory substitutes for query-heavy tests.
- Mocking the class under test or verifying every internal call.
- `getByTestId` everywhere when roles/labels are available.
- One mega E2E test covering everything.
- Tests that pass without assertions; swallowed exceptions in tests.

## Quality checklist
- [ ] Uses the project's test stack and versions.
- [ ] Real infra via Testcontainers where persistence/messaging matters; external HTTP stubbed.
- [ ] Accessible queries in UI tests; web-first assertions in Playwright.
- [ ] No sleeps; deterministic time and data.
- [ ] Tests pass repeatedly and in parallel.
- [ ] Commands and results recorded as evidence.

## Examples
```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Testcontainers
class OrderApiIT {
  @Container @ServiceConnection
  static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17-alpine");

  @LocalServerPort int port;

  @Test
  void returns404ForOtherUsersOrder() {
    UUID foreignOrder = fixtures.orderOwnedBy(otherUser);
    given().port(port).auth().oauth2(tokenFor(currentUser))
      .when().get("/api/v1/orders/{id}", foreignOrder)
      .then().statusCode(404).contentType("application/problem+json");
  }
}
```
```tsx
it('shows server validation error for duplicate email', async () => {
  server.use(http.post('/api/v1/users', () =>
    HttpResponse.json({ status: 409, title: 'Conflict', errors: [{ field: 'email', message: 'already registered' }] },
                      { status: 409 })));
  const user = userEvent.setup();
  renderWithProviders(<RegisterForm />);
  await user.type(screen.getByLabelText(/email/i), 'a@b.com');
  await user.type(screen.getByLabelText(/password/i), 'correct-horse');
  await user.click(screen.getByRole('button', { name: /create account/i }));
  expect(await screen.findByText(/already registered/i)).toBeInTheDocument();
});
```
```ts
test('user can place an order', async ({ page }) => {
  await page.goto('/products');
  await page.getByRole('link', { name: 'Coffee Mug' }).click();
  await page.getByRole('button', { name: 'Add to cart' }).click();
  await page.getByRole('link', { name: /cart/i }).click();
  await page.getByRole('button', { name: 'Checkout' }).click();
  await expect(page.getByRole('heading', { name: /order confirmed/i })).toBeVisible();
});
```

## References
- JUnit user guide: https://docs.junit.org/current/user-guide/
- AssertJ: https://assertj.github.io/doc/
- Mockito: https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html
- Spring Boot testing: https://docs.spring.io/spring-boot/reference/testing/index.html
- Spring Boot Testcontainers support: https://docs.spring.io/spring-boot/reference/testing/testcontainers.html
- Testcontainers for Java: https://java.testcontainers.org/
- WireMock: https://wiremock.org/docs/
- REST Assured: https://rest-assured.io/
- Awaitility: https://github.com/awaitility/awaitility/wiki/Usage
- Vitest: https://vitest.dev/guide/
- React Testing Library: https://testing-library.com/docs/react-testing-library/intro/
- user-event: https://testing-library.com/docs/user-event/intro
- MSW: https://mswjs.io/docs/
- Playwright: https://playwright.dev/docs/intro
- Playwright best practices: https://playwright.dev/docs/best-practices
