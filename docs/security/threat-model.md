# Threat Model — AI Software Delivery Assistant

Status: Draft for Build (Phase 0). Revisit before production (BRD §16: "threat modeling before production rollout").
Method: STRIDE + LLM/agent-specific threats (OWASP LLM Top 10). Aligns with BRD §16, §22, §20 (Security tests).

## 1. Assets

- Project delivery evidence (backlog, code metadata, test results, pipelines, documents).
- Connector credentials / service tokens (high value).
- Reports, approvals, audit trail (integrity critical).
- LLM prompts, tool schemas, model routing config.
- User identity & project access mappings.

## 2. Trust boundaries

1. Browser ↔ Application API (authenticated, RBAC-enforced).
2. API ↔ Orchestrator/Agents (internal; correlation-scoped).
3. Agents ↔ Tool Gateway ↔ Enterprise systems (per-connector least privilege).
4. Agents ↔ Model Provider (data-minimized, masked; secrets never sent).
5. Retrieved documents = **untrusted data** crossing into the model context.

## 3. Threats & mitigations

| ID | Threat (STRIDE / LLM) | Mitigation | BRD ref |
|---|---|---|---|
| T-01 | Spoofing user identity | Enterprise SSO (OIDC), short-lived tokens, session binding | FR-001, NFR-03 |
| T-02 | Elevation / cross-project access | Project + connector RBAC; access checks at retrieval **and** display; project-scoped tokens | FR-002, BR-02 |
| T-03 | Cross-project data leakage | Metadata filters on every retrieval; tenant/project isolation tests | §22 |
| T-04 | Prompt injection in documents | Treat retrieved content as data, not instructions; instruction hierarchy; output filtering; tool allowlists | §16, §22 |
| T-05 | Tool misuse / excessive autonomy | Explicit state graph, max steps, max tool calls, timeouts, write tools disabled by default | §16, §22 |
| T-06 | Unauthorized/unapproved write | Approval bound to payload hash; write requires human approval; immutable audit | FR-017, BR-03 |
| T-07 | Secret leakage into prompts/logs | `SecretProvider` + masking; secrets never in prompts or source; log scrubbing | §16, BR-08 |
| T-08 | Tampering with audit trail | Append-only audit events; integrity hash chain (later); restricted write path | NFR-05 |
| T-09 | SSRF via connector endpoints | Endpoint allowlists, schema-validated args, no user-controlled URLs to internal ranges | §20 Security |
| T-10 | Hallucinated findings presented as fact | Mandatory citations, structured output, evaluators, deterministic scoring | BR-01, §22 |
| T-11 | Repudiation of actions | Correlation IDs + full audit (request, sources, tool calls, model version, approval) | FR-021 |
| T-12 | Denial of service / cost blowup | Rate limits, budgets, circuit breakers, model routing, token/cost monitoring | §22 |

## 4. Kill switches (BRD §16)

Per-connector, per-project, per-model, per-agent enable/disable feature flags. Write actions
globally gated. Documented in `backend/app/core/feature_flags.py`.

## 5. Data protection

Encryption in transit (TLS) and at rest; data minimization on retrieval; masking of secrets,
credentials, PII, and restricted source code before model submission (BR-08); configurable
retention for prompts, retrieved text, outputs, embeddings, logs (NFR-04).

## 6. Residual risks / TODO before production

- Formal pen-test, SSRF fuzzing, RBAC isolation test suite (Phase 8).
- Audit hash-chaining / WORM storage.
- DLP scanning of outbound model payloads.
