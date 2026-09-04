# SKLab Web UI

**A private web control center for the SKLab AI engineering workstation.**

> Run agents. Watch progress. Verify results. Control everything from one place.

Quick start:

```bash
docker compose up --build
```

or dev:

```bash
# backend
cd backend && pip install -e ".[dev]" && SKLAB_MOCK_MODE=true uvicorn sklab_web.main:app --port 8787

# frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:3000. API at http://localhost:8787/api/health.

## Why

One private interface for repositories, tasks, agents, providers, live runs,
verification, history, skills, environments, and settings. The browser is the
control surface; SKLab backends remain the authority.

## Architecture

Browser → Next.js UI → FastAPI BFF → Orchestrator / Agent Adapters /
Provider Connections / RepoContext / ReproBox / PatchBench / BenchSuite /
CodeTrials / PromptBench. See `docs/architecture.md`.

## Features

Dashboard, repos (allowed roots only), plan-then-run task flow, live SSE run
page, attempts/retry evidence, approval gates, verification view, read-only
diff viewer, history, agents, providers (secret-safe), environments,
benchmarks, codetrials/promptbench read views, skills foundation, settings.

## Installation / Development / Deployment / Auth

See `docs/deployment.md` and `docs/authentication.md`. Default to private
access: localhost/SSH tunnel, Tailscale, Cloudflare Access, or Caddy/Nginx
HTTPS + single-user token/password. Never expose with `AUTH_MODE=disabled`.

## Security Model

No raw secrets in responses/logs/browser storage, traversal rejection,
CSP + same-origin CORS, normalized errors, audit log. See `docs/security.md`.

## Integrations / Mock Mode

`SKLAB_MOCK_MODE=true` runs the full UI deterministically without real AI.
Real Orchestrator wiring is isolated in `backend/src/sklab_web/integrations/`.
See `docs/integrations.md`, `docs/mock-mode.md`, `docs/demo.md`.

## Limitations / Roadmap

No direct patch apply, no leaderboard, no Skill Hub auto-install, no Cyber /
Contracts packs yet. See `docs/progress.md`.

## License

MIT — Copyright (c) 2026 SKLab Studio.
