---
name: system-design
description: Software architecture and system design guidance — choosing between monolith, modular monolith, and microservices; Clean, Hexagonal, Layered, and Feature-First architecture; Domain-Driven Design (bounded contexts, aggregates); SOLID and dependency inversion; scalability and maintainability trade-offs; and writing Architecture Decision Records (ADRs). Use when designing a new system or feature that spans modules, restructuring an existing codebase, evaluating architectural options, or documenting an architectural decision.
---

# System Design

## Purpose
Help agents choose and evolve an architecture that fits the **actual** requirements, team, and constraints — and document why. This skill covers structural decisions (boundaries, dependencies, deployment units). Object-level patterns are in `design-patterns`; API contracts in `api-design`; data modeling in `database-design`; frontend structure in `frontend-architecture`.

## When to use
- Starting a new service/application, or a feature that touches several modules.
- Deciding whether to split something into a separate module or service.
- A codebase shows structural pain: circular dependencies, change amplification (one change touches many modules), unclear ownership.
- Evaluating a proposal like "let's move to microservices / hexagonal / event-driven".
- Recording a significant decision as an ADR.

## Core principles
1. **Requirements drive architecture.** Start from quality attributes (scalability, latency, availability, consistency, security, time-to-market, team size) and constraints — not from fashionable patterns.
2. **Optimize for change.** The dominant long-term cost is modifying code. Boundaries should follow what changes together (high cohesion) and isolate what changes independently (low coupling).
3. **Dependencies point inward, toward policy.** Domain/business rules must not depend on frameworks, databases, or transport. Infrastructure depends on the domain via interfaces (Dependency Inversion).
4. **Simplest architecture that meets the requirements.** Every boundary has a cost (indirection, mapping, network, operations). Add one only when it buys something specific.
5. **Make decisions reversible where cheap, deliberate where expensive.** Database choice, service split, and public API shape are expensive to reverse; internal package layout is cheap.
6. **SOLID as heuristics, not laws.** SRP = one reason to change; OCP = extend via new code at known variation points; LSP = substitutable implementations; ISP = small client-specific interfaces; DIP = depend on abstractions owned by the policy layer.

## Architecture styles — what they are and when they fit
| Style | Essence | Fits when | Costs |
|---|---|---|---|
| **Layered** (controller → service → repository) | Horizontal technical layers | Small/CRUD apps, small teams | Business logic leaks across layers; features scatter over many folders |
| **Feature-first / package-by-feature** | Top-level packages per business capability, layers inside | Most applications; default for both backend packages and frontends | Needs discipline to keep shared code genuinely shared |
| **Modular monolith** | One deployable, strongly enforced module boundaries with explicit APIs | Default for new non-trivial backends; teams up to ~several squads | Requires boundary enforcement (ArchUnit, Spring Modulith, Gradle/Maven modules) |
| **Hexagonal (Ports & Adapters)** | Domain core with ports; adapters for web, DB, messaging | Rich domain logic, multiple I/O channels, long-lived systems | More interfaces and mapping; overkill for CRUD |
| **Clean Architecture** | Concentric layers: entities → use cases → interface adapters → frameworks | Same as hexagonal; when use cases are explicit and numerous | Boilerplate; risk of ceremony without benefit |
| **Microservices** | Independently deployable services per bounded context, own data | Independent scaling/deployment needs, multiple autonomous teams, proven domain boundaries | Distributed systems complexity: network failures, eventual consistency, observability, ops overhead |
| **Event-driven** | Components communicate via events | Decoupled workflows, audit trails, integration across contexts | Harder debugging, ordering, idempotency, schema evolution |

Rule of thumb: **start with a well-modularized monolith**; extract a service only when a concrete driver exists (independent scaling, deployment cadence, team autonomy, fault isolation, regulatory isolation) and the boundary has proven stable.

## Domain-Driven Design essentials
- **Ubiquitous language**: code names match business terms.
- **Bounded context**: a boundary within which a model is consistent. Same word (e.g. "Customer") can mean different things in different contexts — don't force one shared model.
- **Aggregate**: a consistency boundary with one root; invariants enforced inside; transactions modify one aggregate; reference other aggregates by ID.
- **Domain events**: record facts that happened ("OrderPlaced") to decouple side-effects across aggregates/contexts.
- **Context mapping**: anti-corruption layer when integrating with a foreign model (legacy, third-party).
- Use tactical DDD (aggregates, value objects) where business rules are rich; use plain CRUD where they are not.

