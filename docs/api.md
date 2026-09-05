# API

Base: same-origin, proxied to BFF in production (nginx) or via
`SKLAB_BACKEND_URL` rewrites in local/E2E dev.

- `GET /api/health`, `GET /api/version`, `GET /api/system`
- `GET /api/repos`, `GET /api/repos/{id}`, `POST /api/repos/{id}/context` (live RepoContext when installed)
- `GET /api/agents`, `GET /api/agents/{id}` (live adapter catalog + zero-cost health)
- `GET /api/providers`, `POST /api/providers`, `POST /api/providers/{id}/test` (zero-cost only, never inference)
- `POST /api/runs/plan` (live inspect+plan, returns `run_id`), `POST /api/runs` (create+execute async)
- `GET /api/runs`, `GET /api/runs/{id}`
- `POST /api/runs/{id}/execute|retry|resume|cancel|approve|reject`
- `GET /api/runs/{id}/events` (SSE `text/event-stream`, `?last_id=` resume)
- `GET /api/runs/{id}/patch`, `GET /api/artifacts/{id}`, `GET /api/audit`
- `GET/PUT /api/settings`, `POST /api/auth/login|logout`
- `GET /api/environments|benchmarks|codetrials|promptbench`
- Skills: `GET /api/skills`, `GET /api/skills/{id}`, `GET /api/skills/{id}/audit`,
  `POST /api/skills/resolve`, `POST /api/skills/{id}/enable|disable`,
  `GET|POST /api/skills-auto` (OFF|SAFE|SMART|FULL; install never means global enable)
- Modules: `GET /api/modules` (3 capability adapters), `GET /api/modules/full`
  (full `sklab status` matrix), `GET /api/modules/{id}`, `GET /api/doctor` (zero-cost)
- Security: `GET /api/security/status|engagements|{id}|{id}/traffic|{id}/api-map|findings|{id}|simulations|reports`,
  `POST /api/security/engagements` (create), `POST .../activate|close`,
  `GET /api/security/browser`, `POST .../browser/launch|capture|audit|simulate`,
  `POST /api/security/retest`, `GET .../findings/{id}/impact`, `POST .../report`
- Contracts: `GET /api/contracts/status|projects|{id}|findings|tools`,
  `POST .../{id}/compile|test|analyze|fuzz|invariants|gas|coverage|upgrade-review|remediate|retest|report`,
  `POST /api/contracts/projects` (template), `POST /api/contracts/projects/import` (.sol upload),
  `GET .../{id}/graph|storage|abi-diff|threat-model`
- Protocols: `GET /api/protocols|{id}|{id}/map|assets|authorities|specs|invariants|evidence|assurance|monitor|incidents`,
  `POST /api/protocols` (init), `POST .../ir|map|specs|invariants|simulate|economic|assure|verify|upgrade-review|deployment-guard|regression|report`

Live-first, mock-fallback: with `SKLAB_MOCK_MODE` off, every endpoint prefers
the real module (Orchestrator service, `sklab-*` CLIs `--json`, typed SDKs)
and fails with a normalized code when the capability is absent — never fake data.
With mocks on, deterministic fixtures are labeled `mock: true`.

Errors: `{code, message}` with codes AUTH_REQUIRED, PROVIDER_UNAVAILABLE,
AGENT_UNAVAILABLE, BUDGET_EXHAUSTED, APPROVAL_REQUIRED, VERIFICATION_FAILED,
RUN_CANCELLED, MODULE_NOT_INSTALLED, MODULE_UNAVAILABLE,
PRIVATE_MODULE_UNAVAILABLE, BROWSER_UNAVAILABLE, ENGAGEMENT_NOT_FOUND,
NOT_FOUND, BAD_REQUEST, etc. No stack traces or secrets to browser.
