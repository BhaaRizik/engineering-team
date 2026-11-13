---
name: spring-boot-development
description: Production-grade Java and Spring Boot development — Java 25 LTS / Spring Boot 4.x where the project supports them (and correct practice on older versions), Spring MVC REST controllers, services, DTOs with records, MapStruct and Lombok, Spring Data JPA and Spring Data MongoDB repositories, Bean Validation, global exception handling with ProblemDetail, Spring Security configuration, springdoc-openapi, configuration properties and profiles, Maven/Gradle builds, and modular-monolith structure. Use when implementing, refactoring, or reviewing Java/Spring backend code or build configuration.
---

# Spring Boot Development

## Purpose
Give `backend` concrete, version-aware Spring practices. API contract rules come from `api-design`; data modeling from `database-design`; security policy from `application-security`; resilience/telemetry from `backend-resilience-observability`; testing from `testing-strategy` / `test-automation`.

## When to use
- Implementing controllers, services, repositories, entities, DTOs, mappers, configuration.
- Upgrading Java/Spring versions or reviewing build files.
- Structuring a Spring application (feature packages, modular monolith).

## Version policy
- **Always detect versions first**: `./mvnw help:evaluate -Dexpression=project.parent.version -q -DforceStdout` or read `pom.xml` / `build.gradle(.kts)` / `gradle/libs.versions.toml`, plus the Java toolchain.
- New projects: latest **Java LTS (25)** and latest **Spring Boot 4.x** GA, if all required libraries support them.
- Existing projects: use the project's versions. Don't upgrade as a side-effect; propose upgrades separately with a migration plan.
- Spring Boot 4 / Spring Framework 7 notable changes to account for (verify against the official release notes for the exact version): Jakarta EE 11 baseline, Jackson 3 as the default JSON library (new `tools.jackson` packages), JSpecify null-safety annotations, more modular starters/auto-configuration, first-class API versioning support in Spring MVC, HTTP service client improvements, and core resilience annotations (`@Retryable`, `@ConcurrencyLimit`). Don't use an API you haven't confirmed exists in the project's version.

## Core principles
1. **Thin controllers, focused services, explicit DTOs.** Controllers map HTTP ↔ application calls; services hold use-case logic; domain objects enforce invariants.
2. **Constructor injection only**; final fields; no `@Autowired` on fields.
3. **Package by feature**, not by layer (see `system-design`).
4. **Immutable data carriers**: Java records for DTOs, commands, events, and value objects.
5. **Configuration is typed and externalized**: `@ConfigurationProperties` records, profiles, environment variables; no secrets in source.
6. **Fail clearly**: domain exceptions mapped centrally to RFC 9457 `ProblemDetail`.

## Best practices
**Structure**
```text
com.example.app
├── order/
│   ├── OrderController.java        # web adapter
│   ├── OrderService.java           # use cases, @Transactional
│   ├── Order.java                  # entity/aggregate
│   ├── OrderRepository.java        # Spring Data
│   ├── dto/ CreateOrderRequest.java, OrderResponse.java
│   └── OrderMapper.java            # MapStruct
├── customer/ ...
└── shared/ (error handling, config, technical utilities only)
```
For modular monoliths, consider Spring Modulith to verify module boundaries and manage inter-module events.

