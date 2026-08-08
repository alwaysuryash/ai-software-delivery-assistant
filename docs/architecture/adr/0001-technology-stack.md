# ADR-0001: Technology Stack

- Status: Accepted
- Date: 2026-07-20
- Deciders: Solution Architect, AI Engineering Lead, Product Owner

## Context

The BRD §14.1 suggests options at several layers ("Python FastAPI or .NET",
"Semantic Kernel, LangGraph, or custom state machine", "Azure AI Search or equivalent").
We must pick one coherent stack optimized for the AI/agent ecosystem, ease of build, and
portability (NFR-12), for a Fortune-500-grade production deployment.

## Decision

| Layer | Decision | Rationale |
|---|---|---|
| Backend | **Python 3.12+ / FastAPI (async)** | Richest AI/agent + evaluator + Azure SDK ecosystem; async performance; typed with Pydantic v2 |
| Orchestration | **LangGraph** | Explicit, inspectable state graph with max-step bounds and deterministic routing — BRD demands explicit graphs over agent loops |
| AI Platform | **Azure OpenAI / AI Foundry** behind a `ModelProvider` port | Enterprise content controls & approved endpoints; abstraction keeps it swappable, plus a deterministic **FakeModelProvider** for offline dev/tests |
| Frontend | **Next.js (App Router) + React + TypeScript + Tailwind** | Per BRD; streaming agent progress; strong a11y story for WCAG 2.1 AA |
| Database | **PostgreSQL + SQLAlchemy 2.0 (async) + Alembic** | Portable over Azure SQL; mature migrations |
| Vector/RAG | **pgvector** behind a `RetrievalProvider` port | "Equivalent hybrid index"; Azure AI Search adapter added later without domain changes |
| Cache/State | **Redis** | Short-lived agent execution state + distributed locks |
| Secrets | **`SecretProvider` port** (env default → Azure Key Vault adapter) | Never store secrets in prompts/source (BRD §16) |
| Observability | **OpenTelemetry + structlog** | Portable tracing; Application Insights exporter optional |

## Consequences

- Two languages (Python backend, TypeScript frontend). Contracts shared via OpenAPI-generated types.
- All external dependencies (models, connectors, secrets, retrieval) sit behind ports → replaceable.
- Offline development is possible end-to-end using `FakeModelProvider` + mock connectors.
- Azure-specific adapters (OpenAI, Key Vault, AI Search) are additive, isolated in `infrastructure/`.
