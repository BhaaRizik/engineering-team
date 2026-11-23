---
name: jira-feature-implementation
description: End-to-end implementation of a Jira issue with the engineering team. Use automatically whenever the user's message contains a Jira issue URL (https://<site>.atlassian.net/browse/KEY-123) or a Jira issue key of a known project such as PROJ-5 — even with no other words. Retrieves the issue (description, acceptance criteria, comments, parent/children, links, attachments) through the connected Jira MCP, then runs the team workflow — Product Owner analysis, Software Architect design, approval gate, backend/frontend implementation, security review, QA, verification — moves the issue In Progress → In Review → Done through the po agent, and reports verified results. Never fabricates Jira data or test results.
---

# Jira Feature Implementation

Turn a Jira issue into working, tested, reviewed code in the current project, using the engineering team. The user only supplies a key or URL; this skill supplies the workflow. Project-specific facts (repos, stack, conventions, commands, Jira project) come from the project's own instructions, never from assumptions.

**Plugin naming.** This skill ships in the `engineering-team` plugin. Team agents and skills named here by short names are invoked as `engineering-team:<name>`, e.g. Agent `subagent_type: "engineering-team:po"`, Skill `"engineering-team:jira-backlog-management"`. If an un-namespaced copy is also installed, prefer the `engineering-team:` version.

**The session that loads this skill is the Software Architect / orchestrator.** It follows the `architect` agent's instructions (phases, delegation brief template, governance, safety rules) and adds the Jira rules below. Where they differ, this skill wins for Jira handling; the project's `CLAUDE.md` / `PROJECT.md` win for product scope, stack, conventions and business rules.

## 0. Trigger and scope detection

Treat the message as a request to work on an issue when it contains:
- a Jira URL: `https://<site>.atlassian.net/browse/<KEY>` (also `…/jira/software/…?selectedIssue=<KEY>`), or
- a bare issue key matching `[A-Z][A-Z0-9]+-\d+` **whose project key is a known Jira project** (named in the project's `CLAUDE.md`, or returned by the Jira tools' project list), or that Jira confirms exists.

Not a trigger: tokens like `UTF-8`, `ISO-8601`, `HTTP-2`, `JDK-25`. If an unknown-prefix key fails lookup, carry on with the user's actual request.

Intent:
- Key/URL alone, or with "implement / work on / do / continue" → full workflow.
- "<KEY> merged" / "PR for <KEY> merged" → only the §10 `Done` step (verify the merge first).
- With an explicit narrower ask ("what is PROJ-5?", "estimate PROJ-14", "review PROJ-15 criteria") → do only that, using Stages 1–2 as needed. Do not start coding.
- Several keys with unclear scope → ask which one(s) to implement, in what order.

The user does not need to restate any of this workflow.

## 1. Stage 1 — Discovery (read-only)

Do these in parallel where possible. Track stages with TodoWrite.

### 1a. Project instructions
Read, every time (they change):
- `CLAUDE.md` and `PROJECT.md` (or README / docs that play that role) of the current repo, and of every sibling repo the issue may touch. A multi-repo workspace usually lists its repos in a workspace-level `CLAUDE.md`.
- Any `.claude/` settings, README and config files in the repos you'll touch (e.g. `application*.yaml`, `.env.example`, `.env.*` for frontends).

From them, extract the **project facts** this workflow needs: repo paths, stack and versions, architecture and code conventions, run and verification commands, configuration/secrets conventions, Jira site and project key, deployment target, and any standing approvals (e.g. test-data sync). Projects may keep a "Known project facts" section in `CLAUDE.md` for this skill; treat it as possibly stale and re-verify against the code.

If a needed fact is missing (e.g. no verification command documented), discover it from the build files; if it still can't be determined, ask at the approval gate.

### 1b. Retrieve the Jira issue
Use the authenticated Jira MCP integration:
1. Find the tools: `ToolSearch` with `jira` (and `atlassian` if nothing matches). Names differ between integrations (e.g. `mcp__jira__read_jira_issue`, `mcp__jira__search_jira_issues` on the community `mcp-atlassian` server; other names on the official Atlassian server), so use whatever is actually present.
2. Read the issue by key with all fields, including comments, attachments, links, subtasks and parent.
3. Children: search with JQL `parent = <KEY> ORDER BY rank` (epics and stories), then read each child that's in scope. If JQL search fails, read children by key from the issue's data and say parent links came from direct reads.
4. Parent: read the parent epic for context, if present.
5. Linked issues: read each `issuelinks` target; note blocks / is blocked by / relates.
6. Attachments: list them. Open only those relevant to the work (mockups, specs) and say which ones you could not open.

