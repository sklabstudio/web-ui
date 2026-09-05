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

Dashboard quick actions, plan-then-run AI workspace with live RepoContext/skills,
run inspector with SSE timeline + Cancel/Retry/Resume/Approve/Reject, Security
engagements + safe audits/simulations/retests, Contracts build/test/analyze/fuzz/
invariants/gas/coverage/upgrade/remediation, Protocols map/specs/simulations/
assurance, full module matrix + doctor, skills trust + task-scoped enable,
provider/agent live status with zero-cost health, and settings.

### Security / Contracts / Protocols (v0.2)

- **Security** (`/security`): engagements, browser status, live traffic
  (redacted), API map + role matrix, findings, bounded simulations, backend
  impact, remediation chain, reports — via optional private AppSec Lab.
- **Contracts** (`/contracts`): projects, inventory, toolchain, analysis,
  tests, fuzz, invariants, authorities, standards, upgrade review, gas,
  reports — via optional public Contract Toolkit.
- **Protocols** (`/protocols`): map, asset flows, authorities, dependencies,
  specs, invariants, threat model, evidence graph, economic twin
  (SIMULATION ONLY), upgrade intelligence, deployment guard, monitoring,
  incidents, assurance profile — via optional private Protocol Intelligence.

Optional private SKLab modules can integrate through the public backend
contract when installed locally. Private code/data never ships in this repo.
See `docs/private-integrations.md`, `docs/security-ui.md`,
`docs/contracts-ui.md`, `docs/protocols-ui.md`.

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

No direct patch apply, no leaderboard, no paid-model execution without approval.
Live AI execution needs an installed agent (otherwise the UI reports
AGENT_UNAVAILABLE honestly); deterministic mock mode (`SKLAB_MOCK_MODE=true`)
covers trials and E2E. See `docs/progress.md`.

## License

MIT — Copyright (c) 2026 SKLab Studio.
