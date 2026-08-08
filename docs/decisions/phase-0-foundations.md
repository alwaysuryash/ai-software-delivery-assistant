# Phase 0 — Foundation & Decisions

Aligns with BRD §18 Phase 0 (steps 11–15). These are the agreed foundational decisions for the MVP.

## 1. MVP tool set (BRD step 11 — one of each category)

| Category | Chosen tool (MVP) | Connector interface | Notes |
|---|---|---|---|
| Work management | **Azure DevOps Boards** | `WorkItemConnector` | Jira adapter behind same port |
| Source repository | **GitHub** | `RepositoryConnector` | Azure Repos adapter later |
| Test management | **Azure DevOps Test Plans** | `TestConnector` | Generic test-result normalization |
| CI/CD | **GitHub Actions / Azure Pipelines** | `PipelineConnector` | Build/deploy status |
| Document source | **Confluence** | `DocumentConnector` | SharePoint adapter later |

All connectors ship first as **mock connectors** with realistic sample data (Phase 1 step 20),
then real read-only implementations (Phase 2). Write tools are **disabled by default**.

## 2. Pilot project (BRD step 12)

- Pilot: **"Project Alpha"** (matches BRD Appendix B sample request).
- Read-only service credentials to be provisioned per connector, stored via `SecretProvider`.
- One sprint of realistic sample data seeded for offline development.

## 3. Health dimensions, weights, thresholds (BRD step 13, §12)

Deterministic, configurable. Defaults (must sum to 100%):

| Dimension | Weight | Example red trigger |
|---|---|---|
| Scope | 20% | Critical requirement unresolved; unapproved scope expansion |
| Schedule | 25% | Critical milestone forecast missed beyond tolerance |
| Quality | 25% | Open release-blocking defect; critical suite not executed |
| Engineering | 15% | Main build failed; critical dependency unresolved |
| Release/Operations | 15% | Prod-like env unavailable; rollback not validated |

Rule: return **`unknown`, not `green`** when required data is missing (BR-04).
Canonical config: `backend/app/scoring/health_config.py` (versioned, override per project).

## 4. User roles (BRD step 13, §7)

`delivery_manager`, `technical_lead`, `qa_lead`, `devops_lead`, `executive`, `administrator`.
Permissions matrix in `backend/app/domain/rbac.py`.

## 5. Data classification (BRD step 14)

| Class | Examples | Handling |
|---|---|---|
| Public | Marketing status headlines | No restriction |
| Internal | Backlog items, build status | Default; project-scoped |
| Confidential | Source code snippets, defect details | Minimized, masked before model submission |
| Restricted | Secrets, credentials, PII | Never sent to model; vault only |

## 6. Approval policy (BRD step 14, §16, FR-017)

- All write operations (ticket create/update, message send) require **explicit human approval**.
- Approval is bound to a **SHA-256 hash of the exact proposed payload**; any change → re-approval.
- Approver, timestamp, payload, result, and source evidence are recorded as immutable audit events.
- In the MVP, stakeholder messages are **drafted but never auto-sent** (FR-019).

## 7. Repositories, standards, CI, environments (BRD step 15)

- Monorepo: `backend/` (Python) + `frontend/` (Next.js) + `docs/`.
- Coding standards: `docs/engineering/coding-standards.md`.
- CI: lint (ruff/eslint), type-check (mypy/tsc), unit tests, contract tests, build.
- Environments: `local` (docker-compose), `dev`, `staging`, `prod` (parametrized via env).
