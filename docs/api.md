# API

Base: same-origin, proxied to BFF in production.

- `GET /api/health`, `GET /api/version`, `GET /api/system`
- `GET /api/repos`, `GET /api/repos/{id}`, `POST /api/repos/{id}/context`
- `GET /api/agents`, `GET /api/agents/{id}`
- `GET /api/providers`, `POST /api/providers`, `POST /api/providers/{id}/test`
- `POST /api/runs/plan`, `POST /api/runs`, `GET /api/runs`, `GET /api/runs/{id}`
- `POST /api/runs/{id}/resume`, `POST /api/runs/{id}/cancel`
- `GET /api/runs/{id}/events` (SSE `text/event-stream`, `?last_id=` resume)
- `GET /api/runs/{id}/patch`, `GET /api/artifacts/{id}`, `GET /api/audit`
- `GET/PUT /api/settings`, `POST /api/auth/login|logout`
- `GET /api/environments|benchmarks|codetrials|promptbench|skills`

Errors: `{code, message}` with codes AUTH_REQUIRED, PROVIDER_UNAVAILABLE,
AGENT_UNAVAILABLE, BUDGET_EXHAUSTED, APPROVAL_REQUIRED, VERIFICATION_FAILED,
RUN_CANCELLED, etc. No stack traces to browser.
