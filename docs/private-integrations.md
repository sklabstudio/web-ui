# Private integrations boundary

PUBLIC stays PUBLIC. PRIVATE stays PRIVATE.

This repo (PUBLIC) may contain:

- public UI code, generic typed API contracts, capability models,
  public adapters, mock fixtures.

It must NEVER contain:

- AppSec Lab / Protocol Intelligence implementation, client evidence,
  private reports/sessions/models/data, sensitive repo URLs, credentials.

Rules enforced by tests (`backend/tests/test_v02.py`):

- Frontend builds with private modules absent.
- Backend adapters use dynamic `importlib.find_spec` discovery only.
- DTOs pass through `redacted()` (cookies/tokens/RPC URLs stripped).
- Artifacts scoped to `patch-*`, `artifact-rep-*`, `ev-*` IDs only.
- `test_secret_leak_absent_from_fixtures` + secret tests guard fixtures,
  DOM, logs, DTOs, git history.
