---
name: backend-resilience-observability
description: Building resilient and observable backend services — timeouts, retries with backoff, circuit breakers, rate limiters, bulkheads and time limiters (Resilience4j, Spring Framework resilience annotations), graceful degradation and failure handling; plus Micrometer metrics, OpenTelemetry distributed tracing, structured logging with correlation IDs, Spring Boot Actuator health/readiness/liveness probes, SLO-based monitoring and alerting. Use when a service calls external dependencies, when adding metrics/tracing/logging/health checks, when diagnosing production failures, or when designing monitoring and alerts.
---

# Backend Resilience & Observability

## Purpose
Make services fail gracefully and make their behavior visible — with the **minimum** machinery needed. Application code concerns are owned by `backend`; collector/dashboard/alerting infrastructure by `devops` (see `devops-cicd`).

## When to use
- Calling another service, third-party API, message broker, or slow resource.
- Adding health checks, metrics, tracing, or logs to a service.
- Designing alerts, dashboards, or SLOs.
- Investigating latency spikes, cascading failures, or intermittent errors.

## Core principles
1. **Every remote call has a timeout.** No timeout = unbounded resource consumption.
2. **Retry only idempotent, transient failures**, with exponential backoff + jitter and a small cap. Never retry 4xx (except 408/429 with `Retry-After`).
3. **Fail fast when a dependency is down** (circuit breaker) and **degrade gracefully** (fallback, cached/stale data, feature off) rather than cascade.
4. **Isolate resources** (bulkheads) so one slow dependency can't exhaust all threads/connections.
5. **Observability = metrics + traces + logs, correlated by trace ID.**
6. **Alert on symptoms users feel** (error rate, latency, saturation against SLOs), not on every cause.
7. **Proportionality**: a single-dependency CRUD service needs timeouts and health checks, not a full resilience matrix.

## Best practices

### Resilience toolbox
| Mechanism | Purpose | Key settings | Pitfalls |
|---|---|---|---|
| **Timeout / TimeLimiter** | Bound wait time | Connect + read timeouts on HTTP/DB clients; per-call budget | Timeouts longer than the caller's own timeout are useless |
| **Retry** | Survive transient blips | 2–3 attempts, exponential backoff + jitter, retry on specific exceptions | Retry storms; retrying non-idempotent POSTs; retries × callers multiply load |
| **Circuit breaker** | Stop calling a failing dependency | Failure-rate threshold, sliding window, wait duration in open state, half-open permitted calls | Fallback that hides real outages; one breaker for many endpoints |
| **Rate limiter** | Protect yourself or respect a provider's quota | Limit per period, timeout for permission | Client-side limiter ≠ server-side protection (that's gateway/infra) |
| **Bulkhead** | Limit concurrent calls to a dependency | Max concurrent calls (semaphore) or thread pool | Too small = artificial errors; size from measured latency × throughput |
| **Fallback** | Graceful degradation | Cached value, default, partial response, queued for later | Never fallback on authorization/payment decisions silently |

Implementation options:
- **Resilience4j** (Spring Boot starter / Spring Cloud CircuitBreaker): annotations `@CircuitBreaker`, `@Retry`, `@RateLimiter`, `@Bulkhead`, `@TimeLimiter` with config in `application.yml`; metrics exported to Micrometer automatically.
- **Spring Framework 7+ core resilience** (`@Retryable`, `@ConcurrencyLimit`, enabled via `@EnableResilientMethods`) — sufficient for simple retry/concurrency limits without an extra library. Verify availability in the project's Spring version.
- Annotation order matters when stacking (Resilience4j default aspect order: Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( call ))))) — confirm in docs for the version used.
- Messaging: idempotent consumers, dead-letter queues, bounded redelivery, transactional outbox for publishing.

### Observability toolbox
**Health (Actuator)**
- Expose `health`, `info`, `prometheus` (or OTLP export) — not everything. Secure the rest or use a separate management port.
- Kubernetes/containers: `management.endpoint.health.probes.enabled=true` → `/actuator/health/liveness` and `/readiness`. Liveness must not depend on external systems (or the orchestrator will restart healthy pods when the DB blips); readiness may.

**Metrics (Micrometer)**
- RED for services (Rate, Errors, Duration) — `http.server.requests` is auto-instrumented; USE for resources (Utilization, Saturation, Errors) — JVM, pools.
- Custom business metrics with `MeterRegistry`/`@Timed`/`@Counted` or the Observation API; **low-cardinality tags only** (never user IDs, emails, raw URLs).
- Percentile histograms for latency SLOs (`management.metrics.distribution.percentiles-histogram.http.server.requests=true`).

**Tracing (OpenTelemetry)**
- Spring Boot uses Micrometer Tracing with an OpenTelemetry bridge, or the OpenTelemetry Java agent / Spring Boot starter — pick one approach per service and follow the project's existing choice.
- Propagate W3C `traceparent` across HTTP and messaging; sample sensibly (e.g. parent-based ratio) in production.
- Export via OTLP to a collector; backends (Tempo, Jaeger, vendor) are infrastructure decisions.