**Controllers**
- `@RestController` + `@RequestMapping("/api/v1/...")`; `@Valid` on request bodies; return DTOs or `ResponseEntity` when status/headers matter (201 + `Location`).
- Pagination via `Pageable` with max page size configured (`spring.data.web.pageable.max-page-size`); map `Page<T>` to a stable DTO (Spring Data's `PagedModel`/`VIA_DTO` serialization rather than serializing `PageImpl` directly).

**Services & transactions**
- `@Transactional` on service methods (public), `readOnly = true` for queries.
- No remote HTTP calls inside DB transactions; no self-invocation of `@Transactional`/`@Cacheable` methods.
- Domain invariants in the entity/aggregate (`order.cancel()` throws if shipped), not scattered in services.

**Persistence — Spring Data JPA**
- Entities: no Lombok `@Data` (breaks `equals/hashCode` and lazy loading); use `@Getter` + explicit methods; `equals/hashCode` based on ID handled carefully or not overridden.
- Default `FetchType.LAZY` on associations; solve N+1 with `@EntityGraph`, fetch joins, or DTO projections.
- `@Version` for optimistic locking.
- `spring.jpa.open-in-view=false`.
- `spring.jpa.hibernate.ddl-auto=validate` (or `none`) with Flyway/Liquibase owning the schema.

**Persistence — Spring Data MongoDB**
- `@Document` aggregates, embedded value objects as records; indexes declared in migrations/`MongoTemplate` init or `@Indexed` with `auto-index-creation` disabled in production and managed explicitly.
- `@Version` for optimistic locking; `@Transactional` requires a replica set and a `MongoTransactionManager`.

**DTOs & mapping**
- Records for request/response DTOs with Bean Validation annotations.
- MapStruct (`@Mapper(componentModel = "spring")`) for non-trivial mapping; manual mapping for small cases. With Lombok on mapped classes, add `lombok-mapstruct-binding` and correct annotation-processor order.
- Lombok: acceptable for entities (`@Getter`, `@NoArgsConstructor(access = PROTECTED)`), avoid where records suffice.

**Validation & errors**
- Bean Validation (`@NotBlank`, `@Email`, `@Size`, custom constraints); validate path/query params with `@Validated` on the controller.
- A single `@RestControllerAdvice` (extend `ResponseEntityExceptionHandler`) producing `ProblemDetail`; enable `spring.mvc.problemdetails.enabled=true` if not extending.
- Map: validation → 400 with field errors; `EntityNotFound`-type → 404; optimistic lock → 409; access denied → 403. Log unexpected errors once with trace ID; return generic 500.

**Security (implementation side)**
- `SecurityFilterChain` bean (lambda DSL); `@EnableMethodSecurity` + `@PreAuthorize` for method-level rules.
- OAuth2 Resource Server for JWT validation when tokens come from an identity provider; don't hand-roll JWT parsing.
- `PasswordEncoder` via `PasswordEncoderFactories.createDelegatingPasswordEncoder()` (bcrypt default) or Argon2.
- Policy decisions (token lifetime, storage, roles model) come from `security` / `application-security`.

**Configuration**
- `application.yml` + profile files (`application-local.yml`, `application-prod.yml`); environment variables override; secrets from env/secret manager.
- `@ConfigurationProperties` records with `@Validated` for typed settings.
- Virtual threads (`spring.threads.virtual.enabled=true`, Java 21+) for blocking I/O-heavy apps — verify driver/pool sizing and pinning behavior.

**API documentation**
- springdoc-openapi version matching the Boot major version; annotate only where defaults are insufficient; document error responses and security schemes.

**Build**
- Use the wrapper (`./mvnw`, `./gradlew`). Manage versions via the Spring Boot BOM/plugin; don't pin transitive Spring versions manually.
- Enable compiler `-parameters` (Boot plugin does), fail on warnings only if the project does.

## Implementation workflow
1. Inspect build file, versions, package structure, existing error handling, security config, and test setup.
2. Confirm the API contract and data model (from the architect's brief).
3. Implement bottom-up: migration → entity/repository → service (+ unit tests) → DTO/mapper → controller (+ slice test) → OpenAPI annotations.
4. Wire configuration and properties.
5. Run `./mvnw -q verify` / `./gradlew build`; fix warnings introduced.
6. Report files changed and command results.

## Decision-making guidelines
- **JPA vs. JDBC Client/jOOQ**: JPA for aggregate-centric CRUD; `JdbcClient`/jOOQ for reporting, bulk, or complex SQL.
- **MapStruct vs. manual**: >5 fields or many mappers → MapStruct; trivial → manual constructor/record method.
- **Records vs. Lombok**: records for DTOs/value objects; Lombok only for JPA entities or when records can't be used.
- **Blocking MVC vs. WebFlux**: MVC (+ virtual threads) by default; WebFlux only for streaming/backpressure needs or an already-reactive stack.
- **Spring events vs. direct calls**: see `design-patterns`.

## Anti-patterns
- Exposing entities in controllers; bidirectional entity graphs serialized to JSON.
- `@Data` on entities; field injection; static utility "services".
- Catching `Exception` and returning 200; multiple competing exception handlers.
- `ddl-auto=update` in any shared environment.
- Business logic in controllers or mappers.
- Hardcoded URLs/credentials; secrets in `application.yml` committed to Git.
- Blindly upgrading dependencies in a feature task.

## Quality checklist
- [ ] Versions detected; no APIs used beyond the project's versions.
- [ ] Feature-package placement; module boundaries respected.
- [ ] DTOs separate from entities; validation in place.
- [ ] Transactions correct; no N+1 on main paths; `open-in-view=false`.
- [ ] Errors mapped to ProblemDetail consistently.
- [ ] Security config/annotations applied as designed.
- [ ] Configuration externalized; no secrets.
- [ ] OpenAPI reflects the endpoint.
- [ ] Build and tests pass (command output captured).

## Examples
```java
public record CreateOrderRequest(
    @NotEmpty List<@Valid Item> items,
    @NotNull UUID shippingAddressId) {
  public record Item(@NotNull UUID productId, @Positive int quantity) {}
}

@RestController
@RequestMapping("/api/v1/orders")
class OrderController {
  private final OrderService orders;
  OrderController(OrderService orders) { this.orders = orders; }

  @PostMapping
  ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest req,
                                       @AuthenticationPrincipal Jwt jwt,
                                       UriComponentsBuilder uri) {
    OrderResponse created = orders.create(UUID.fromString(jwt.getSubject()), req);
    return ResponseEntity.created(uri.path("/api/v1/orders/{id}").build(created.id())).body(created);
  }
}

@RestControllerAdvice
class ApiExceptionHandler extends ResponseEntityExceptionHandler {
  @ExceptionHandler(OrderNotFoundException.class)
  ProblemDetail notFound(OrderNotFoundException ex) {
    ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    pd.setTitle("Order not found");
    return pd;
  }
}

@ConfigurationProperties("app.orders")
@Validated
public record OrderProperties(@Positive int maxItems, @NotNull Duration reservationTtl) {}
```

## References
- Spring Boot reference: https://docs.spring.io/spring-boot/index.html
- Spring Boot release notes & migration guides: https://github.com/spring-projects/spring-boot/wiki
- Spring Framework reference: https://docs.spring.io/spring-framework/reference/
- Spring Security reference: https://docs.spring.io/spring-security/reference/
- Spring Data JPA: https://docs.spring.io/spring-data/jpa/reference/
- Spring Data MongoDB: https://docs.spring.io/spring-data/mongodb/reference/
- Spring Modulith: https://docs.spring.io/spring-modulith/reference/
- Jakarta Bean Validation: https://beanvalidation.org/
- MapStruct reference: https://mapstruct.org/documentation/stable/reference/html/
- Project Lombok features: https://projectlombok.org/features/
- springdoc-openapi: https://springdoc.org/
- OpenJDK JDK 25: https://openjdk.org/projects/jdk/25/
- Maven: https://maven.apache.org/guides/ · Gradle: https://docs.gradle.org/current/userguide/userguide.html
