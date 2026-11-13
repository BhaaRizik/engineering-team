---
name: devops-cicd
description: Reliable, repeatable build and deployment workflows — Dockerfiles and Docker Compose, GitHub Actions CI/CD pipelines, automated test stages, artifact and image versioning, deployment strategies (rolling, blue-green, canary), environment configuration and secrets management, Railway and AWS (including S3) deployment basics, health checks, logging/monitoring infrastructure, rollbacks, and production troubleshooting. Use when containerizing an app, creating or fixing CI/CD workflows, configuring environments or secrets, planning a deployment or rollback, or investigating production incidents. Provider-neutral unless the project uses a specific cloud.
---

# DevOps & CI/CD

## Purpose
Help `devops` build pipelines and deployments that are reproducible, secure, observable, and reversible. Application-level health/metrics/tracing are in `backend-resilience-observability`; secret-handling rules in `application-security`.

## When to use
- Writing or reviewing Dockerfiles / Compose files.
- Creating or debugging GitHub Actions workflows.
- Setting up environments (dev/staging/prod), configuration, and secrets.
- Planning a deployment, migration rollout, or rollback.
- Troubleshooting a production issue.

## Core principles
1. **Build once, deploy many.** The same immutable artifact/image (tagged by commit SHA) moves through environments; only configuration differs.
2. **Everything as code**: pipelines, infrastructure, configuration templates — reviewed and versioned.
3. **Fast, reliable feedback**: CI on every PR; fail fast; cache dependencies.
4. **Safe by default**: least-privilege credentials, no secrets in images/logs, production changes gated by approval.
5. **Every deploy is reversible**: rollback path known and tested before you need it; database migrations backward compatible.
6. **Don't assume a provider.** Detect what the project uses (Railway, AWS, other) and follow it.

## Best practices

### Docker
- Multi-stage builds: build stage (JDK/Node) → runtime stage (JRE/distroless/nginx or Node slim).
- Pin base images by version (and digest for strict reproducibility); update via Dependabot/Renovate.
- Run as non-root; read-only filesystem where possible; no secrets in `ENV`/`ARG`/layers (use BuildKit `--mount=type=secret` for build-time secrets).
- `.dockerignore` excludes `.git`, `node_modules`, `target`, `.env`.
- Order layers for caching (dependencies before sources). Spring Boot: layered jars / `spring-boot:build-image` (Buildpacks) are good alternatives to hand-written Dockerfiles.
- JVM in containers: rely on container-aware defaults; set `-XX:MaxRAMPercentage` rather than fixed `-Xmx`.
- `HEALTHCHECK` in Dockerfile is optional when the orchestrator probes health; never point it at endpoints requiring auth.
- Frontend: build static assets, serve via CDN/object storage or a minimal web server; runtime config via a small config endpoint/file if values differ per environment (build-time `VITE_*` values are baked in and public).

### Docker Compose
- For local development and integration environments (app + Postgres/Mongo + Redis + broker).
- Healthchecks + `depends_on: condition: service_healthy`; named volumes; `.env` for local values only (`.env.example` committed).
- `docker compose down -v` deletes data — requires explicit confirmation.

### GitHub Actions
- Workflow per concern: `ci.yml` (PR + main), `deploy.yml` (main/tags, environments).
- `permissions:` least privilege at workflow/job level (default `contents: read`).
- Pin third-party actions to a full commit SHA (or at least major version for official `actions/*`); review new actions.
- Cache: `actions/setup-java` with `cache: maven|gradle`, `actions/setup-node` with `cache: npm|pnpm`.
- Concurrency groups to cancel superseded runs: `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` (not for production deploy jobs).
- Use **environments** with required reviewers for production; secrets scoped to environments.
- Cloud auth via OIDC (`aws-actions/configure-aws-credentials` with role-to-assume) instead of long-lived keys.
- Never echo secrets; avoid `pull_request_target` with checkout of untrusted code.
- Lint workflows with `actionlint` when available.

### Pipeline stages (reference)
```text
PR:    lint/typecheck → unit tests → integration tests (Testcontainers) → build → (image build, no push) → security scans
main:  all of the above → push image :sha → deploy staging → smoke/E2E → [manual approval] → deploy prod → post-deploy smoke → notify
```

### Deployment strategies
| Strategy | How | Use when | Rollback |
|---|---|---|---|
| **Rolling** | Replace instances gradually | Default for stateless services | Redeploy previous image |
| **Blue-green** | Two environments, switch traffic | Need instant switch/rollback | Switch back |
| **Canary** | Small % traffic to new version, watch metrics | High-traffic, risky changes | Route 100% back |
| **Feature flags** | Deploy dark, release by toggle | Decouple deploy from release | Toggle off |

Database migrations: expand/contract (see `database-design`); app version N and N+1 must both work with the schema during rollout. Run migrations as a dedicated step or on startup with locking (Flyway does this), never manual SQL in prod.

### Environment configuration & secrets
- 12-factor: config via environment variables; same image across environments.
- Secrets in the platform's secret store (GitHub Environments secrets, Railway variables, AWS Secrets Manager/SSM Parameter Store); rotate; audit access.
- Validate required configuration at startup (fail fast with clear error, without printing values).