**Logging**
- Structured JSON logs in non-local environments (Spring Boot supports structured logging formats such as ECS/Logstash via `logging.structured.format.console`).
- Include `traceId`/`spanId` in every line (MDC — automatic with Micrometer Tracing).
- Log levels: ERROR = needs human action; WARN = degraded but handled; INFO = significant business/lifecycle events; DEBUG off in prod.
- Never log secrets, tokens, passwords, full card numbers, or unnecessary PII. Log an error once, at the boundary that handles it.

**Alerting**
- Define SLIs/SLOs (e.g. 99.5% of requests < 300 ms, error rate < 1%); alert on burn rate.
- Each alert links to a runbook and is actionable; delete noisy alerts.

## Implementation workflow
1. Inventory remote dependencies and their criticality (can the feature work without it?).
2. Set connect/read timeouts on every client (RestClient/WebClient/HTTP interface clients, JDBC pool, Mongo, Redis, Kafka).
3. Add retry only where the operation is idempotent and failures are transient; add circuit breaker for dependencies that can fail for extended periods; add bulkhead/rate limiter only with a concrete reason.
4. Define fallback behavior explicitly with product input (what does the user see?).
5. Enable Actuator health + probes; add custom `HealthIndicator` only for critical dependencies (and only in readiness).
6. Ensure metrics and tracing export; add key business metrics.
7. Configure structured logging with trace correlation.
8. Test failure modes: WireMock delays/faults, Testcontainers stopping a dependency (see `test-automation`); verify breaker opens, fallback works, timeouts trigger.
9. Hand dashboards/alerts infra to `devops` with the SLIs defined.

## Decision-making guidelines
- **Resilience4j vs. Spring core resilience**: need circuit breaker, rate limiter, or time limiter → Resilience4j. Only simple retries/concurrency limits → Spring core annotations (if available).
- **Retry vs. no retry**: non-idempotent operation without an idempotency key → no retry. User-facing request with tight latency budget → at most one fast retry.
- **Fallback vs. error**: fallback for non-critical enrichment (recommendations, avatars); explicit error for critical operations (payments, authorization).
- **Agent vs. library instrumentation**: follow the existing project approach; agent for zero-code broad coverage, library/starter for fine control and native-image compatibility.

## Anti-patterns
- Infinite or immediate retries; retries at every layer (client + service + gateway).
- Circuit breakers with fallbacks that silently return empty data for critical operations.
- Liveness probe checking the database.
- High-cardinality metric tags (user ID, order ID, full path with IDs).
- Logging full request/response bodies with PII; logging and rethrowing the same exception at every layer.
- Exposing all Actuator endpoints publicly.
- Alerts on CPU > 80% with no user impact; alerts without runbooks.

## Quality checklist
- [ ] Every outbound call has explicit timeouts.
- [ ] Retries limited to idempotent, transient failures with backoff + jitter.
- [ ] Circuit breaker/fallback behavior defined and tested for critical dependencies.
- [ ] Liveness independent of external dependencies; readiness reflects ability to serve.
- [ ] Metrics exported with low-cardinality tags; latency histograms enabled where SLOs exist.
- [ ] Trace context propagated over HTTP and messaging; trace ID in logs.
- [ ] Logs structured, levels correct, no sensitive data.
- [ ] Actuator exposure minimal and secured.
- [ ] Failure scenarios tested.

## Examples
```yaml
resilience4j:
  circuitbreaker:
    instances:
      inventory:
        sliding-window-size: 20
        failure-rate-threshold: 50
        wait-duration-in-open-state: 30s
        permitted-number-of-calls-in-half-open-state: 3
  retry:
    instances:
      inventory:
        max-attempts: 3
        wait-duration: 200ms
        enable-exponential-backoff: true
        enable-randomized-wait: true
        retry-exceptions: [java.io.IOException, java.util.concurrent.TimeoutException]
management:
  endpoints.web.exposure.include: health,info,prometheus
  endpoint.health.probes.enabled: true
  tracing.sampling.probability: 0.1
```
```java
@CircuitBreaker(name = "inventory", fallbackMethod = "availabilityUnknown")
@Retry(name = "inventory")
public Availability check(UUID productId) { return inventoryClient.availability(productId); }

private Availability availabilityUnknown(UUID productId, Throwable t) {
  log.warn("Inventory unavailable for product {}, returning UNKNOWN", productId, t);
  return Availability.UNKNOWN;   // UI shows "availability unknown", checkout re-validates
}
```

## References
- Resilience4j documentation: https://resilience4j.readme.io/docs
- Spring Framework resilience features: https://docs.spring.io/spring-framework/reference/core/resilience.html
- Spring Boot Actuator: https://docs.spring.io/spring-boot/reference/actuator/index.html
- Spring Boot observability: https://docs.spring.io/spring-boot/reference/actuator/observability.html
- Spring Boot structured logging: https://docs.spring.io/spring-boot/reference/features/logging.html
- Micrometer: https://docs.micrometer.io/micrometer/reference/
- Micrometer Tracing: https://docs.micrometer.io/tracing/reference/
- OpenTelemetry Java: https://opentelemetry.io/docs/languages/java/
- W3C Trace Context: https://www.w3.org/TR/trace-context/
- Google SRE book — Monitoring distributed systems: https://sre.google/sre-book/monitoring-distributed-systems/
- Google SRE workbook — Alerting on SLOs: https://sre.google/workbook/alerting-on-slos/