## Best practices
- Enforce module boundaries automatically (Spring Modulith `ApplicationModules.verify()`, ArchUnit rules, separate build modules, ESLint import rules on the frontend).
- Each module exposes a small public API; internals are package-private or unexported.
- No shared mutable database tables across modules/services; share via APIs or events.
- Keep framework annotations at the edges when using hexagonal/clean; pragmatic mixing is acceptable in feature-first Spring apps.
- Design for failure at every network boundary (see `backend-resilience-observability`).
- Define non-functional requirements numerically when possible (p95 latency, RPS, RPO/RTO).
- Capture significant decisions in ADRs stored with the code (`docs/adr/NNNN-title.md`).

## Implementation workflow
1. **Clarify drivers**: functional scope, quality attributes, constraints (team, budget, existing stack, compliance), expected scale.
2. **Inspect what exists**: current structure, dependency graph, pain points, conventions. Prefer evolving over rewriting.
3. **Identify boundaries**: business capabilities/bounded contexts; what data each owns; which interactions cross boundaries.
4. **Choose a style** using the table and decision guidelines; keep it as simple as the drivers allow.
5. **Define contracts** between modules (interfaces, events, APIs) and data ownership.
6. **Assess risks & trade-offs**: consistency, failure modes, migration path, operability, security implications.
7. **Record the decision** in an ADR.
8. **Plan incremental delivery**: strangler-fig for migrations; boundary enforcement tests first.

## Decision-making guidelines
- **Monolith vs. microservices**: choose microservices only if you can name the driver *and* you have the operational maturity (CI/CD per service, observability, on-call). Otherwise modular monolith.
- **Hexagonal/Clean vs. layered feature-first**: rich invariants, multiple adapters, long lifespan → hexagonal. CRUD-heavy, short-lived, or small → feature-first layered.
- **Sync vs. async integration**: need an immediate answer → sync (with timeouts/circuit breakers). Can tolerate delay, want decoupling, fan-out → events (with idempotent consumers, outbox pattern).
- **Shared library vs. duplication across services**: share stable technical utilities; duplicate small domain concepts rather than coupling services through a shared domain library.
- When two options are close, prefer the one that is **easier to reverse**.

## Anti-patterns
- **Distributed monolith**: services that must deploy together, share a database, or call each other synchronously in long chains.
- **Architecture astronautics**: hexagonal + CQRS + event sourcing for a CRUD admin panel.
- **Anemic domain + god services**: all logic in 2,000-line service classes.
- **Package-by-layer at scale**: `controllers/`, `services/`, `repositories/` with hundreds of files and no feature cohesion.
- **Shared "common" module** that slowly absorbs business logic and couples everything.
- **Undocumented decisions**: the "why" lost, leading to repeated debates or accidental reversal.
- **Big-bang rewrites** instead of incremental migration.

## Quality checklist
- [ ] Architectural drivers and constraints are stated explicitly.
- [ ] Chosen style is justified against at least one simpler alternative.
- [ ] Module/service boundaries align with business capabilities; data ownership is clear.
- [ ] Dependency direction is inward toward domain; no cycles.
- [ ] Cross-boundary contracts defined (APIs/events) and versioning considered.
- [ ] Failure modes and consistency model identified for every network/async boundary.
- [ ] Security implications identified (trust boundaries, sensitive data flows).
- [ ] Boundary enforcement mechanism in place or planned.
- [ ] ADR written for significant decisions.

## Examples

**Feature-first modular monolith (Spring)**
```text
com.example.shop
├── catalog/          # module: public API = CatalogService, ProductDto
│   ├── internal/     # entities, repositories, mappers (not used by other modules)
│   └── CatalogService.java
├── ordering/
│   ├── internal/
│   ├── OrderService.java
│   └── OrderPlaced.java   # domain event published for other modules
└── shared/           # technical utilities only (no business rules)
```

**ADR template**
```markdown
# ADR-0007: Use a modular monolith instead of microservices
- Status: Accepted (2026-01-15)
- Context: 4 developers, single product, unclear domain boundaries, need fast iteration.
- Decision: One deployable; modules per business capability; boundaries verified by Spring Modulith tests; inter-module communication via public services and application events.
- Alternatives: Microservices (rejected: ops overhead, unproven boundaries); layered monolith (rejected: poor cohesion as features grow).
- Consequences: + simple deployment, transactions, refactoring; − single scaling unit; revisit if a module needs independent scaling.
```

## References
- Martin Fowler — Software Architecture Guide: https://martinfowler.com/architecture/
- Microservices prerequisites & MonolithFirst: https://martinfowler.com/bliki/MonolithFirst.html
- Alistair Cockburn — Hexagonal Architecture: https://alistair.cockburn.us/hexagonal-architecture/
- Robert C. Martin — The Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- DDD Reference (Eric Evans): https://www.domainlanguage.com/ddd/reference/
- Spring Modulith reference: https://docs.spring.io/spring-modulith/reference/
- ArchUnit user guide: https://www.archunit.org/userguide/html/000_Index.html
- ADR resources: https://adr.github.io/
- microservices.io patterns: https://microservices.io/patterns/
