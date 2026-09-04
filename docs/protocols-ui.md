# Protocols UI (`/protocols`)

Public-safe surface for OPTIONAL PRIVATE Protocol Intelligence.

- Tabs: Overview, Architecture, Asset Flows, Authorities, Dependencies,
  Specifications, Invariants, Threat Model, Evidence, Economic Twin,
  Upgrades, Deployment Guard, Monitoring, Incidents, Assurance.
- All graphs use shared `GraphView` (bounded 200 nodes/edges, table
  fallback, text alternative). No proprietary generation logic exposed.
- Invariant statuses: PROVEN/DISPROVEN/BOUNDED_VERIFIED/INCONCLUSIVE/NOT_RUN.
  Fuzz pass is never equated with proof.
- Economic Twin is SIMULATION ONLY: synthetic price/liquidity/withdrawal
  scenarios, no live transactions.
- Assurance profile uses VERIFIED/PARTIAL/FAILED/INCONCLUSIVE/NOT_TESTED/
  NOT_APPLICABLE with no single misleading score; stale reason + re-run
  action when backend supports it.
