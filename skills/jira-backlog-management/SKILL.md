---
name: jira-backlog-management
description: Safely creating and managing a Jira backlog through an MCP or other Jira integration — detecting whether Jira tools are connected, discovering projects, issue types, hierarchy, fields (Story Points, custom "Assigned Agent"), priorities, statuses, and permissions; the mandatory approval gate before any issue is created; parent-before-child creation, epic/parent linking, dependency links, agent-ownership labels, duplicate prevention with JQL, verification, and honest reporting of created and failed issues. Use whenever Jira is involved — setup, discovery, issue creation or updates, or reporting backlog status.
---

# Jira Backlog Management

## Purpose
Turn an **approved** backlog into correct Jira issues — or explain exactly what is needed when Jira isn't connected — without duplicates, guesses, or false success claims. Backlog content comes from `user-story-writing`, `acceptance-criteria`, and `backlog-prioritization`.

## When to use
- A new project needs a Jira connection and discovery.
- The user approved a backlog for creation.
- Updating, linking, or reporting on Jira issues.

## Best practices
**0. Approval gate (non-negotiable)**
- No create/edit/transition/delete/link/comment operation in Jira without the user's explicit approval **of that specific backlog or change**, given in the current conversation (e.g. "Approved — create these in Jira"). Approval of the analysis, or a general "looks good" on part of it, is not approval to create.
- Read-only discovery (list projects, fields, issue types, search) is allowed before approval.
- Before creating, restate what will be created (counts by type, project key) and confirm that matches the approval.

**1. Detect the integration**
- Search for Jira tools: use `ToolSearch` with queries like `jira`, `atlassian`, `issue` and inspect the `mcp__…` tools found (e.g. tools to list accessible resources/projects, get issue-type metadata, create/edit issues, search with JQL, create issue links). Tool names differ between integrations — use what is actually available.
- If none are found, say so plainly and explain the setup (below). Never simulate issue creation or invent issue keys.

**Setup guidance when Jira isn't connected**
- Option A — Atlassian's remote MCP server (Jira Cloud): add it to Claude Code (`claude mcp add --transport http <name> <Atlassian MCP URL>` — get the current URL from Atlassian's MCP documentation), then authenticate via `/mcp`.
- Option B — an Atlassian/Jira connector enabled in the user's claude.ai account (synced to Claude Code).
- Option C — another Jira MCP server the organization uses (e.g. for Jira Data Center), configured with an API token stored outside the repository.
- After setup, restart the session and re-run discovery.

**2. Discover before creating** (read-only)
- Site/cloud ID if the tool requires it; the project (from URL or key the user gives).
- Issue types and hierarchy: Epic, Story, Task, Bug, Sub-task (names may be localized or customized; team-managed vs. company-managed projects differ).
- Create-screen fields per issue type: required fields, Story Points field name/ID (often "Story Points" or "Story point estimate"), custom field "Assigned Agent" if it exists, labels, components, priority values.
- How parent links work: modern Jira uses the `parent` field for Story → Epic and Sub-task → Story; older company-managed projects may use an "Epic Link" field — detect which.
- Issue link types for dependencies (e.g. "Blocks").
- Permissions: can the connected account create issues in this project?
- Existing issues: search with JQL for similar summaries/epics to avoid duplicates (`project = KEY AND summary ~ "\"cancel booking\""`).
- Present a short discovery summary and any mismatches (e.g. no Sub-task type, no Story Points field).

