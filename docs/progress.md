# Progress

- [x] v0.1.0: Monorepo scaffold, typed BFF + SSE + mock simulator, auth,
  allow-list, all pages dashboard→settings, secret/XSS/traversal tests,
  Docker/Compose, docs, changelog
- [x] v0.2.0 foundation:
  - [x] Generic module capability/status layer
    (`security.appsec`, `contracts.toolkit`, `protocols.intelligence`;
    READY/DEGRADED/UNAVAILABLE/NOT_INSTALLED/UNKNOWN; never fake READY)
  - [x] Security section (`/security`, 10 tabs) via safe AppSec adapter
  - [x] Contracts section (`/contracts`, 13 tabs) via toolkit adapter
  - [x] Protocols section (`/protocols`, 15 tabs) via safe PI adapter
  - [x] Shared FindingCard / ReportViewer / GraphView / ModuleStatusCard
  - [x] Extended event model (security/contracts/protocols events)
  - [x] Mock scenarios SKLAB_MOCK_{SECURITY,CONTRACTS,PROTOCOLS}
  - [x] Frontend (15) / backend (23) / E2E (4+2) tests incl. boundary,
    secret-leak, XSS, artifact-scope
  - [x] Docs: security-ui, contracts-ui, protocols-ui,
    private-integrations, integration-contracts, mock-mode
- [x] Real-integration dogfood: typed contracts ready; live wiring pending
  stable local modules (adapters degrade to NOT_INSTALLED, mock verified)
- [ ] CI green on public repo (verify after push)
