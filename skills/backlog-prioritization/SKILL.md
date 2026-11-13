---
name: backlog-prioritization
description: Ordering and classifying a product backlog — Highest/High/Medium/Low priority scale, MVP vs. future enhancement vs. optional vs. technical improvement, MoSCoW, value/risk/effort trade-offs (lightweight WSJF/RICE), dependency-aware sequencing, release slicing, and honest estimation policy (story points only with an agreed team method; pending estimates requested from engineering agents). Use when prioritizing or re-prioritizing a backlog, defining an MVP release, sequencing work with dependencies, or handling estimates.
---

# Backlog Prioritization

## Purpose
Give the backlog a defensible order so the most valuable, riskiest, and most-depended-upon work comes first — with estimates that are honest about uncertainty. Scope framing is in `product-management`; item structure in `user-story-writing`.

## When to use
- After stories are drafted and before presenting the backlog.
- When the user changes scope, priorities, or deadlines.
- Planning releases or sprints; resolving priority conflicts.

## Best practices
**Priority scale (maps to Jira priorities if they exist)**
| Priority | Meaning |
|---|---|
| **Highest** | MVP-critical and blocking other work, or addresses major risk/compliance; nothing ships without it |
| **High** | MVP-required core functionality |
| **Medium** | Valuable; MVP-nice-to-have or early follow-up release |
| **Low** | Optional or later improvement |
If the Jira project uses different priority names, map to them and show the mapping.

**Release category (separate from priority)**: MVP · Future enhancement · Optional · Technical improvement. Labels such as `mvp`, `future`, `optional`, `tech-improvement` make this filterable in Jira.

**Factors** (state the main reason for each Highest/High item)
- Business value and user impact.
- Risk reduction (unknown integrations, security, regulatory) — risky items early.
- Dependencies — enablers before dependents.
- Technical complexity (from engineering input, not PO guesswork).
- MVP necessity.

**Techniques**
- **MoSCoW** to set the MVP boundary (Must = MVP; Should/Could = Future/Optional; Won't = out of scope this release).
- **Lightweight WSJF / RICE** only when many items compete at the same level — use relative scores, show the inputs, and treat the result as an aid, not a verdict.

**Sequencing**
- Build a dependency list (A blocks B). Order: architecture/enabler tasks → core backend capabilities → dependent UI → cross-cutting hardening → enhancements.
- Prefer a **walking skeleton**: the thinnest end-to-end slice of the core journey first (with minimal CI/CD and deployment) to reduce integration risk early.
- Note parallelizable streams (e.g. frontend against an agreed API contract while backend implements).

**Estimation policy**
- Use story points only if the team has an agreed method (ask the user which scale, e.g. Fibonacci 1–13, and the reference story).
- The PO doesn't invent estimates. Request estimates from the relevant engineering agent via the architect, or mark `Estimate: Pending — needs <agent>`.
- Large uncertainty → spike task first; estimate after.
- Never present precise totals ("delivery in 37 days") derived from guesses.

## Workflow
1. Classify each item's release category (MVP/Future/Optional/Technical improvement).
2. Assign priority using the scale and factors; write the reason for Highest/High.
3. Map dependencies and derive an execution order.
4. Identify the walking skeleton and parallel streams.
5. Collect or mark estimates per the policy.
6. Present the ordered backlog with rationale; invite the user to change priorities.
7. Re-run after any change and show what moved and why.

## Decision-making guidelines
- **Two items both "Highest"** → the one others depend on, or that retires more risk, goes first.
- **Conflict between user priority and dependency order** → keep the user's priority but show the blocking prerequisite and its impact.
- **Too much MVP** → show the MVP size and propose concrete cuts with impact; the user decides.

## Anti-patterns
- Everything "High".
- Prioritizing by ease instead of value/risk.
- Hidden dependencies discovered mid-sprint.
- Invented story points or deadlines.
- Re-prioritizing silently without telling the user what changed.

## Quality checklist
- [ ] Every item has priority and release category.
- [ ] Highest/High items have a stated reason.
- [ ] Dependencies mapped; no item scheduled before its blocker.
- [ ] MVP is complete (all MVP requirements covered) and minimal.
- [ ] Estimates are either from an agreed method/engineering input or marked pending.

## Examples
```markdown
| Order | Item | Priority | Release | Depends on | Reason |
|---|---|---|---|---|---|
| 1 | Task: Architecture & API contract for booking (architect) | Highest | MVP | — | Unblocks backend and frontend streams |
| 2 | Task: CI pipeline + staging deploy (devops) | Highest | MVP | — | Walking skeleton; early integration risk |
| 3 | Patient books an appointment | High | MVP | 1 | Core journey |
| 4 | Patient cancels a booking up to 24 h before | High | MVP | 3 | Core journey; reduces no-shows |
| 5 | SMS reminders | Medium | Future | 3 | Valuable but email covers MVP |
| 6 | Patient reviews | Low | Optional | 3 | Not tied to an objective |
```

## References
- Scrum Guide — Product Backlog: https://scrumguides.org/scrum-guide.html#product-backlog
- Atlassian — Backlog prioritization techniques: https://www.atlassian.com/agile/product-management/prioritization-framework
- MoSCoW method (Agile Business Consortium): https://www.agilebusiness.org/dsdm-project-framework/moscow-prioririsation.html
- SAFe — WSJF: https://framework.scaledagile.com/wsjf
- Intercom — RICE: https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/
