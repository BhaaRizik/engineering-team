---
name: acceptance-criteria
description: Writing testable, unambiguous acceptance criteria — Given/When/Then (Gherkin) scenarios, rule-based checklists, covering happy paths, validation, errors, permissions, edge cases, and relevant non-functional criteria; distinguishing acceptance criteria from the Definition of Done; and making criteria directly usable by QA and engineering agents. Use when writing or reviewing acceptance criteria for stories and tasks, or when a story's "done" is unclear.
---

# Acceptance Criteria

## Purpose
Define exactly when a backlog item is done, in a form `qa` can turn into tests and engineers can implement without guessing. Story structure is in `user-story-writing`; test design depth is in `testing-strategy`.

## When to use
- Every story and task before it is presented for approval.
- Reviewing a backlog for "missing acceptance criteria".
- A disagreement about whether something is done.

## Best practices
- **Testable**: each criterion has an observable outcome (UI state, API response, data change, message sent).
- **Unambiguous**: concrete values instead of adjectives ("within 2 seconds", "max 2 active bookings", "error message 'Email already registered'") — use values from the requirements; if unknown, it's a question, not a guess.
- **Behavior, not implementation**: no class names, frameworks, or database tables unless the requirement itself is technical (Tasks).
- **Independent and numbered** (AC-1, AC-2 …) so tests and discussions can reference them.
- **Coverage per story** (include only what applies):
  1. Happy path.
  2. Validation rules (required fields, formats, limits).
  3. Business rules (each BR referenced).
  4. Error and failure handling (integration down, conflict, not found).
  5. Permissions (who can / cannot — include a negative case).
  6. Edge cases (boundaries, duplicates, concurrency, time zones, empty states).
  7. Relevant NFRs (performance, accessibility, audit, privacy) when specific to this story.
- **Format choice**:
  - Given/When/Then for behavior and flows.
  - Rule checklist for simple constraints or UI content.
- 3–8 criteria per story is typical; more suggests splitting.
- **Definition of Done (DoD)** is team-wide and separate (code reviewed, tests pass, docs updated, deployed to staging). Don't repeat DoD items in each story's AC.

## Workflow
1. Re-read the story, its requirement refs, and related business rules.
2. Write the happy-path scenario.
3. Add scenarios for each validation rule, business rule, error, permission, and edge case that applies.
4. Add NFR criteria specific to this story.
5. Check each criterion: observable? concrete values? traceable to a requirement or approved decision?
6. Mark any criterion based on an unapproved assumption as "(pending confirmation of A-nn)".

## Decision-making guidelines
- **Gherkin or checklist?** Multi-step behavior or state changes → Given/When/Then. Static rules/content → checklist.
- **AC or new story?** If a criterion introduces a new user capability, it's a new story.
- **Unknown values** (limits, messages, timings) → open question to the user, never invented.

## Anti-patterns
- "Works correctly", "is user-friendly", "is secure", "is fast".
- Restating the story as the only criterion.
- Implementation instructions as criteria ("use a POST endpoint", "store in Redis") in user stories.
- Missing negative/permission cases.
- Invented numbers presented as requirements.
- Copying the DoD into every story.

## Quality checklist
- [ ] Every story/task has numbered acceptance criteria.
- [ ] Happy path, validation, business rules, errors, permissions, and edge cases covered where applicable.
- [ ] Concrete, observable outcomes; no vague adjectives.
- [ ] Each criterion traceable to a requirement, rule, or approved decision.
- [ ] Assumption-based criteria marked pending.
- [ ] Criteria count suggests the story is appropriately sized.

## Examples
**Given/When/Then**
```gherkin
AC-1 Successful cancellation
  Given a patient with a confirmed booking starting in 30 hours
  When the patient cancels the booking
  Then the booking status becomes "Cancelled"
  And the slot becomes available for other patients
  And the patient receives a cancellation confirmation email

AC-2 Cancellation window closed
  Given a patient with a confirmed booking starting in 20 hours
  When the patient tries to cancel the booking
  Then the cancellation is rejected
  And the message "Bookings can only be cancelled up to 24 hours in advance" is shown

AC-3 Not the owner
  Given a patient viewing another patient's booking reference
  When they try to cancel it
  Then the system responds as if the booking does not exist

AC-4 Already cancelled
  Given a booking that is already cancelled
  When the patient cancels it again
  Then no change is made and the patient sees the booking as "Cancelled"
```
**Checklist (Task: CI pipeline)**
- AC-1 Every pull request runs build, unit tests, and integration tests.
- AC-2 A failing test blocks merging.
- AC-3 Pipeline results are visible on the pull request.

## References
- Cucumber — Gherkin reference: https://cucumber.io/docs/gherkin/reference/
- Atlassian — Acceptance criteria: https://www.atlassian.com/work-management/project-management/acceptance-criteria
- Scrum.org — Definition of Done: https://www.scrum.org/resources/what-definition-done