### Provider notes
**Railway**: services from repo or image; variables per environment (reference variables between services); healthcheck path configured per service; deploy via GitHub integration or `railway up` — **production deploys only with explicit user approval**. Use managed Postgres/Redis plugins or external services; know the rollback (redeploy previous deployment).
**AWS** (typical container setup): ECR for images; ECS Fargate (or App Runner/EKS if the project uses it); ALB health checks to readiness endpoint; RDS for Postgres; Secrets Manager/SSM for config; CloudWatch logs/metrics; IAM roles per task with least privilege; IaC (Terraform/CDK/CloudFormation) as the project uses.
**S3**: Block Public Access on; bucket policies least privilege; encryption (SSE-S3/SSE-KMS); versioning + lifecycle rules for important data; pre-signed URLs for uploads/downloads; CloudFront (OAC) for public static assets instead of public buckets.

### Logging & monitoring infrastructure
- Ship structured logs from stdout to the platform's log system; retention policies set.
- Scrape/export metrics (Prometheus/OTLP) and traces (OTLP → collector); dashboards for RED + resource saturation; alerts tied to SLOs with runbooks.

### Rollbacks & troubleshooting
- Before deploy: know the previous good version, rollback command, and migration compatibility.
- Rollback triggers: failed health checks, error-rate/latency SLO burn, failed smoke tests.
- Troubleshooting order: (1) what changed (deploys, config, traffic, dependencies), (2) symptoms in metrics, (3) traces for slow/failing paths, (4) logs by trace ID, (5) mitigate first (rollback, scale, feature flag), (6) root cause after stabilization, (7) blameless postmortem with action items.
- Read-only investigation in production by default; any mutating action (restart, scale, rollback, data fix) requires user approval.

## Implementation workflow
1. Inspect existing Dockerfiles, Compose, workflows, IaC, and deployment setup — never overwrite blindly.
2. Define pipeline stages and environments; identify secrets and how they're provided.
3. Implement minimal, explained changes (Docker → CI → deploy).
4. Validate locally: `docker build`, `docker compose config`, `actionlint`, dry runs/plans (`terraform plan`).
5. Document deploy and rollback procedure.
6. Report pending actions that require approval (exact commands, environment, impact).

## Decision-making guidelines
- **Buildpacks vs. Dockerfile**: Buildpacks for standard Spring apps with little customization; Dockerfile for custom runtime needs.
- **Railway vs. AWS**: Railway for simplicity and small teams; AWS for compliance, network control, scale, or existing org standards — follow the project.
- **Rolling vs. blue-green/canary**: rolling by default; canary/blue-green for high-risk or high-traffic releases with good metrics.
- **Monorepo CI**: path filters so only affected apps build/test.

## Anti-patterns
- Rebuilding images per environment; `latest` tags in deployments.
- Secrets in Dockerfiles, repo, workflow logs, or frontend build vars.
- Long-lived cloud keys in CI when OIDC is available.
- Deploying to prod on every push without gates or smoke tests.
- Destructive migrations shipped with the code that stops using the column.
- Manual, undocumented production changes ("click-ops").
- Liveness checks depending on the database causing restart storms.
- Overwriting existing pipeline/infra config without reading it.

## Quality checklist
- [ ] Image is multi-stage, pinned, non-root, minimal, no secrets.
- [ ] CI runs lint, tests, build on PRs with caching and least-privilege permissions.
- [ ] Same artifact promoted across environments; tagged by commit SHA.
- [ ] Secrets in a secret store; OIDC for cloud auth where possible.
- [ ] Production deploy gated by approval; smoke tests after deploy.
- [ ] Health checks wired to readiness; logs/metrics/traces flowing.
- [ ] Rollback path documented and migration-compatible.
- [ ] Validation commands executed and results reported.

## Examples
```dockerfile
# syntax=docker/dockerfile:1
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN ./mvnw -q dependency:go-offline
COPY src/ src/
RUN ./mvnw -q -DskipTests package

FROM eclipse-temurin:25-jre
RUN useradd --system --uid 10001 app
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
USER 10001
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
```
```yaml
# .github/workflows/ci.yml
name: CI
on: { pull_request: {}, push: { branches: [main] } }
permissions: { contents: read }
concurrency: { group: "${{ github.workflow }}-${{ github.ref }}", cancel-in-progress: true }
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '25', cache: maven }
      - run: ./mvnw -B verify
  frontend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - run: npm ci
      - run: npm run lint && npm run typecheck && npm test -- --run && npm run build
```
(Adjust action versions, Java/Node versions, and paths to the project; verify current major versions of actions.)

## References
- Docker build best practices: https://docs.docker.com/build/building/best-practices/
- Docker Compose: https://docs.docker.com/compose/
- Spring Boot container images: https://docs.spring.io/spring-boot/reference/packaging/container-images/index.html
- GitHub Actions: https://docs.github.com/en/actions
- GitHub Actions security hardening: https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- GitHub Actions OIDC with AWS: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- actionlint: https://github.com/rhysd/actionlint
- Railway docs: https://docs.railway.com/
- AWS ECS best practices: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-best-practices.html
- Amazon S3 security best practices: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html
- The Twelve-Factor App: https://12factor.net/
- Google SRE book — Release engineering: https://sre.google/sre-book/release-engineering/
