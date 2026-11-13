---
name: design-patterns
description: Practical object-oriented and enterprise design patterns — Factory, Abstract Factory, Builder, Strategy, Adapter, Decorator, Observer, Repository, Specification, Facade, Proxy, Chain of Responsibility, Template Method, Dependency Injection, and Domain Events — with when to use each, trade-offs, alternatives, and how to avoid overengineering. Use when choosing how to structure classes or modules to handle variation, integration, or cross-cutting behavior, or when reviewing code for unnecessary abstraction.
---

# Design Patterns

## Purpose
Help agents apply patterns **only where they solve a present problem**, choose the lightest option, and recognize when a pattern is adding cost without benefit. System-level structure (modules, services, hexagonal) lives in `system-design`.

## When to use
- Code has a growing `if/else` or `switch` over types/modes.
- Integrating a third-party or legacy API whose shape differs from yours.
- Adding cross-cutting behavior (caching, logging, retries, authorization) without editing core logic.
- Constructing complex objects with many optional parameters.
- Decoupling side-effects (notifications, projections) from a core operation.
- Reviewing code that looks over-abstracted.

## Core principles
1. **Problem first, pattern second.** Name the force (variation, integration mismatch, cross-cutting concern, construction complexity) before naming a pattern.
2. **Rule of three.** Abstract after you see the third variation, not the first.
3. **Prefer language/framework features** (lambdas, records, sealed types, Spring DI, AOP, React composition) over hand-rolled pattern scaffolding.
4. **Composition over inheritance.**
5. **Every indirection must pay rent**: testability, replaceability, or readability — measurably.

## Pattern catalog
| Pattern | Use when | Advantages | Disadvantages | Lighter alternative |
|---|---|---|---|---|
| **Factory (method)** | Creation logic varies or needs a name/validation (`Money.of(...)`) | Encapsulates construction; named constructors | Extra type if trivial | Static factory method, constructor |
| **Abstract Factory** | Families of related objects must be created consistently (e.g. per-provider clients) | Guarantees compatible families | Many types; rarely needed with DI | DI configuration with profiles/qualifiers |
| **Builder** | Many optional params, immutable objects, readable test data | Readable, immutable results | Boilerplate (mitigate with Lombok `@Builder`/records) | Records with factory methods; named args (TS objects) |
| **Strategy** | Interchangeable algorithms selected at runtime (pricing rules, payment providers) | Open for extension; testable | More classes | `Map<Type, Function>`, sealed interface + switch pattern matching |
| **Adapter** | External interface ≠ the interface your code wants | Isolates third-party changes; enables anti-corruption layer | Mapping code | Direct call if used in one place and stable |
| **Decorator** | Add behavior around an object without modifying it (caching, metrics) | Stackable, SRP | Debugging layers; order matters | Spring AOP / annotations (`@Cacheable`), HOCs/hooks in React |
| **Observer** | Many listeners react to state changes | Loose coupling | Hidden control flow; memory leaks if not unsubscribed | Direct calls when listeners are few and fixed; framework events |
| **Repository** | Abstract persistence of aggregates behind a collection-like interface | Domain decoupled from storage; testable | Leaky if it exposes query-builder internals | Spring Data repository interfaces (already the pattern) |
| **Specification** | Composable business rules / dynamic query criteria | Reusable, combinable predicates | Can become an unreadable DSL | Explicit query methods; QueryDSL/Criteria when truly dynamic |
| **Facade** | Simplify use of a complex subsystem behind one entry point | Lowers coupling; clear module API | Can become a god object | Module public service (feature `index.ts`, module service class) |
| **Proxy** | Control access: lazy loading, remote calls, security, transactions | Transparent to callers | Surprises (self-invocation bypasses Spring proxies) | Framework-provided proxies (`@Transactional`, `@PreAuthorize`) |
| **Chain of Responsibility** | Ordered handlers that may process or pass on (filters, validation pipelines) | Configurable pipelines | Hard to trace which handler acted | Simple ordered list of validators; Spring Security filter chain |
| **Template Method** | Fixed algorithm skeleton with varying steps | Reuse of skeleton | Inheritance coupling | Strategy/higher-order function passed into one method |
| **Dependency Injection** | Always, for wiring services (constructor injection) | Testability, configuration | Overuse of interfaces with one impl | Concrete classes until a second impl or a test seam is needed |
| **Domain Events** | Side-effects of a domain change belong to other modules/aggregates | Decoupling, audit, extensibility | Eventual consistency, ordering, idempotency concerns | Direct method call within the same module/transaction |

