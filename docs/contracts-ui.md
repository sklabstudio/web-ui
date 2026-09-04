# Contracts UI (`/contracts`)

Surface for the PUBLIC Contract Toolkit (optional dependency).

- Tabs: Overview, Projects, Contracts, Tools, Analysis, Tests, Fuzz,
  Invariants, Authorities, Standards, Upgrades, Gas, Reports.
- Project actions: Inspect/Compile/Test/Analyze/Fuzz/Run Invariants/
  Generate Report. No deployment button in v0.2.
- Tools table shows installed/version/status/capabilities; never fakes support.
- Invariant sources labeled EXPLICIT / STANDARD_TEMPLATE / PRIVATE_MINED
  only when backend provides them.
- Upgrade verdict: SAFE/RISKY/INCOMPATIBLE/INCONCLUSIVE + storage/ABI/
  authority/initializer diffs.
- Gas shows hotspots/regressions; no dollar conversion without backend price.
