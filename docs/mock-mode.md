# Mock mode

`SKLAB_MOCK_MODE=true` enables deterministic fixtures for every page and a
threaded run simulator: inspection → plan → hermes attempt 1 → REJECT
(regression `test_auth_timeout`) → retry → attempt 2 → ACCEPT 94 → COMPLETED.

Scenarios via payload: default success, `model: paid-*` → approval gate,
`scenario: blocked|fail` in tests. All screens demoable with no AI spend.
