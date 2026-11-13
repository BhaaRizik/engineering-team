---
name: requirements-analysis
description: Systematic requirements analysis from Markdown, README, PDF, Word, plain-text, or existing project documentation — extracting functional and non-functional requirements, business rules, actors, system boundaries, integrations, constraints, and dependencies; classifying explicit requirements vs. assumptions vs. recommendations vs. open questions; finding ambiguities, contradictions, risks, and edge cases; writing focused clarification questions; and keeping requirement IDs for traceability. Use whenever requirements or specification documents are provided and before any backlog is created.
---

# Requirements Analysis

## Purpose
Turn raw requirement material into a structured, traceable, honest understanding of what is being asked — and what is not yet known. Product framing is in `product-management`; turning results into stories is in `user-story-writing`.

## When to use
- Any new requirements document or project brief.
- Change requests to an existing backlog.
- Before asking the user clarification questions or preparing a backlog.

## Best practices
**Reading the sources**
- Read **everything** supplied before concluding. Note each source's name, version/date, and section structure.
- Formats: Markdown/README/text → Read. PDF → Read (page ranges for long files). Word `.docx` → convert to text read-only (macOS: `textutil -convert txt -stdout file.docx`; elsewhere `pandoc file.docx -t plain`), or ask the user for a PDF/Markdown export if no converter is available. Never modify source documents.
- Existing projects: also read README, docs, API specs, and existing tickets to avoid re-specifying what exists.

**Extraction categories** (give each item an ID for traceability)
| Category | ID prefix | Example |
|---|---|---|
| Functional requirement | FR-nn | FR-04 Patient can cancel a booking up to 24 h before |
| Non-functional requirement | NFR-nn | NFR-02 Booking page loads in < 2 s on 4G |
| Business rule | BR-nn | BR-01 Max 2 active bookings per patient |
| Actor / role | ACT-nn | ACT-02 Receptionist |
| Integration / external system | INT-nn | INT-01 SMTP provider for emails |
| Constraint | CON-nn | CON-01 Must run on existing AWS account |
| Data entity | DATA-nn | DATA-03 Appointment (date, practitioner, patient, status) |
Record the **source reference** for each item (`spec.pdf p.4 §2.3`, `README.md#booking`).

**Classification — always explicit**
- **Explicit requirement**: stated in the sources (cite it).
- **Assumption**: needed to proceed, not stated; reasonable but unapproved.
- **Recommendation**: the PO's suggestion (e.g. add audit logging) — never silently added to scope.
- **Open question**: needs the user's decision.

**NFR checklist** (ask only where relevant): security and privacy (PII, GDPR), authentication/roles, performance, availability, scalability, accessibility (WCAG), localization/time zones/currency, browser/device support, audit/compliance, data retention, backup, observability.

**Finding gaps**
- Ambiguity: vague words ("fast", "secure", "user-friendly", "etc.", "manage", "support").
- Incompleteness: CRUD gaps (create without edit/delete), missing error/empty states, missing roles/permissions, undefined lifecycle states, missing notifications.
- Contradictions between sources or sections.
- Edge cases: concurrency, limits, time zones, cancellations, duplicates, partial failures of integrations.
- Risks: unclear integrations, regulatory exposure, data migration, third-party dependencies.

**Clarification questions**
- Group by topic (Business behavior, Users & permissions, Data, Integrations, Security & compliance, UX).
- Order by impact; mark each **Blocking** (backlog can't be correct without it) or **Non-blocking** (a stated default assumption applies).
- Offer options and a recommended default where possible ("A) hard delete, B) soft delete with 30-day restore — recommend B because…").
- Aim for the fewest questions that resolve the most uncertainty (typically ≤ 10 in the first round).

## Workflow
1. Inventory sources.
2. Read fully; extract items into the categories with IDs and references.
3. Classify each item (explicit / assumption / recommendation / question).
4. Run the gap, contradiction, edge-case, and risk passes.
5. Flag architecture-significant items for the architect (integrations, scale, security model, data residency).
6. Produce the analysis summary and grouped questions.
7. After answers: update items, record decisions (`product-management` decision log), re-check for new gaps.

## Decision-making guidelines
- If a missing detail changes business behavior, data, security, integrations, or UX → question, not assumption.
- If a reasonable industry default exists and impact is low → assumption with the default stated, flagged for confirmation.
- If two sources conflict → never pick one silently; ask, citing both.

## Anti-patterns
- Starting the backlog before reading all sources.
- Turning recommendations into requirements without approval.
- 40 unprioritized questions, or questions already answered in the documents.
- Losing source references, making later traceability impossible.
- Treating NFRs as an afterthought.

## Quality checklist
- [ ] All sources read and listed.
- [ ] Every item has an ID, category, classification, and source reference.
- [ ] NFRs considered for relevant categories.
- [ ] Ambiguities, contradictions, edge cases, and risks listed.
- [ ] Questions grouped, prioritized, blocking/non-blocking marked, with recommended defaults.
- [ ] Architecture-significant items flagged for the architect.

## Examples
**Analysis summary excerpt**
```markdown
### Functional requirements
- FR-01 Patient books an appointment for a treatment and practitioner (spec.pdf §2.1) — Explicit
- FR-02 Patient cancels a booking (spec.pdf §2.2) — Explicit; cancellation window not specified → Q-03
### Business rules
- BR-01 Slot length depends on treatment type (spec.pdf §3.1) — Explicit
### Assumptions
- A-01 All times shown in the clinic's local time zone — Assumption (non-blocking)
### Recommendations
- R-01 Audit log of booking changes for staff disputes — Recommendation (not in scope unless approved)
```
**Question**
> **Q-03 (Blocking — Business behavior):** Until when can a patient cancel? A) any time, B) up to 24 h before (recommended — matches the no-show policy mentioned in §4), C) configurable per clinic.

## References
- IIBA BABOK Guide overview: https://www.iiba.org/career-resources/a-business-analysis-professionals-foundation-for-success/babok/
- ISO/IEC 25010 quality model (NFR categories): https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
- Atlassian — Product requirements documents: https://www.atlassian.com/agile/product-management/requirements
