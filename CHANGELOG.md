# Changelog

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
