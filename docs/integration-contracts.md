# Integration contracts (v0.2)

Capability IDs (see `backend/src/sklab_web/integrations/__init__.py`):

- `security.appsec` → `appsec_lab.py`
- `contracts.toolkit` → `contract_toolkit.py`
- `protocols.intelligence` → `protocol_intelligence.py`

Module states: READY / DEGRADED / UNAVAILABLE / NOT_INSTALLED / UNKNOWN.
Never fake READY.

Backend routes (auth-protected unless noted):

```text
GET /api/modules, /api/system (extended), /api/version (extended)
GET /api/security/status, /engagements, /engagements/{id},
    /engagements/{id}/traffic, /engagements/{id}/api-map,
    /findings, /findings/{id}, /simulations, /reports
GET /api/contracts/status, /projects, /projects/{id},
POST /api/contracts/projects/{id}/{compile|test|analyze|fuzz|invariants}
GET /api/contracts/findings, /tools
GET /api/protocols/status, /protocols, /protocols/{id}, /map, /assets,
    /authorities, /specs, /invariants, /evidence, /assurance, /monitor, /incidents
```

Error codes: MODULE_NOT_INSTALLED, MODULE_UNAVAILABLE,
PRIVATE_MODULE_UNAVAILABLE, BROWSER_UNAVAILABLE, ENGAGEMENT_NOT_FOUND,
CONTRACT_TOOL_UNAVAILABLE, COMPILE_FAILED, TEST_FAILED, FUZZ_COUNTEREXAMPLE,
INVARIANT_FAILED, UPGRADE_BLOCKED, ASSURANCE_STALE, MONITOR_DISCONNECTED,
INCIDENT_DATA_INCOMPLETE (see `frontend/src/lib/api.ts` ERROR_HELP).

Frontend types mirror backend Pydantic models; CI checks drift via
`api_schema: 2` + OpenAPI snapshot.
