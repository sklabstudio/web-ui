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
- [x] v0.3.0 operational console:
  - [x] Live-first wiring: real OrchestratorService runs (persistent store + SSE),
    live agents/connections/RepoContext/skills, full module matrix + doctor
  - [x] AppSec/Contracts/Protocols browser write-ops via typed SDK + `--json` CLIs
  - [x] Run controls (cancel/retry/resume/approve/reject), finding actions, reports,
    interactive graphs, skills/providers/agents/modules/settings operations
  - [x] Normalized error UX + loading/empty/disabled states; CSP hydration fix
  - [x] Frontend (20) / backend (37) / E2E (13 mock + live smoke) tests, prod build green
  - [ ] Live VPS deploy + URL verification (in progress)
