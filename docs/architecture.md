# Architecture

```
Browser → Next.js (frontend/) → FastAPI BFF (backend/src/sklab_web) → SKLab services
```

- Frontend: Next.js App Router, TypeScript, Tailwind. Pages per nav. SSE via
  EventSource with `last_id` resume + polling fallback for state.
- Backend: FastAPI. Typed Pydantic schemas in `models.py` (contract source).
  OpenAPI served by FastAPI; frontend `lib/api.ts` mirrors types (drift checked
  in CI by schema snapshot test).
- Integrations isolated in `integrations/`; Orchestrator via import or
  machine-readable CLI JSON only. Never duplicate state-machine logic.
- Mock mode: `MockStore` deterministic fixtures + threaded event simulator.
- No database in v0.1.0; in-memory + YAML/env config.
