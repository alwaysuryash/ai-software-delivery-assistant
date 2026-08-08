# PROJECT_STATUS.md — AI Software Delivery Assistant

> **Source of truth.** Every working session must append a dated changelog entry here.
> This file tracks phase progress against the BRD (v1.0, 19-Jul-2026) build plan (Sections 18, 24).

---

## 1. Product

AI-native, multi-agent Software Delivery Intelligence Platform. Monitors software delivery,
gathers evidence from enterprise tools, analyzes project health with specialized agents,
detects risks, prepares evidence-backed reports, and keeps a human in control before any write.

**Golden rules (never violate):**
- No claim without retrieved evidence or an explicit `inference` label (BR-01).
- No source access without project + user authorization (BR-02).
- No write without an approval record bound to the exact payload hash (BR-03).
- Health is `unknown` when minimum data is missing — never guess (BR-04).
- LLM never assigns the final health score; deterministic engine does (§12).
- Never expose chain-of-thought; expose concise rationale + evidence only.

## 2. Locked Technology Decisions (ADR-0001)

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router) + React + TypeScript + Tailwind |
| Backend | Python 3.12+ + FastAPI (async) |
| Orchestration | LangGraph (explicit state graph) |
| AI Platform | Azure OpenAI / AI Foundry via `ModelProvider` abstraction (fake provider offline) |
| DB | PostgreSQL + SQLAlchemy 2.0 (async) + Alembic |
| Cache / State | Redis |
| RAG / Search | pgvector behind `RetrievalProvider` (Azure AI Search adapter later) |
| Secrets | `SecretProvider` (env default → Azure Key Vault adapter) |
| Observability | OpenTelemetry + structlog |
| Tool layer | Permission-aware connector gateway; mock connectors first |

## 3. Phase Progress (BRD §18)

| Phase | Title | Status |
|---|---|---|
| 0 | Foundation & Decisions | ✅ Done |
| 1 | Application Skeleton | 🟡 Backend done + verified; frontend scaffolded (pnpm install/build pending) |
| 2 | Read Connectors & Evidence | ⬜ Not started |
| 3 | Deterministic Metrics & Health | ⬜ Not started |
| 4 | Single-Agent MVP | ⬜ Not started |
| 5 | Multi-Agent Specialization | ⬜ Not started |
| 6 | Evaluation & Quality Gates | ⬜ Not started |
| 7 | Human Approval & Write Actions | ⬜ Not started |
| 8 | Pilot & Production Hardening | ⬜ Not started |

Legend: ⬜ not started · 🟡 in progress · ✅ done

## 4. Requirements Traceability (high level)

Detailed matrix: [docs/traceability-matrix.md](docs/traceability-matrix.md) (maintained from Phase 1).

## 5. Changelog

### 2026-07-20 — Phase 0 kickoff
- Repo initialized (`git`, `main` branch).
- Locked technology stack (ADR-0001): Python/FastAPI + LangGraph, Next.js frontend,
  Azure OpenAI behind a `ModelProvider` abstraction, PostgreSQL/pgvector, Redis, OpenTelemetry.
- Authored Phase 0 deliverables: solution architecture, ADR-0001, threat model,
  data classification, approval policy, health-model config, coding standards.
- Defined MVP tool set + pilot project (`docs/decisions/phase-0-foundations.md`).
- Added `docker-compose.yml` (Postgres + Redis), `.env.example`, `.gitignore`.
### 2026-07-20 — Phase 1 skeleton (backend verified)
- **Backend (FastAPI) — done & tested (12/12 pytest passing on Python 3.14):**
  - Core: `config` (env-driven, provider selectors), `correlation` IDs (NFR-05),
    `logging` (structlog JSON + secret scrubbing), `errors` (typed hierarchy + handlers),
    `feature_flags` (per connector/project/agent/model kill switches — §16), `security` (JWT +
    dev/Entra provider abstraction — FR-001).
  - Domain: `enums`, `rbac` capability matrix (FR-002, §7), `contracts` (mandatory Agent
    Response schema §10.1, `EvidenceRef` with min-1 citation — FR-011/BR-01).
  - Persistence: full **Minimum Data Model (§15)** as SQLAlchemy models (14 entities incl.
    append-only `AuditEvent`); async session; Alembic scaffold (autogenerate) + create_all bootstrap.
  - Application services: `AuditService` (FR-021), `AccessService` (BR-02/US-05 project isolation).
  - API: correlation+logging middleware, `healthz`/`readyz`, `auth` (dev-login+me),
    `projects` (access-scoped listing; uniform 404 for unauthorized).
  - **Connectors:** replaceable ports (WorkItem/Repository/Pipeline/Test/Document) + registry
    (mock/live seam) + **mock connectors** with deterministic "Project Alpha" sample data
    (blocked work, aged PR, failed main build, unexecuted critical suite, release-blocking defect,
    unavailable env — realistic amber/red signals). Normalized evidence DTOs with provenance.
  - Seed script (users across all 6 roles, Project Alpha, access grants, connector rows).
  - Tests: `test_rbac`, `test_connectors`, `test_api` (auth, access isolation, correlation header).
- **Frontend (Next.js App Router) — scaffolded:** login (dev SSO), access-scoped project selector,
  assistant workspace shell (question input, period, health/approvals panes), typed API client,
  react-query providers, Tailwind health palette. `pnpm install`/`build` not yet run.
- Added `docs/traceability-matrix.md`.
- **Next:** finish Phase 1 (frontend `pnpm install` + build/typecheck verify; wire Entra later),
  then **Phase 2** — real read connectors + evidence normalization + resilience + contract tests.
