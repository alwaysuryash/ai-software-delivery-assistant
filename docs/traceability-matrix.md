# Requirements Traceability Matrix

Maps BRD requirements to implementation + verification. Updated each phase. `⬜` = later phase.

| Req | Description | Implementation | Test / Verification |
|---|---|---|---|
| FR-001 | Authentication (SSO) | `core/security.py`, `api/routers/auth.py` (dev provider; Entra later) | `test_api.py::test_dev_login_and_me` |
| FR-002 | Project + connector RBAC | `domain/rbac.py`, `application/access.py`, `api/routers/projects.py` | `test_rbac.py`, `test_api.py::test_outsider_cannot_see_project` |
| FR-003 | Project configuration | `Project`/`Connector` models; seed script | `test_api.py` (project listing) |
| FR-011 | Evidence citation contract | `domain/contracts.py` (`EvidenceRef`, `Finding`) | Model validation (min 1 evidence) |
| FR-012 | Freshness / data-gap warnings | `contracts.DataGap` + `retrieved_at`/`source_timestamp` on evidence | ⬜ Phase 3 |
| FR-021 | Audit trail | `application/audit.py`, `AuditEvent` model | ⬜ expanded Phase 4/7 |
| BR-01 | No claim without evidence | `Finding.evidence` min_length=1; `is_inference` flag | contract enforced |
| BR-02 | No source without authorization | `AccessService.require`, `ConnectorContext.allowed_scopes` | `test_api.py::test_outsider_cannot_see_project` |
| BR-04 | Unknown, not guess | `Health.UNKNOWN` default; scoring returns unknown | ⬜ Phase 3 |
| NFR-05 | Correlation ID traceability | `core/correlation.py`, `api/middleware.py` | `test_api.py::test_healthz_is_public` (header echoed) |
| NFR-11 | Observability | structlog JSON + request logging; OTEL deps wired | manual (log output) |
| NFR-12 | Portability / replaceable adapters | ports: `ModelProvider`⬜, `Connector`, `SecretProvider`⬜, `RetrievalProvider`⬜ | `test_connectors.py` |
| §16 | Kill switches | `core/feature_flags.py` | ⬜ wired to admin API later |
| §20 | Connector contract tests | mock connectors + registry | `test_connectors.py` |
