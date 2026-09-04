# Security UI (`/security`)

Public-safe browser surface for the OPTIONAL PRIVATE AppSec Lab.

- Tabs: Overview, Engagements, Browser, Live Traffic, API Map, Findings,
  Simulations, Impact, Remediation, Reports.
- Data only via `GET /api/security/*` typed DTOs. No raw cookies/tokens,
  no remote-debug port, no devtools proxy.
- Role matrix rendered from backend `roles` map; suspicious 401/403/200
  deltas highlighted but never auto-claimed as vulnerabilities.
- Findings statuses: OPEN/CONFIRMED/LIKELY/NEEDS_REVIEW/FIXED/
  FIXED_VERIFIED/ACCEPTED_RISK/FALSE_POSITIVE/INCONCLUSIVE.
- Impact grid is backend-provided only (NONE/LOW/MEDIUM/HIGH/UNKNOWN).
- Remediation chain is prepare → run → view patch → verify; never auto-apply.
