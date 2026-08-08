# Solution Architecture — AI Software Delivery Assistant

Status: Draft for Build · Aligns with BRD §14 (Target Solution Architecture).

## 1. Logical components (BRD §14)

| Component | Responsibility | Module |
|---|---|---|
| Web UI | Project selector, chat, health dashboard, evidence drawer, report editor, approval panel, feedback | `frontend/` |
| Application API | AuthN/Z, project config, report mgmt, approval workflow | `backend/app/api` |
| Agent Orchestrator | Task planning, agent invocation, state, conflict resolution, assembly | `backend/app/agents/orchestrator` |
| Specialist Agents | BA, Development, QA, DevOps, PM | `backend/app/agents/specialists` |
| Tool Gateway | Permission-aware, schema-validated, audited connectors | `backend/app/connectors` |
| Retrieval Layer | Ingestion, chunking, metadata filter, hybrid search, citations | `backend/app/infrastructure/retrieval` |
| Rules & Scoring Engine | Deterministic metrics, thresholds, health, policy checks | `backend/app/scoring` |
| Evaluation Layer | Groundedness, completeness, contradiction, safety, freshness, format | `backend/app/evaluation` |
| Data Stores | App DB, vector index, agent state, approved memory, audit log | PostgreSQL + pgvector + Redis |
| Observability | Logs, traces, metrics, token/cost, model/tool performance | OpenTelemetry + structlog |

## 2. Backend structure (Domain-Driven Design)

```
backend/app/
  core/            Cross-cutting: config, logging, correlation, errors, security, feature flags
  domain/          Entities, value objects, enums, domain services (pure, no I/O)
  application/     Use cases / services orchestrating domain + ports (interfaces)
  infrastructure/  Adapters: db (SQLAlchemy), retrieval, model providers, secrets, cache
  connectors/      Tool gateway + connector implementations (mock + real), evidence normalization
  scoring/         Deterministic metrics + weighted health engine
  agents/          LangGraph orchestrator + specialist agents + prompts (versioned)
  evaluation/      Evaluators + gold dataset runner
  api/             FastAPI routers, dependencies, schemas (DTOs), middleware
  main.py          App factory + wiring
```

**Ports & Adapters (Hexagonal).** The domain and application layers depend on *ports*
(abstract interfaces): `ModelProvider`, `RetrievalProvider`, `SecretProvider`, `Connector`,
`UnitOfWork`/repositories. Infrastructure supplies adapters. This satisfies NFR-12 (portability)
and the rule "every connector must be replaceable / every model must be configurable".

## 3. Request flow — Daily Project Health (BRD §8)

1. Authenticate user (SSO) → verify project access (RBAC).
2. Load project config, reporting period, sprint dates, connectors.
3. Orchestrator builds a task plan → delegates to BA/Dev/QA/DevOps/PM.
4. Each agent retrieves **minimum** evidence via authorized tools only.
5. Agents return structured JSON findings (§10.1 schema) with evidence refs + timestamps + confidence + data gaps.
6. Orchestrator reconciles contradictions, de-duplicates.
7. **Deterministic scoring engine** computes dimension + overall health (LLM does not score).
8. Evaluation layer checks grounding, freshness, completeness, policy, unsupported claims.
9. UI shows draft report: health, progress, risks, blockers, actions, decisions, evidence.
10. User edits/approves. Any write requires explicit approval bound to a payload hash + audit.

## 4. Determinism & control

- LangGraph state graph with **max steps** and **deterministic routing** — no open agent loops.
- Per-agent **tool allowlist**, **max tool calls**, **execution timeout**.
- Retrieved content is **untrusted data**, never instructions (prompt-injection defense).
- Model output is a **draft** until evaluators pass (BR-09).

## 5. Cross-cutting concerns

- **Correlation ID** per request, propagated through agents, tool calls, model calls, audit (NFR-05).
- **Structured logging** (structlog JSON) + **OpenTelemetry** spans for request/agent/model/retrieval/tool.
- **Feature flags** to gate write actions, connectors, agents, models (kill switch — BRD §16).
- **RBAC** at project + connector level; read/write tool separation; write tools off by default.

## 6. Data model

Implements BRD §15 Minimum Data Model — see `backend/app/domain` and Alembic migrations.
Core entities: User, Project, ProjectAccess, Connector, AgentRun, ToolCall, Evidence, Finding,
Risk, Action, Report, Evaluation, Feedback, AuditEvent.

## 7. Non-functional targets (BRD §13)

Performance (daily health < 60s), 99.5% availability, enterprise security (SSO/RBAC/vault/encryption),
privacy (retention/minimization/masking), auditability, horizontal scalability, reliability
(retry/timeout/circuit-breaker/idempotency/partial results), explainability, WCAG 2.1 AA,
observability, portability.
