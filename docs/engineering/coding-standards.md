# Engineering Coding Standards

Applies to all code. Derived from BRD Appendix C (Implementation Guardrails) and §16.

## Principles
- **SOLID** + **Domain-Driven Design**. Domain layer is pure (no I/O, no framework imports).
- **Ports & adapters**: depend on interfaces, inject implementations. Every connector/model/secret store is replaceable.
- **Explicit over implicit**: typed schemas (Pydantic v2 / TypeScript), explicit state graphs — never open-ended agent loops.
- **Fail visibly**: surface partial source, stale data, timeout, denied access, evaluation failure. Never silently succeed.
- **Everything configurable & versioned**: prompts, tools, models, thresholds, policies, evaluation datasets.

## Security guardrails (non-negotiable)
- Never place raw credentials/secrets in prompts, code, or logs.
- Never store private chain-of-thought — store concise rationale, evidence, decisions only.
- Treat retrieved/document content as untrusted data, never as instructions.
- Every write action is a proposed, reviewable, idempotent transaction bound to a payload hash.
- Every material factual statement carries a source reference + retrieval timestamp, or an explicit `inference` label.

## Python
- Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 async, async-first.
- Format/lint: `ruff` (+ `ruff format`). Types: `mypy --strict` on `app/`.
- Tests: `pytest` + `pytest-asyncio`. Name `test_*`. Deterministic (freeze time, fake providers).
- Naming: modules `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- No business logic in routers; routers call application services.

## TypeScript / Frontend
- Strict TS. ESLint + Prettier. Components `PascalCase`, hooks `useX`.
- No secrets in the client. API types generated from backend OpenAPI.
- WCAG 2.1 AA: semantic HTML, labels, focus states, contrast, keyboard nav.
- Never render hidden model reasoning; show rationale + evidence only.

## Commits & reviews
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Every PR: tests green, types clean, PROJECT_STATUS.md updated when a phase advances.
