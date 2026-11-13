---
name: product-management
description: Product ownership fundamentals for turning a product idea into a deliverable plan — product vision and business objectives, stakeholder and user identification, MVP scoping vs. future enhancements, roadmap framing, decision and assumption logs, stakeholder communication, and the Product Owner's boundaries with the architect and engineering team. Use when starting a new product or project, framing scope and MVP, communicating plans or trade-offs to stakeholders, or recording product decisions.
---

# Product Management

## Purpose
Give the Product Owner a consistent way to frame **why** a product exists, **for whom**, and **what is in scope now**, and to keep decisions traceable. Detailed requirement extraction is in `requirements-analysis`; story writing in `user-story-writing`; ordering in `backlog-prioritization`; Jira mechanics in `jira-backlog-management`.

## When to use
- A new project or major feature arrives with requirements documents.
- Scope is unclear, too big, or contested; an MVP must be defined.
- A product decision needs to be made, approved, and recorded.
- Communicating backlog status, trade-offs, or changes to the user/stakeholders.

## Best practices
**Vision and objectives**
- Write a one-paragraph product vision: target users, problem, proposed solution, key differentiator.
- Translate goals into 2–5 measurable business objectives (outcome, metric, target, timeframe) when the requirements support it. If no metrics are given, propose them as **recommendations**, not facts.

**Users and stakeholders**
- Separate *users* (interact with the product — personas/actors with roles and permissions) from *stakeholders* (care about outcomes — sponsors, operations, compliance, support).
- For each actor: goals, key tasks, frequency, permissions, constraints (device, accessibility, locale).

**Scope and MVP**
- MVP = the smallest set of capabilities that delivers the core value to the primary user and can be validated. Everything else is labeled Future enhancement, Optional, or Technical improvement.
- Define explicit **out of scope** items — they prevent silent scope creep.
- Prefer thin end-to-end slices (one actor completing one core journey) over completing one layer at a time.

**Decision log** (keep it current and show it with every backlog proposal)
| ID | Date | Decision / Assumption | Type | Source | Status |
|---|---|---|---|---|---|
| D-01 | 2026-03-02 | Users log in with email + password; no social login in MVP | Decision | User approval in chat | Approved |
| A-03 | 2026-03-02 | Single currency (EUR) | Assumption | PO | Pending approval |
Types: Explicit requirement, Assumption, Recommendation, Decision. Only the user can turn an assumption into an approved decision.

**Role boundaries**
- PO owns: problem, users, scope, priorities, acceptance criteria, backlog.
- Architect owns: technical feasibility, architecture, technical decomposition, technical dependencies.
- Engineers own: implementation and technical feedback (estimates, edge cases).
- The PO never decides architecture or technology; it asks the architect and records the answer.

**Communication**
- Lead with the decision needed, then the context. Offer options with a recommendation and its trade-off.
- Keep status updates short: done, in progress, blocked (and by whom), decisions needed.

## Workflow
1. Read all supplied material (see `requirements-analysis`).
2. Draft vision, objectives, actors, stakeholders.
3. Propose MVP boundary, future enhancements, optional items, and out-of-scope list.
4. Identify decisions needed from the user; ask them (grouped, prioritized).
5. Record answers in the decision log.
6. Consult the architect on anything with significant architectural implications.
7. Proceed to backlog decomposition (`user-story-writing`) and prioritization (`backlog-prioritization`).

## Decision-making guidelines
- **Is it MVP?** Without it, can the primary user complete the core journey and can the business validate the core hypothesis? If yes without it → not MVP.
- **Decide or ask?** Anything affecting business behavior, money, legal/compliance, security, data ownership, user-visible UX flows, or integrations → ask. Naming, ordering within the same priority, formatting → the PO may decide and record it.
- **Conflicting stakeholder needs** → surface both, show the impact of each, recommend one, and let the user decide.

## Anti-patterns
- Inventing requirements or metrics and presenting them as given.
- "Everything is MVP."
- Silent assumptions that change business behavior.
- Making architecture or technology choices as the PO.
- Letting the decision log drift out of date or exist only in scattered chat messages.
- Long status reports that bury the decisions needed.

## Quality checklist
- [ ] Vision and objectives stated; metrics marked as given vs. recommended.
- [ ] Actors and stakeholders identified with goals and permissions.
- [ ] MVP, future, optional, technical improvements, and out-of-scope clearly separated.
- [ ] Every assumption labeled and either approved or flagged pending.
- [ ] Architect consulted on architecture-significant items.
- [ ] Decision log current.

## Examples
**Vision**
> For small clinic receptionists who juggle phone and paper bookings, *ClinicBook* is a web booking system that lets patients self-schedule appointments and lets staff manage the day's calendar in one place — unlike generic calendar tools, it enforces clinic-specific rules (slot length per treatment, practitioner availability).

**Scope summary**
| Category | Items |
|---|---|
| MVP | Patient self-booking, staff calendar, practitioner availability, email confirmations |
| Future | SMS reminders, online payments |
| Optional | Patient reviews |
| Technical improvement | Audit log export |
| Out of scope | Medical records, insurance billing |

## References
- The Scrum Guide (Product Owner, Product Backlog): https://scrumguides.org/scrum-guide.html
- Atlassian — Product management guides: https://www.atlassian.com/agile/product-management
- Roman Pichler — Product vision board: https://www.romanpichler.com/tools/product-vision-board/