**3. Map the backlog to Jira**
| Backlog field | Jira |
|---|---|
| Title | Summary |
| Description, user story, business value, AC, requirement refs | Description (structured headings; AC as numbered list or Gherkin block) |
| Priority | Priority (mapped to the project's values) |
| Epic | `parent` (or Epic Link) |
| Dependencies | Issue links ("is blocked by") |
| Suggested agent | "Assigned Agent" custom field if it exists; otherwise labels `agent-backend`, `agent-frontend`, `agent-architect`, `agent-security`, `agent-qa`, `agent-devops`, `agent-po` (primary first; supporting agents named in the description) |
| Release category | Labels `mvp`, `future`, `optional`, `tech-improvement` (or Fix Version if the user prefers) |
| Estimate | Story Points field only if an agreed estimate exists |
- Never set the Jira **Assignee** to a person unless the user explicitly names a real Jira user to assign.
- Add one batch label (e.g. `po-import-2026-03-02`) to every created issue to make verification and cleanup easy.

**4. Create in order**
1. Epics → record keys.
2. Stories and Tasks with `parent` = epic key.
3. Sub-tasks with `parent` = story key.
4. Dependency links after both sides exist.
- Before each create, check (JQL by summary + batch label) that it doesn't already exist — makes retries safe.
- On a failure: stop the dependent chain, record the error, continue with independent items, and report.

**5. Verify and report**
- Re-query by batch label; compare against the approved list (counts by type, parents, labels, priorities).
- Report: Key · Summary · Type · Parent Epic · Priority · Agent · URL (`https://<site>/browse/<KEY>`), plus failures with error messages and what remains to be done.

## Workflow
1. Ask for the Jira project URL / key (and configuration details only if discovery can't find them).
2. Detect tools → discover configuration (read-only) → summarize.
3. Map the approved backlog; show the mapping and any adaptations (e.g. no Sub-task type → use checklist in description).
4. Confirm the approval matches what will be created.
5. Create in order with duplicate checks.
6. Verify and report honestly.

## Decision-making guidelines
- **Missing field (e.g. no Story Points)** → omit and note in the report; don't create custom fields without approval.
- **Hierarchy mismatch** (e.g. team-managed project without Sub-task) → propose the adaptation and get approval before creating.
- **Possible duplicate found** → don't create; list it and ask whether to reuse, update, or create anyway.
- **Partial failure** → never claim completion; report created keys and failed items separately.

## Anti-patterns
- Creating issues before explicit approval, or treating analysis approval as creation approval.
- Pretending an issue was created or fabricating keys/URLs.
- Creating children before parents, or orphan stories.
- Re-running creation and producing duplicates.
- Assigning to imaginary users; creating custom fields or changing project settings without approval.
- Dumping acceptance criteria as an unreadable single paragraph.

## Quality checklist
- [ ] Explicit approval for this exact backlog recorded (quote it).
- [ ] Integration detected and project configuration discovered.
- [ ] Duplicate search done.
- [ ] Parents created before children; all stories linked to epics.
- [ ] Agent ownership recorded (custom field or `agent-*` labels); no fake assignees.
- [ ] Dependencies linked.
- [ ] Verification query matches the approved list; failures reported.

## Examples
**Description body**
```markdown
**User story**
As a patient, I want to cancel my booking up to 24 hours before it starts, so that the slot can be reused.

**Business value**
Reduces no-shows (O-2).

**Acceptance criteria**
AC-1 Given … When … Then …
AC-2 …

**Suggested agents**
Primary: backend · Supporting: frontend, qa · Order: backend → frontend → qa

**Requirement references**
FR-02, BR-04 (spec.pdf §2.2, §4)
```
**Final report**
| Key | Summary | Type | Epic | Priority | Agent | URL |
|---|---|---|---|---|---|---|
| CB-1 | Appointment booking | Epic | — | High | agent-architect | https://example.atlassian.net/browse/CB-1 |
| CB-2 | Patient cancels a booking up to 24 h before | Story | CB-1 | High | agent-backend | https://example.atlassian.net/browse/CB-2 |
Failed: 1 — "Task: Staging environment" (error: field "Story Points" not on create screen) — not created; needs decision.

## References
- Atlassian Remote MCP Server: https://support.atlassian.com/rovo/docs/getting-started-with-the-atlassian-remote-mcp-server/
- Claude Code MCP: https://docs.claude.com/en/docs/claude-code/mcp
- Jira issue types and hierarchy: https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/
- JQL reference: https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jira-query-language-jql/
- Jira Cloud REST API (issues, fields, links): https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
