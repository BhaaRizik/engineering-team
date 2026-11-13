---
name: database-design
description: Database and data modeling guidance for PostgreSQL/relational and MongoDB/document databases — modeling from access patterns, normalization vs. denormalization, relationships vs. embedding, indexing, query optimization with EXPLAIN, transactions and isolation, concurrency and locking, migrations (Flyway/Liquibase), schema evolution with zero downtime, data integrity constraints, and caching. Use when designing tables/collections, writing migrations, diagnosing slow queries, choosing between SQL and document storage, or reviewing persistence code.
---

# Database Design

## Purpose
Help agents design data models that are correct, performant for real access patterns, and safe to evolve in production. ORM/Spring Data specifics are in `spring-boot-development`; caching infrastructure in `backend-resilience-observability`.

## When to use
- New entity/aggregate, table, or collection.
- Writing or reviewing a migration.
- Slow queries, N+1 problems, lock contention, deadlocks.
- Choosing relational vs. document storage, or embedding vs. referencing.
- Adding caching for read-heavy data.

## Core principles
1. **Integrity first, enforced by the database.** NOT NULL, foreign keys, unique and check constraints are your last line of defense against application bugs.
2. **Model from access patterns.** List the queries (filters, sorts, joins, volumes, frequency) before finalizing structure and indexes.
3. **Normalize by default (relational), denormalize deliberately** with a stated read-performance reason and a plan for keeping copies consistent.
4. **Migrations are code.** Versioned, reviewed, repeatable, forward-only in production.
5. **Schema changes must be backward compatible** with the currently running application version (expand → migrate → contract).
6. **Measure before optimizing.** Use `EXPLAIN (ANALYZE, BUFFERS)` / MongoDB `explain("executionStats")`.

## Best practices

### Relational (PostgreSQL)
- Primary keys: `bigint generated always as identity` or UUID (prefer time-ordered UUIDv7 if available to reduce index fragmentation). Expose UUIDs externally if IDs should not be guessable.
- Types: `timestamptz` for instants, `numeric(p,s)` for money (never float), `text` with check constraints over arbitrary `varchar(n)`, `jsonb` only for genuinely schemaless attributes.
- Constraints: FK on every reference (index the FK column — PostgreSQL does not do it automatically), UNIQUE for natural keys, CHECK for enumerations/ranges.
- Indexes: support WHERE + ORDER BY of frequent queries; composite index column order = equality columns first, then range/sort; partial indexes for hot subsets (`WHERE status = 'OPEN'`); covering indexes (`INCLUDE`) when justified. Every index costs writes and storage — remove unused ones (`pg_stat_user_indexes`).
- Transactions: default READ COMMITTED; use optimistic locking (`version` column) for user edits; `SELECT ... FOR UPDATE` (with `SKIP LOCKED` for queues) for pessimistic needs; keep transactions short; never hold a transaction open across remote calls.
- Soft delete only when there is a business requirement (audit/restore); otherwise hard delete + audit table. Soft delete complicates unique constraints (use partial unique indexes).
- Auditing: `created_at`, `updated_at`, and `created_by` where useful.
- Large tables: plan partitioning (by time/tenant) only with evidence of need.

### Document (MongoDB)
- **Embed** when data is read together, owned by the parent, bounded in size, and not updated independently (order → line items).
- **Reference** when data is shared, unbounded (comments, events), large, or updated independently.
- Avoid unbounded arrays; the 16 MB document limit and growing write cost are real constraints.
- Use schema validation (`$jsonSchema`) to enforce required fields and types.
- Indexes follow the ESR rule: **E**quality, **S**ort, **R**ange field order in compound indexes.
- Multi-document transactions exist (replica sets) but design so most operations touch one document.
- Denormalized copies need an update strategy (application event, change streams) and tolerance for staleness.

### Migrations & schema evolution
- Tool: Flyway or Liquibase — use what the project uses. One change per migration, descriptive name (`V12__add_order_status_index.sql`).
- Never edit an applied migration; add a new one.
- Zero-downtime pattern (**expand/contract**):
  1. Expand: add new nullable column/table; deploy code that writes both old and new.
  2. Backfill in batches (avoid long locks).
  3. Switch reads to new structure.
  4. Contract: drop old column in a later release.
- PostgreSQL specifics: `CREATE INDEX CONCURRENTLY` on large tables (not inside a transaction — configure the migration accordingly); adding a column with a constant default is fast in modern PostgreSQL, but adding NOT NULL to an existing column requires a full scan — add a `CHECK (...) NOT VALID` then `VALIDATE` instead; renames are breaking for running code.
- **Destructive operations (DROP, TRUNCATE, mass DELETE/UPDATE) require explicit user approval** and a backup/rollback plan.