Collect: summary, type, status, priority, description, acceptance criteria (inside the description or a custom field), comments and clarifications (newest wins on conflict, but flag the conflict), labels, parent, children (key, type, summary, status), links and dependencies, attachments, requirement references (e.g. "Scope: FR-01").

The ADF description is nested JSON; extract its text faithfully. Do not summarize away acceptance criteria.

**If Jira access fails, stop and say exactly what's missing. Never pretend.**

| Symptom | Cause | Smallest action to ask for |
|---|---|---|
| No `jira`/`atlassian` tools found via ToolSearch | MCP server not registered or session not restarted | "Run `claude mcp list`; if the Jira server is ✔ Connected, restart Claude Code. Otherwise add it." |
| Tool returns 401 | Wrong email/token or revoked token | New API token from id.atlassian.com → update the Jira server's credentials |
| Tool returns 404 / "does not exist or you do not have permission" | Wrong key, or account lacks project access | Confirm the key/site, or grant Browse permission |
| Server "Failed to connect" (community `mcp-atlassian` npm package) | Missing peer dependency | Launch it as `npx -y -p mcp-atlassian -p jsdom mcp-atlassian` |

Alternatively, the user can paste the issue content. Label everything derived from a paste as "from user paste, not retrieved from Jira".

### 1c. Inspect the codebase
For each repo the issue plausibly touches: `git status -sb`, current branch, recent log; build files (`pom.xml`, `build.gradle`, `package.json` + lockfile); source tree; existing tests; env/config files; any existing code for this feature and existing APIs it can reuse. Reuse what exists and do not re-create it.

Watch for:
- **Git start state:** after a merge, local repos may still be on the old feature branch. Before branching, `git checkout main && git pull` in each repo touched (after the clean-tree check).
- **Agent defaults vs. project stack:** agent instructions mention common defaults (e.g. JPA/Flyway/PostgreSQL, JVM-focused QA). When the project differs (e.g. MongoDB with Spring Data MongoDB, Testcontainers `mongodb`), state the project's stack explicitly in every brief.

### 1d. Map the affected areas
List the affected backend modules/packages, frontend features, shared pieces, and any foundation the feature needs that doesn't exist yet (e.g. first database use, first route, theme, API client, test tooling).

## 2. Stage 2 — Requirements analysis (Product Owner)

Spawn the `po` agent in **analysis-only** mode. It runs without access to this conversation, so the brief must be self-contained:
- the full retrieved Jira content (parent, children, comments, links). Paste it so `po` does not refetch.
- relevant `PROJECT.md` sections (scope, domain, business rules, UI/UX, open decisions).
- "Do not create or modify Jira issues. Do not modify files. You cannot ask the user — return questions."
- SKILLS TO USE: `requirements-analysis`, `acceptance-criteria` (plus `user-story-writing` if the issue needs splitting).

Ask `po` to return:
- Problem statement and business value.
- In scope / out of scope (explicit, tied to Jira text or project docs).
- Functional and non-functional requirements with IDs and sources.
- Business rules that apply, with their references in the project docs.
- Acceptance criteria: the existing ones as written, plus **proposed missing ones** (Given/When/Then), clearly marked "proposed — not in Jira".
- Dependencies (Jira links, foundations, other stories).
- Ambiguities and contradictions (Jira vs. project docs vs. comments), each marked blocking or non-blocking, with a recommended default.
- Which open product decisions in the project docs this touches.

While `po` works, the main session does Stage 1c/1d and starts Stage 3. Review `po`'s output critically; it may only state facts that trace to a source.

## 3. Stage 3 — Architecture and design (you, the Architect)

Follow the architect's design phase. Load `system-design` / `api-design` / `database-design` only as needed. Produce a concise design containing:

