# Integrations

All shims in `backend/src/sklab_web/integrations/` degrade to UNAVAILABLE when
packages are absent, READY when importable, mock fixtures when
`SKLAB_MOCK_MODE=true`.

- `orchestrator.py` — import `sklab_orchestrator.planning/routing` for plan
  classification; CLI `sklab-run plan --json` fallback; never Rich text.
- `adapters.py` — agent/provider detectors.
- Real status dogfood: zero-cost status/version/capability reads only, no
  inference spend, no secret reveal.