### Query optimization workflow
1. Reproduce with realistic data volume.
2. Capture the actual SQL (enable ORM SQL logging / `pg_stat_statements`).
3. `EXPLAIN (ANALYZE, BUFFERS)`: look for Seq Scans on large tables, row-estimate mismatches, nested loops over large sets, sorts spilling to disk.
4. Fix in order: query shape (N+1 → join/batch fetch, select only needed columns), then indexes, then schema/denormalization, then caching.
5. Re-measure and record the before/after.

### Caching
- Cache only data with a clear read/write ratio benefit and tolerable staleness. Define TTL and invalidation upfront.
- Cache-aside is the default; avoid caching per-user authorization-sensitive data without keys that include the principal.
- Never use the cache as the source of truth.

## Implementation workflow
1. List entities, relationships, invariants, and lifecycle.
2. List access patterns with expected volumes.
3. Choose store and model (relational tables / document shape).
4. Define constraints and indexes for the access patterns.
5. Write migration(s) following expand/contract if the table is live.
6. Validate with tests against the real database engine (Testcontainers — see `test-automation`).
7. Review query plans for critical queries.

## Decision-making guidelines
- **PostgreSQL vs. MongoDB**: strong relationships, reporting, multi-entity transactions, ad-hoc queries → PostgreSQL. Self-contained aggregates with variable structure, read-together documents, horizontal scale needs → MongoDB. When unsure, PostgreSQL (with `jsonb` for flexible parts).
- **Normalize vs. denormalize**: denormalize only for a measured read hotspot, with an explicit sync mechanism.
- **Optimistic vs. pessimistic locking**: low contention, user-facing edits → optimistic. High contention on a single row, short critical sections → pessimistic.
- **Database constraint vs. application validation**: both — application for UX messages, database for guarantees.

## Anti-patterns
- Floats for money; `timestamp` without time zone for instants.
- No FKs "for performance".
- Index on every column; or no indexes on FK/filter columns.
- `SELECT *` and loading entire aggregates to read one field in hot paths.
- N+1 queries hidden by ORM lazy loading.
- Entity-Attribute-Value tables instead of proper schema or `jsonb`.
- Long transactions spanning HTTP calls or user think-time.
- Editing applied migrations; manual production schema changes.
- MongoDB documents with unbounded arrays; using Mongo like a relational DB with many cross-collection "joins".

## Quality checklist
- [ ] Access patterns listed and each critical query has a supporting index.
- [ ] Constraints (PK, FK, UNIQUE, NOT NULL, CHECK / `$jsonSchema`) enforce invariants.
- [ ] Correct types for money, time, identifiers.
- [ ] Migration is versioned, backward compatible with the running app, and safe for table size.
- [ ] No destructive operation without approval and backup plan.
- [ ] Concurrency strategy defined (optimistic/pessimistic).
- [ ] Query plans checked for critical/slow queries.
- [ ] Tests run against the real engine.

## Examples
**PostgreSQL migration (Flyway)**
```sql
-- V7__create_orders.sql
CREATE TABLE orders (
  id           uuid PRIMARY KEY,
  customer_id  uuid        NOT NULL REFERENCES customers(id),
  status       text        NOT NULL CHECK (status IN ('PENDING','PAID','SHIPPED','CANCELLED')),
  total_amount numeric(12,2) NOT NULL CHECK (total_amount >= 0),
  currency     char(3)     NOT NULL,
  version      bigint      NOT NULL DEFAULT 0,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_orders_customer_created ON orders (customer_id, created_at DESC);
CREATE INDEX idx_orders_open ON orders (created_at) WHERE status = 'PENDING';
```

**MongoDB embedding decision**
```js
// Order embeds its bounded line items; references the customer.
{ _id: ObjectId(), customerId: ObjectId(), status: "PAID",
  items: [{ productId: ObjectId(), name: "Mug", unitPrice: Decimal128("9.90"), qty: 2 }],
  createdAt: ISODate() }
db.orders.createIndex({ customerId: 1, createdAt: -1 })  // E then S
```

## References
- PostgreSQL documentation: https://www.postgresql.org/docs/current/
- PostgreSQL — Using EXPLAIN: https://www.postgresql.org/docs/current/using-explain.html
- PostgreSQL — Indexes: https://www.postgresql.org/docs/current/indexes.html
- PostgreSQL — Transaction isolation: https://www.postgresql.org/docs/current/transaction-iso.html
- MongoDB — Data modeling: https://www.mongodb.com/docs/manual/data-modeling/
- MongoDB — ESR rule for indexes: https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/
- Flyway documentation: https://documentation.red-gate.com/flyway
- Liquibase documentation: https://docs.liquibase.com/
- Use The Index, Luke: https://use-the-index-luke.com/
