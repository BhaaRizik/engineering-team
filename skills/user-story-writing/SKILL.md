---
name: user-story-writing
description: Writing and decomposing backlog items — Epic → User Story → Subtask hierarchy, features as product capabilities, the "As a / I want / So that" format, INVEST, story splitting patterns (workflow steps, business rules, data variations, CRUD, roles, happy/unhappy paths, spikes), when to use technical Tasks instead of stories, and the full story template including priority, dependencies, requirement references, and the suggested implementation agent. Use when converting analyzed requirements into epics, stories, and tasks, or when splitting or reviewing backlog items.
---

# User Story Writing

## Purpose
Produce backlog items that are meaningful, small, testable, and traceable — and that the engineering agents can pick up without guessing. Acceptance criteria detail is in `acceptance-criteria`; ordering in `backlog-prioritization`; Jira creation in `jira-backlog-management`.

## When to use
- Building a backlog from a completed requirements analysis.
- Splitting large or vague items.
- Reviewing backlog quality before presenting it for approval.

## Best practices
**Hierarchy**
```text
Project
 └── Epic (business capability / large product area, e.g. "Appointment booking")
      ├── Feature (logical capability grouping — expressed via labels/components or story grouping, not necessarily a Jira issue)
      └── Story (independently testable user value)  /  Task (technical work without direct user value)
           └── Subtask (only when a story genuinely needs separately tracked parts, e.g. backend + frontend + tests owned by different agents)
```
- Epics: 3–15 stories each is typical; an epic with 1 story is probably a story; with 40 it is probably two epics.
- Don't create issues for every technical detail; implementation details belong in the story description or subtasks.

**Story format**
> As a **[actor from the analysis]**, I want **[capability]**, so that **[business value]**.
The "so that" must name real value; if it can't, the item may be a Task.

**INVEST**: Independent, Negotiable, Valuable, Estimable, Small (fits comfortably in a sprint), Testable.

**Splitting patterns** (apply in order until stories are small and testable)
1. Workflow steps (search → select → book → confirm).
2. Business rule variations (standard booking, booking with deposit).
3. Happy path first, then unhappy paths/error handling as separate stories when substantial.
4. Data/input variations (single vs. recurring appointment).
5. Roles (patient vs. receptionist doing the same action).
6. Operations (create / view / edit / cancel) when each has real logic.
7. Interface (basic UI first, enhanced UI later).
8. Spike (time-boxed investigation) when uncertainty blocks estimation — output is a decision, not code.

**Story vs. Task**
- Story: observable user/business value.
- Task: technical enablers — CI/CD pipeline, environment setup, architecture spike, security hardening, test infrastructure, data migration. Tasks still get acceptance criteria and an owner.

**Story template (all fields required)**
| Field | Content |
|---|---|
| Title | Verb + object, specific ("Patient cancels a booking up to 24 h before start") |
| Description | Context, scope notes, out-of-scope notes, UX/API notes if known |
| User story | As a / I want / So that |
| Business value | Why it matters, which objective it supports |
| Acceptance criteria | Testable criteria (see `acceptance-criteria`) |
| Priority | Highest / High / Medium / Low (see `backlog-prioritization`) |
| Release category | MVP / Future / Optional / Technical improvement |
| Epic | Parent epic |
| Dependencies | Blocking items (IDs), external dependencies |
| Suggested agent | Primary agent + supporting agents + execution order |
| Estimate | Story points if the team has an agreed method, else "Pending — needs <agent>" |
| Requirement refs | FR/NFR/BR IDs and source references |

**Agent assignment guide**
| Work | Primary | Typical support |
|---|---|---|
| REST API, business logic, persistence | `backend` | `architect` (design), `qa` (tests) |
| React UI, pages, forms, client state | `frontend` | `backend` (contract), `qa` |
| Cross-cutting design, module boundaries, tech choices, spikes on architecture | `architect` | relevant specialists |
| Auth, roles, sensitive data, security review | `security` (review) / `backend` or `frontend` (implementation) | `architect` |
| Test strategy, automated/regression/E2E tests | `qa` | owning engineer |
| CI/CD, environments, deployment, monitoring infra | `devops` | `security` (secrets) |
Full-stack stories: primary = the agent owning most of the work or the API contract (usually `backend`), supporting = `frontend`, `qa`; order: architect (if needed) → backend → frontend → qa → security review (if sensitive).

## Workflow
1. Group analyzed requirements into epics by business capability.
2. Within each epic, identify features and draft stories along the user journey.
3. Apply splitting patterns until each story is INVEST-compliant.
4. Add technical Tasks for enablers; add Subtasks only where ownership or tracking requires it.
5. Fill every template field; write acceptance criteria.
6. Map every FR/NFR/BR to at least one item (traceability check).
7. Assign suggested agents and dependencies.

## Decision-making guidelines
- **Story or subtask?** Independently valuable and testable → story. A part of one story's implementation → subtask (or just description).
- **Split or keep?** Split if it has more than ~6–8 acceptance criteria, spans multiple roles or workflows, or can't be finished within a sprint.
- **NFRs**: global NFRs (e.g. performance budget) → acceptance criteria on relevant stories or a Definition of Done note; NFRs needing dedicated work (e.g. set up monitoring) → Task.

## Anti-patterns
- Vague stories: "Implement authentication", "Create the backend", "Fix frontend", "Manage users".
- Layer-based stories ("build the database", "build the UI") instead of vertical slices.
- Stories with no "so that" value or with the actor "as a developer" for product features.
- One issue per technical detail; or giant stories with 20 acceptance criteria.
- Orphan stories without an epic; stories without requirement references.
- Assigning to imaginary people instead of recording the suggested agent.

## Quality checklist
- [ ] Every story follows the format and has all template fields.
- [ ] Every story is INVEST; none oversized.
- [ ] Every story/task has a parent epic; no orphans.
- [ ] Every FR/NFR/BR maps to at least one item; no duplicates.
- [ ] Technical work expressed as Tasks; subtasks only where useful.
- [ ] Dependencies and suggested agents filled in.

## Examples
**Vague → split**
"Implement authentication" →
- Visitor registers with email and password
- Registered user logs in with email and password
- User resets a forgotten password via an emailed link
- User logs out from all devices
- Task: Security review of authentication flows (`security`)

**Complete story**
```markdown
**Title:** Patient cancels a booking up to 24 h before start
**User story:** As a patient, I want to cancel my booking up to 24 hours before it starts, so that the slot can be offered to someone else and I avoid a no-show fee.
**Business value:** Reduces no-shows (objective O-2).
**Acceptance criteria:** see AC-1…AC-4 (Given/When/Then)
**Priority:** High · **Release:** MVP · **Epic:** Appointment booking
**Dependencies:** "Patient books an appointment"
**Suggested agent:** Primary backend · Support frontend, qa · Order: backend API → frontend UI → qa tests
**Estimate:** Pending — needs backend/frontend input
**Requirement refs:** FR-02, BR-04 (spec.pdf §2.2, §4)
```

## References
- Atlassian — User stories: https://www.atlassian.com/agile/project-management/user-stories
- Atlassian — Epics, stories, themes: https://www.atlassian.com/agile/project-management/epics-stories-themes
- Bill Wake — INVEST in Good Stories: https://xp123.com/articles/invest-in-good-stories-and-smart-tasks/
- Humanizing Work — Guide to splitting user stories: https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/
- Mike Cohn — User stories: https://www.mountaingoatsoftware.com/agile/user-stories
