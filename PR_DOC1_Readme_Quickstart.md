# PR DOC1 — README, Quickstart (Railway), envs, module matrix

**Branch**: `feature/docs-01`  
**Title**: README + Quickstart for Railway + .env.example + module matrix  
**Execution order**: **Last**  
**Recommended Copilot model**: **Claude**

## Description
Publishes a crisp **README** with Umbra overview, Railway deployment steps, env variables (OpenRouter, R2, Creator providers), module matrix, and links to ARCHITECTURE/PROJECT_MAP/ACTION_PLAN. Adds `.env.example` with sane defaults and comments.

## Tasks for Copilot
- `README.md` — what/why, Railway deploy (Dockerfile + `$PORT`), health endpoint, module list, platform envs, samples.
- `.env.example` — include `OPENROUTER_*`, `R2_*`, `CREATOR_*`, `MAIN_N8N_URL`, `ALLOWED_*`, `LOCALE_TZ`, `PRIVACY_MODE`, `RATE_LIMIT_PER_MIN`.
- Screenshots/diagrams placeholders.

## Acceptance
- New contributor can deploy to Railway, set envs, run `/status`, and try each module quickly.