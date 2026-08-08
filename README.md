# AI Software Delivery Assistant

An AI-native, multi-agent **Software Delivery Intelligence Platform**. It continuously monitors
software delivery, gathers project evidence from enterprise tools (Azure DevOps, GitHub, Jira,
test management, CI/CD, SharePoint/Confluence, Teams/Outlook), analyzes project health with
specialized AI agents, detects risks before escalation, prepares evidence-backed reports, and
**keeps a human in control before any write action**.

> Built to the Business Requirements Document (BRD v1.0, 19-Jul-2026). This is an enterprise
> product built incrementally, strictly following the BRD's 8-phase plan. Progress is tracked in
> [PROJECT_STATUS.md](PROJECT_STATUS.md) — the source of truth.

## Architecture

```
User (PM / Delivery Manager)
        │
   AI Delivery Assistant  (Next.js web)
        │
   Application API  (FastAPI)
        │
   Orchestrator (LangGraph explicit graph)
        │
 ┌──────┬───────┬───────┬─────────┬──────┐
 BA    Dev     QA     DevOps     PM     (specialist agents)
 └──────┴───────┴───────┴─────────┴──────┘
        │
   Tool Gateway (permission-aware MCP-style connectors)
        │
 Azure DevOps · GitHub · Jira · SonarQube · Teams/Outlook · SharePoint/Confluence
```

Full design: [docs/architecture/solution-architecture.md](docs/architecture/solution-architecture.md).

## Repository layout

```
backend/      FastAPI app — domain, application, infrastructure, agents, connectors, api (DDD)
frontend/     Next.js web app — project selector, assistant workspace, health, approvals
docs/         Architecture, ADRs, security (threat model), decisions, traceability
docker-compose.yml   Local Postgres + Redis
```

## Quick start (local dev)

Prerequisites: Docker, Python 3.12+, Node 20+, pnpm.

```bash
cp .env.example .env          # fill in values; never commit .env
docker compose up -d          # Postgres + Redis
# backend
cd backend && python -m venv .venv && . .venv/Scripts/activate  # (Windows: .venv\Scripts\activate)
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
# frontend
cd frontend && pnpm install && pnpm dev
```

## Engineering principles

SOLID · Domain-Driven Design · explicit workflows over autonomous loops · every connector
replaceable · every model/prompt/threshold/policy configurable & versioned · every action
auditable · every failure visible · evaluation, observability, governance, explainability, and
security are first-class features (BRD Appendix C).

## License

Internal / Client Demonstration Use.