1. **Approach**: how it fits the project's documented architecture (e.g. layered backend packages, feature-first frontend). No new architectural patterns, services or libraries beyond the project's stack without explicit approval.
2. **Affected files/modules**: a create/modify list per repo.
3. **API contract**: for each endpoint, method + path (with the project's versioning prefix), request params/body DTO, response DTO (field names and types), status codes, error format (stable error code + safe message), pagination/sorting parameters. This contract is binding on both backend and frontend.
4. **Data model**: tables/collections, fields, indexes, validation, migrations. Note backward compatibility, how existing data is handled, and whether seed/sample data is needed (and how it's loaded without committing secrets).
5. **Foundations required** (if any): the minimum setup this feature needs. **List every new dependency explicitly in the approval gate**, even inside the approved stack. Add only what this issue needs now.
6. **Security implications**: auth required or public? Data exposure, input validation, CORS, rate limits. Decide whether `security` review is required (rules in Stage 6).
7. **UI states**: for every data-driven screen, loading, success, empty (with a useful next action) and error (with recovery). Responsive breakpoints and accessibility notes.
8. **Edge cases**: inactive/missing records, empty collections, missing images, long names, pagination bounds, invalid IDs, backend down.
9. **Test plan**: backend unit + slice/integration (Testcontainers where the project uses it); frontend component tests; E2E only for critical journeys the project names. List AC → test mapping.
10. **Agent plan**: which agents, in what order, with file ownership (no two agents on the same files at once), and what runs in parallel.
11. **Branches**: `feature/<KEY>-<short-slug>` in each repo touched (or the project's branch convention).

If an open product decision blocks a correct design, it goes to the gate as a blocking question. Don't invent business rules.

## 4. Stage 4 — Approval gate (mandatory; no code before this)

Present one compact plan to the user and **stop**:

```
<KEY> — <summary>   (<type>, <status>, <priority>)
Scope: in / out
Acceptance criteria: from Jira (n) + proposed (m)
Blocking questions: (each with recommended default)
Design: API contract table · data model · UI states · edge cases
Files: per repo
New dependencies: name — why (or "none")
Branches: …
Agents: order and responsibilities
Tests: AC → test mapping; commands to run
Jira board: on approval po adds <KEY> to the active sprint, assigns it to the user, moves it → In Progress (and the parent epic → In Progress if it is still To Do); after verification → In Review; when merged → Done
Risks / spec conflicts noticed
```

**Epic or story with children:** show the children in dependency order and recommend a delivery slice. Default: one story at a time, starting with the one that establishes shared foundations. Ask whether to do the whole epic or a specific story.

Approving the plan also authorizes the board updates in §10 for the issues in the approved slice: sprint placement, assignment to the user, status changes, and moving the parent epic from To Do to In Progress. It does not cover other issues, comments, other fields, or moving the epic to Done.

Proceed only on an explicit go-ahead for this plan ("approved", "go", "implement it", or answers to the blocking questions plus a go). Silence or "looks interesting" is not approval. If the user changes the plan, update it. Re-present only if the change is material.

## 5. Stage 5 — Implementation

After approval:
0. **Jira → on the board, In Progress.** Spawn `po` with the start brief in §10 (active sprint + assign + `inprogress`, and the epic → `inprogress` if still To Do), in parallel with step 1. Don't wait for it before coding. Check its result before the final report.
1. In each repo touched: check the tree is clean (if it isn't, show the user and ask), `git checkout main && git pull`, then create the feature branch from `main`. **No commits, pushes or PRs unless the user asks.**
2. **Contract first.** The approved API contract goes verbatim into both the `backend` and `frontend` briefs.
3. **Backend** (`backend` agent), when backend work exists. Brief per the architect's template, including:
   - PROJECT: absolute repo path, stack and versions, base package, database technology, all from the project facts.
   - Rules: the project's architecture and code conventions. **Copy the backend agent's "Mandatory code conventions" and any project-specific conventions into the brief verbatim.** Controllers → services → repositories; DTOs never expose entities/documents; Bean Validation at the boundary; consistent error responses (e.g. `@RestControllerAdvice` + ProblemDetail with stable codes); server-side business rules and authorization; configuration per the project's convention; document new variables in the README; OpenAPI annotations if springdoc is present.
   - Tests: unit tests for services; controller slice tests; Testcontainers for repository/integration tests (report honestly if Docker is unavailable).
   - VERIFICATION: the project's backend command (e.g. `./mvnw -q verify`, `./gradlew build`).
   - SKILLS TO USE: `spring-boot-development`, `api-design`, `database-design` (only those relevant).
4. **Frontend** (`frontend` agent), when frontend work exists. It can run **in parallel with backend** once the contract is fixed, coding against the contract and mocking at the service/hook layer in tests.
   - PROJECT: absolute repo path, framework, build tool, linter, package manager, from the project facts.
   - Rules: the project's frontend structure (e.g. feature-first `src/app`, `src/shared`, `src/features/<feature>`) and styling approach (Styled Components, never Tailwind, unless the project says otherwise); server state via the project's data library; one API client; loading/empty/error/success states; responsive; accessible (semantic HTML, keyboard, focus, contrast, alt text); no fake controls. It writes component tests for its own code.
   - "You were delegated: do not delegate further."
   - VERIFICATION: the project's frontend commands (e.g. `npm run lint`, `npm run build`, `npx vitest run`).
   - SKILLS TO USE: `react-development`, `frontend-architecture`, `frontend-state-forms` (only those relevant).
5. **DevOps** (`devops` agent), only if the issue needs Docker/Compose, CI, deployment or env wiring changes. Never deploy; report the commands instead.
   - **Test-data sync:** when the change adds or changes seed/test data and the project's instructions ask for hosted copies (with a standing approval, or the user approves it now), spawn `devops` after the backend work is verified to follow "Test-data sync to a hosted database" in its instructions. Quote the approval in the brief. Include its before/after counts in the final report.
6. Read every report. Spot-check diffs (`git diff --stat`, key files) against the contract and design. Route deviations back to the same agent via `SendMessage`.

Small changes (a single file, a few lines) can be done directly by the Architect instead of delegating.

## 6. Stage 6 — Security review (conditional)

Spawn `security` (read-only) when the change touches any of: authentication/authorization, roles/admin endpoints, personal data, payments, secrets/config, file uploads, CORS/security headers, new public write endpoints, or new dependencies with network exposure. For public read-only pages, a short self-review by the Architect is enough. Record which applied.

Give it the diff scope (files, endpoints) and the project's security rules. Blocking findings go back to the owning engineer; re-review the fix.

## 7. Stage 7 — QA

Spawn `qa`:
- **Backend**: `implement` mode, scoped to the backend test directories. Derive tests from the acceptance criteria and risks: positive, negative, validation, 4xx/5xx, pagination bounds, empty data, inactive items, and authorization where relevant.
- **Frontend**: if `qa`'s scope is JVM-focused, use `review-only`: it reviews the frontend agent's tests against the ACs and runs the frontend test/build commands; missing frontend tests go back to `frontend`. Browser E2E is added only for critical journeys and only if approved in the plan; QA may then write the E2E directory listed in its brief.
- QA reports defects with reproduction and `file:line`. It never fixes production code; the owning agent does, then QA re-runs.

## 8. Stage 8 — Verification (you, personally)

- Run the project's verification commands yourself and read the output. Never relay a subagent's "passing".
- Walk every acceptance criterion: met, partially met, or not met, with evidence (test name, file, or manual check).
- If practical, run the app and exercise the main flow. Say whether this was done.
- Confirm: no secrets or `.env` values in the diff (e.g. `git diff | grep -iE 'mongodb\+srv|password|secret|token'`), no unrelated changes, docs and config updated where needed.
- Failures: fix via the owning agent, or report them plainly. Never weaken or delete tests to pass.

## 9. Stage 9 — Final report and Jira

If Stage 8 passed, first spawn `po` to move `<KEY>` → `review` (§10) and wait for its result.

Report (plus anything the project's `CLAUDE.md` requires):
1. Jira key, title, link; scope delivered vs. planned.
2. Acceptance criteria checklist with evidence.
3. Architecture decisions (and any disagreements resolved).
4. Files changed, per repo and per agent.
5. API and database changes.
6. **Agents actually invoked** (name + stage). Say that the Architect role was performed by the main session. Agents not invoked: say why.
7. Exact commands run, with real results (pass/fail counts).
8. Limitations, follow-ups, spec conflicts, and open product decisions.
9. Git state: branch names, uncommitted. Offer to commit/open a PR. Do not do it unasked.
10. Jira board: each sprint, assignment and status change `po` reported, quoting its output (`'In Progress' -> 'In Review' (verified)`), or the failure.

**Other Jira writes:** apart from the §10 board updates, do not change comments, assignee or fields, or the status or sprint of any issue outside the approved slice, unless the user explicitly authorizes that specific change in this conversation. If authorized to comment, add a short delivery summary (no secrets, no internal paths beyond repo-relative).

## 10. Jira board and status lifecycle (owned by `po`)

The `po` agent owns the board: sprint placement, assignee and status. The Architect never runs these itself; it spawns `po` with a short brief. Many Jira MCP servers have no transition, sprint or assign tools, so `po` uses MCP tools if present, otherwise the `jira-backlog-management` skill's scripts (`scripts/jira_transition.py` for status, `scripts/jira_board.py` for sprints and assignees).

A Scrum board shows only issues in the **active sprint**. A story left in the backlog never appears on the board, whatever its status. So every story that starts work goes into the active sprint first.

| When | Move | Condition |
|---|---|---|
| Stage 4 approval given | add to active sprint, assign to the user (`--to me`), → `In Progress`; parent epic → `In Progress` | Story: skip steps already done. Epic: only if it is still `To Do`; epics are never added to a sprint |
| Stage 8 verification passes | → `In Review` | All checks green, ACs met. If anything failed or is partial, leave it in `In Progress` and say why |
| Feature branch merged into `main` (user says so, or `gh pr view <n> --json state` shows `MERGED` in every touched repo) | → `Done` | Only after a real merge. Never on "code complete" or an open PR. If the work spans several repos, every PR must be merged |
| Work abandoned / rolled back | → `To Do` | Only when the user asks |

**Status brief for `po`** (self-contained, one per transition, may cover several keys):
```
TASK: Jira status update — write already approved by the user (approval of <KEY> plan: "<quote>").
Move <KEY>[, <KEY>…] → <todo|inprogress|review|done>.
Reason: <approval given | verification passed: <summary> | merged: <PR URL(s)>>.
SKILLS TO USE: jira-backlog-management (sections 6 and 7).
Steps (scripts in that skill's scripts/ folder):
- start of work only: `python3 jira_board.py add-to-sprint <KEYS> --project <PROJECT>`, then `python3 jira_board.py assign <KEYS> --to me`, then, if the parent epic is `To Do`, `python3 jira_transition.py move <EPIC> inprogress`.
- every time: `python3 jira_transition.py status <KEYS>`, then `move <KEYS> <target>`; finish with `python3 jira_board.py board <PROJECT>`.
For `done`: also run `python3 jira_transition.py status` on the parent's other children (from the parent's issue data, or JQL `parent = <PARENT>` if search works) and report whether all are Done.
Do nothing else in Jira: no comments, other fields, or other issues; the parent epic only as listed above. Return each script's exact output and exit code.
```

- **Parent epic:** moving a story never moves its epic. When `po` reports that every child of the epic is `Done`, the Architect asks the user whether to move the epic to `Done`.
- **Failure:** if `po` reports a failed transition (exit code 2, no matching transition, 401/403), report it with the error and tell the user what to fix. Never claim a status that `po` did not verify.
- **Merge happens later:** if the session ends before the merge, the final report says `<KEY>` is `In Review` and will move to `Done` once merged. When the user later says it's merged (e.g. "PROJ-14 merged"), run only the `Done` step and don't restart the workflow.

## Non-negotiables

- Never claim Jira content, agent runs, test results or builds that did not happen.
- No code before the Stage 4 approval.
- Implement only the approved scope. Unrelated issues get reported, not fixed.
- Don't invent business rules (currency, taxonomy, pricing, shipping, payment, returns). Ask.
- No new libraries, services or patterns beyond the project's stack without approval. Inside the stack, still list them at the gate.
- Secrets only via env vars; never commit `.env`, URIs, tokens or keys; never print the Jira token.
- No deploy, push, PR or destructive DB operation without explicit approval.
- One owner per file at a time across agents.
