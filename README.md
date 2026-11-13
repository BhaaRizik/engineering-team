# Engineering Team — Claude Code plugin

`bhaa-engineering-team` is a reusable multi-agent software engineering team for [Claude Code](https://docs.claude.com/en/docs/claude-code/overview). It packages a Product Owner, Software Architect, and Backend, Frontend, Security, QA, and DevOps specialists, plus a library of 21 engineering skills they load on demand. You talk to one primary agent (usually the architect or the PO); it plans the work, delegates to specialists, reviews their results, and reports back with evidence.

The plugin contains instructions only: no code, no credentials, no MCP server configuration.

## What the team does

- **Turns requirements into a backlog.** The PO analyzes requirement documents, asks clarification questions, and prepares epics, user stories, and acceptance criteria. It creates Jira issues only after your explicit approval.
- **Designs and builds software.** The architect designs the solution, defines API contracts, and delegates implementation to the backend (Java/Spring Boot) and frontend (React/TypeScript) engineers.
- **Reviews and tests.** The security engineer reviews security-sensitive work read-only. The QA engineer derives test cases from requirements and risks and writes automated tests.
- **Ships it.** The DevOps engineer handles Docker, CI/CD, environments, and observability. It never deploys to production without your approval.

## Agents

| Agent | Role | Responsibilities | Can delegate to |
|---|---|---|---|
| `po` | Senior Product Owner & Business Analyst | Requirements analysis, clarification questions, epics/stories/acceptance criteria, prioritization, approval-gated Jira backlog creation. Never writes code. | Read-only consultation with the architect and specialists |
| `architect` | Software Architect & coordinator | Requirements → architecture → delegation → QA → final verified review. Owns API contracts and technical decisions. | `po`, `backend`, `frontend`, `security`, `qa`, `devops` |
| `backend` | Java Spring Backend Engineer | Spring Boot APIs, business logic, persistence and migrations, backend performance | — |
| `frontend` | Senior Frontend Engineer & React Architect | React + TypeScript, feature-first architecture, Styled Components (no Tailwind), TanStack Query, forms, accessibility | `backend`, `security`, `qa`, `devops` (when run as the primary agent) |
| `security` | Security Engineer (read-only reviewer) | Auth/authz design and review, OWASP, secrets, dependency vulnerabilities | — |
| `qa` | QA Engineer | Test strategy, unit/integration/API/E2E tests (writes test code only) | — |
| `devops` | DevOps Engineer | Docker, GitHub Actions, Railway/AWS, environments, observability, rollbacks | — |

Subagents can't start other subagents in Claude Code, so delegation is one level deep. Specialists return reports to the coordinator, who relays decisions between them.

## Skills

Agents load skills with Claude Code's Skill tool only when a task needs them.

| Skill | Purpose | Used by |
|---|---|---|
| `system-design` | Architecture styles, DDD, modular monoliths, ADRs | architect, backend |
| `design-patterns` | When (not) to apply GoF/enterprise patterns | architect, backend |
| `api-design` | REST conventions, RFC 9457 errors, pagination, versioning, OpenAPI | architect, backend, frontend, security, qa |
| `database-design` | PostgreSQL/MongoDB modeling, indexing, migrations | architect, backend |
| `engineering-code-review` | Severity-ranked code review method | architect, frontend |
| `spring-boot-development` | Version-aware Java/Spring Boot practice | backend |
| `backend-resilience-observability` | Timeouts, retries, circuit breakers, metrics, tracing, logging | backend, devops |
| `react-development` | React + TypeScript components, styling, accessibility, performance | frontend |
| `frontend-architecture` | Feature-first folder structure and boundaries | frontend |
| `frontend-state-forms` | Server vs. client state, TanStack Query, Zustand/RTK, React Hook Form + Zod | frontend |
| `application-security` | Secure-coding defaults (OWASP, JWT/OAuth2, CSRF/CORS, secrets) | security, devops |
| `engineering-security-review` | Threat modeling and structured security review process | security |
| `testing-strategy` | What to test at which level, and why | backend, qa |
| `test-automation` | JUnit, Testcontainers, WireMock, Vitest, RTL, MSW, Playwright | qa |
| `devops-cicd` | Docker, GitHub Actions, deployments, rollbacks, troubleshooting | devops |
| `product-management` | Vision, MVP scope, decision log, stakeholder communication | po |
| `requirements-analysis` | Extracting and classifying requirements; clarification questions | po |
| `user-story-writing` | Epic/story/task decomposition and story template | po |
| `acceptance-criteria` | Testable Given/When/Then criteria | po |
| `backlog-prioritization` | Priorities, MVP vs. future, dependencies, honest estimates | po |
| `jira-backlog-management` | Approval-gated Jira discovery, creation, and verification | po |

The two review skills are named `engineering-code-review` and `engineering-security-review` so they stay separate from Claude Code's built-in `/code-review` and `/security-review` commands.

## Plugin architecture

```text
engineering-team/
├── .claude-plugin/
│   ├── plugin.json          # plugin manifest (name: bhaa-engineering-team)
│   └── marketplace.json     # marketplace catalog (name: engineering-team), source "./"
├── agents/                  # 7 subagent definitions (auto-discovered)
├── skills/<name>/SKILL.md   # 21 skills (auto-discovered)
├── README.md
└── LICENSE
```

- The repository is both a **marketplace** (`engineering-team`) and the **plugin** it lists (`bhaa-engineering-team`).
- Claude Code namespaces plugin components: agents are invoked as `bhaa-engineering-team:<agent>` and skills as `bhaa-engineering-team:<skill>`. Each agent file includes a short "Plugin naming" note so it uses the namespaced names, and the `Agent(...)` restrictions in `architect.md` and `frontend.md` list the namespaced specialists.
- Each agent's instructions name the skills it should use (the skill map is also in `architect.md`). Skills are not copied into the agents.
- Safety rules live in the agent instructions. These include approval before production deploys, destructive database operations, and Jira issue creation, and the read-only security reviewer. For stricter enforcement, add `permissions.ask` rules to your own `~/.claude/settings.json` (for example `"Bash(git push:*)"`, `"Bash(terraform apply:*)"`). The plugin doesn't ship settings.

## Installation

Requires Claude Code with plugin support. Check your version with `claude --version` and update if needed.

### For the repository owner

```bash
claude plugin marketplace add BhaaRizik/engineering-team
claude plugin install bhaa-engineering-team@engineering-team
```

If you also keep un-namespaced copies of these agents in `~/.claude/agents/` and `~/.claude/skills/`, both sets will appear. `claude --agent architect` runs your personal copy, and `claude --agent bhaa-engineering-team:architect` runs the plugin version. To use only the plugin, move your personal copies out of those folders.

### For another developer

The repository is public, so no access grant is needed. From a terminal:

```bash
claude plugin marketplace add BhaaRizik/engineering-team
claude plugin install bhaa-engineering-team@engineering-team
```

Or inside a Claude Code session:

```text
/plugin marketplace add BhaaRizik/engineering-team
/plugin install bhaa-engineering-team@engineering-team
```

Restart Claude Code after installing.

### Start the team

```bash
cd your-project
claude --agent bhaa-engineering-team:architect   # primary coordinator for engineering work
claude --agent bhaa-engineering-team:po          # requirements → backlog → (approved) Jira
```

To make the architect the default for every session, add `"agent": "bhaa-engineering-team:architect"` to `~/.claude/settings.json`.

Example request that engages several specialists:

> Add JWT login with refresh tokens to the orders API, a React login page, Testcontainers integration tests, and a GitHub Actions workflow that runs them.

### Jira (optional, for the PO)

The PO works without Jira. It stops at an approved, ready-to-create backlog. To let it create issues, connect a Jira integration yourself, for example Atlassian's remote MCP server (`claude mcp add --transport http atlassian <URL from Atlassian's MCP documentation>`, then authenticate with `/mcp`) or a Jira connector in your claude.ai account. Credentials stay in your local Claude Code configuration, never in this repository.

## Updating

**Users** pull the latest version:

```bash
claude plugin marketplace update engineering-team
claude plugin update bhaa-engineering-team@engineering-team
```

Restart Claude Code to apply.

**Maintainers** publish a new version:

1. Edit agents or skills in this repository.
2. Bump `version` in `.claude-plugin/plugin.json` **and** the plugin entry in `.claude-plugin/marketplace.json` (semver: patch for wording fixes, minor for new skills/agents, major for renamed or removed components).
3. Validate: `claude plugin validate .`
4. Test locally without installing: `claude --plugin-dir . --agent bhaa-engineering-team:architect`
5. Commit and push to `main`.

## Contributing

### Add a skill

1. Create `skills/<skill-name>/SKILL.md` with frontmatter:
   ```markdown
   ---
   name: <skill-name>
   description: <what it covers and when to use it, specific enough for automatic selection>
   ---
   ```
   Use lowercase kebab-case names that don't clash with built-in commands, and match the directory name. Follow the existing structure: Purpose, When to use, Core principles, Best practices, Implementation workflow, Decision-making guidelines, Anti-patterns, Quality checklist, Examples, References. Reference related skills instead of duplicating their content.
2. Update the mappings:
   - Add the skill to the **Skills** section of each agent that should use it (`agents/<agent>.md`), with a one-line "use when".
   - Add it to the **Specialist skill map** table in `agents/architect.md`.
   - Add a row to the Skills table in this README.
3. Validate and test (see Updating), then bump the minor version.

### Add an agent

1. Create `agents/<agent-name>.md` with frontmatter `name`, `description` (a specific "use for…" so delegation works), and `tools` (least privilege), plus `model: inherit` if you want it to follow the session model.
2. Add the "Plugin naming" note (copy it from an existing agent), a Skills section, the collaboration rules, and a report format.
3. Register it in `agents/architect.md`: add it to the `Agent(...)` list in `tools` as `bhaa-engineering-team:<agent-name>`, add a row to the routing table and the skill map, and update the overlap rules.
4. Update this README, validate, test, and bump the minor version.

### Rules for contributions

- Instructions only. Never commit API keys, tokens, passwords, `.env` files, personal settings, or MCP configurations.
- Keep everything project-neutral and reusable.
- Never weaken the approval gates (production deploys, destructive data operations, Jira creation).

## License

[MIT](LICENSE)
