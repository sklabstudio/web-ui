# Changelog

## 0.3.0 — operational control center

Browser-operable workflows over the real backend (live-first, mock-fallback, never fake READY):

- AI Workspace: repo select + live RepoContext inspect, agent/provider/model/skill
  dropdowns from live catalogs, skill resolution preview, execution mode/budget
  policy, plan-then-run with `run_id`, honest AGENT_UNAVAILABLE when no agent installed
- Runs: full inspector (facts, live SSE timeline with friendly labels, logs,
  attempts, verification, patch, warnings) + Cancel/Retry/Resume/Approve/Reject;
  real persistent OrchestratorService runs in live mode, deterministic simulator in mock
- AppSec: engagement create/activate/close, browser launch (headed/headless),
  capture, safe audit, bounded simulations, finding retest, impact, reports
- Contracts: project create-from-template + .sol import, compile/test/analyze/fuzz/
  invariants/gas/coverage/graphs/upgrade-review/storage/ABI-diff/threat-model/
  prepare-fix/verify-fix/report via typed SDK + `--json` CLIs
- Protocols: project init, IR/map build, spec/invariant derivation, bounded economic
  simulation + named scenarios, upgrade/change-impact/deployment-guard,
  regression, assure, verify, live monitor/incidents, reports (simulation only)
- Skills: search, trust/permissions/risk, task-scoped enable/disable, audit,
  task-aware resolve, auto mode OFF/SAFE/SMART/FULL (install ≠ global enable)
- Providers/Agents: live catalogs, zero-cost health (never paid inference), refresh
- Modules: full 18-module matrix via `sklab status`, per-module details, zero-cost doctor
- UX: quick-action Home, normalized errors with help + retry, loading/empty/disabled
  states everywhere, finding actions, report view/copy/download, interactive graphs
  (zoom/fit/select/search), responsive tables, CSP fixed so the app actually hydrates
- E2E: Playwright suites A–F against mock (login → verified flows) with webServer
  harness; live smoke spec for the VPS (LIVE_E2E=1)
- Tests: backend 37, frontend 20, E2E 13, production build verified

## 0.2.0

Implemented (public integration foundation; live private wiring is optional):

- Module capability layer (`security.appsec`, `contracts.toolkit`,
  `protocols.intelligence`) with READY/DEGRADED/UNAVAILABLE/NOT_INSTALLED/
  UNKNOWN — never fake READY; `/api/modules`, extended `/api/system`,
  `/api/version` (schema 2)
- Security section: overview/engagements/browser/live-traffic (redacted)/
  API map + role matrix/findings/simulations/impact/remediation/reports
- Contracts section: overview/projects/inventory/tools/analysis/tests/fuzz/
  invariants/authorities/standards/upgrade-review/gas/reports
- Protocols section: overview/map/asset-flows/authorities/dependencies/
  specs/invariants/threat/evidence/economic-twin (SIMULATION ONLY)/upgrade/
  guard/monitor/incidents/assurance + freshness
- Shared FindingCard/ReportViewer/GraphView/ModuleStatusCard + extended
  event model + normalized v0.2 error codes
- Mock scenarios SKLAB_MOCK_{SECURITY,CONTRACTS,PROTOCOLS} (synthetic only)
- Tests: frontend 15, backend 23, E2E security/contracts/protocols, plus
  boundary/secret/XSS/artifact-scope; production build verified

## 0.1.0

Implemented:

- Next.js + TypeScript + Tailwind frontend with Dashboard, Repositories, New Task,
  Runs, Live Run (SSE), Agents, Providers, Environments, Benchmarks, CodeTrials,
  Prompt Experiments, Skills, Settings, Login
- FastAPI typed BFF with OpenAPI, health/version/system, plan/run/cancel/resume,
  SSE event streaming with resume, artifact safety, audit log
- Single-user auth: disabled | token | password (bcrypt, HTTP-only cookie, rate limit)
- Allowed-root repository policy with traversal rejection
- Deterministic mock mode (`SKLAB_MOCK_MODE=true`) + fake retry run simulator
- Isolated integrations for Orchestrator (import/CLI-JSON) + 8 SKLab services
- Terminal-like safe log viewer, attempt timeline, verification view, read-only diff viewer
- Secret safety: keys never returned, never stored in browser, leak tests
- XSS-safe rendering, CSP, same-origin CORS, normalized API errors
- Docker + Compose, Caddy/Nginx examples, Tailscale guidance
- Pytest + Vitest + Playwright (mock) suites, CI, docs, demo script

No fake real-agent claims. Orchestrator live execution remains pending until its
stable API is wired beyond plan classification; mock contract is verified.
