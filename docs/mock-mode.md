# Mock mode

`SKLAB_MOCK_MODE=true` enables deterministic fixtures for every page and a
threaded run simulator: inspection → plan → hermes attempt 1 → REJECT
(regression `test_auth_timeout`) → retry → attempt 2 → ACCEPT 94 → COMPLETED.

Scenarios via payload: default success, `model: paid-*` → approval gate,
`scenario: blocked|fail` in tests. All screens demoable with no AI spend.

## v0.2 module mocks

- `SKLAB_MOCK_SECURITY=true` (or unified mock): active audit, role issue,
  CORS issue, verified fix.
- `SKLAB_MOCK_CONTRACTS=true`: compile success, fuzz counterexample
  (seed 42), invariant fail, upgrade REVIEW_REQUIRED.
- `SKLAB_MOCK_PROTOCOLS=true`: stale assurance (oracle changed), economic
  fixture, authority blast radius, monitor alert, incident, verified upgrade
  parts.

All fixtures are synthetic (`fixture.local`, `demo-token`, `proto-demo`);
no client hostnames, tokens, or private data.