## Best practices
- Constructor injection; no field injection; one implementation does **not** need an interface unless it is a port (hexagonal) or test seam.
- Use sealed interfaces + pattern matching (Java 21+) or TS discriminated unions instead of Visitor/Strategy hierarchies when the set of variants is closed.
- Spring: beware self-invocation — proxied behaviors (`@Transactional`, `@Cacheable`, `@Async`) don't apply to calls within the same bean.
- Domain events in Spring: publish via `ApplicationEventPublisher`; use `@TransactionalEventListener(phase = AFTER_COMMIT)` for side-effects that must only happen after commit; for cross-service delivery use the transactional outbox (Spring Modulith's event publication registry can provide this).
- Name classes by role in the domain (`ShippingCostCalculator`), not by pattern (`ShippingStrategyFactoryImpl`).

## Implementation workflow
1. Describe the problem in one sentence without pattern names.
2. Identify the variation axis or coupling to remove.
3. Try the simplest code (function, enum switch, direct call). Is it actually painful? If not, stop.
4. Pick the lightest pattern from the table; prefer framework support.
5. Implement with tests that exercise each variant.
6. Re-read: can a newcomer follow the flow? If not, simplify.

## Decision-making guidelines
- Closed set of variants → sealed type + switch. Open set (plugins, per-tenant) → Strategy registered via DI (`Map<String, PaymentProvider>`).
- Cross-cutting concern on many beans → AOP/annotation. On one bean → Decorator or inline.
- Same-transaction consequence → direct call. Different module, can be async → domain event. Different service → outbox + message broker.
- Dynamic search with many optional filters → Specification/Criteria. Fixed queries → derived/`@Query` methods.

## Anti-patterns
- `XxxService` + `XxxServiceImpl` for every class with no second implementation.
- Factories that just call `new`.
- Strategy hierarchies for two branches that will never grow.
- Event-driven spaghetti: events triggering events with no traceability.
- Generic repositories wrapping Spring Data repositories ("repository of repositories").
- Deep inheritance trees used for code reuse (Template Method abuse).
- Singletons with mutable global state.

## Quality checklist
- [ ] The problem the pattern solves is stated and present today.
- [ ] A simpler alternative was considered.
- [ ] Names express domain intent.
- [ ] Each variant/handler is tested.
- [ ] No proxy/self-invocation pitfalls; transactions and event phases correct.
- [ ] Control flow remains traceable (logs/traces for events and chains).

## Examples

**Strategy via DI (Spring)**
```java
public interface PaymentProvider { String id(); PaymentResult charge(Payment p); }

@Service
class PaymentService {
  private final Map<String, PaymentProvider> providers;
  PaymentService(List<PaymentProvider> list) {
    this.providers = list.stream().collect(toMap(PaymentProvider::id, identity()));
  }
  PaymentResult charge(Payment p) {
    var provider = Optional.ofNullable(providers.get(p.providerId()))
        .orElseThrow(() -> new UnsupportedProviderException(p.providerId()));
    return provider.charge(p);
  }
}
```

**Closed variants without a pattern (Java 21+)**
```java
sealed interface Discount permits Percentage, Fixed {}
record Percentage(BigDecimal pct) implements Discount {}
record Fixed(Money amount) implements Discount {}

Money apply(Discount d, Money price) {
  return switch (d) {
    case Percentage p -> price.minus(price.times(p.pct()));
    case Fixed f      -> price.minus(f.amount());
  };
}
```

**Domain event after commit**
```java
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
void on(OrderPlaced event) { notifications.sendConfirmation(event.orderId()); }
```

## References
- Refactoring.Guru design patterns catalog: https://refactoring.guru/design-patterns
- Martin Fowler — Catalog of Patterns of Enterprise Application Architecture: https://martinfowler.com/eaaCatalog/
- Spring Framework — Application events: https://docs.spring.io/spring-framework/reference/core/beans/context-introduction.html#context-functionality-events
- Spring Framework — Transaction-bound events: https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html
- Spring Modulith — Events: https://docs.spring.io/spring-modulith/reference/events.html
- Java pattern matching for switch (JEP 441): https://openjdk.org/jeps/441
