# PR SEC1 — Security & Observability: RBAC matrix, structured logs, metrics, audit

**Branch**: `feature/security-01`  
**Title**: Per-module RBAC + structured logs + metrics stub + audit trail  
**Execution order**: **After core + main modules**  
**Recommended Copilot model**: **GPT**

## Description
Hardens Umbra with **per-module/action RBAC**, **structured JSON logs with request_id**, a **Prometheus-ready metrics stub**, and a durable **audit log** with redaction.

## Tasks
- `umbra/core/rbac.py` — RBAC matrix `{module: {action: role}}`, helper guards.
- Extend PermissionManager to consult RBAC on dispatch.
- `umbra/core/logging_mw.py` — request_id injection; user_id, module, action, latency.
- `umbra/core/metrics.py` — counters/gauges/histograms; `/metrics` endpoint (Prometheus).
- `umbra/core/audit.py` — append-only audit writer; store records in R2 as JSONL (no SQL).
- Redaction utils: scrub tokens, emails, phone numbers in logs/audit.
- Apply RBAC/logging/metrics in bot dispatcher and module registry.

## Tests
- RBAC allows/denies correctly; admin-only enforced.
- Logs include request_id and required fields.
- Metrics increment on happy/error paths.
- Audit rows written; sensitive fields redacted.

## Docs
- README "Security & Observability" with RBAC examples; `/metrics` usage.