"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { GraphView } from "@/components/GraphView";
import { ReportViewer } from "@/components/ReportViewer";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

const TABS = ["Overview", "Architecture", "Asset Flows", "Authorities", "Dependencies", "Specifications", "Invariants", "Threat Model", "Evidence", "Economic Twin", "Upgrades", "Deployment Guard", "Monitoring", "Incidents", "Assurance"] as const;

export default function ProtocolsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [list, setList] = useState<Record<string, unknown>[]>([]);
  const [pid, setPid] = useState("proto-demo");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [out, setOut] = useState<unknown>(null);
  const [outLabel, setOutLabel] = useState("");
  const [err, setErr] = useState<unknown>("");
  const [msg, setMsg] = useState("");
  const [createId, setCreateId] = useState("");
  const [scenario, setScenario] = useState("price-drop");

  const load = useCallback(async () => {
    setErr("");
    try {
      setStatus(await api<Record<string, unknown>>("/api/protocols/status"));
    } catch (e) { setErr(e); return; }
    try {
      const p = await api<Record<string, unknown>[]>("/api/protocols");
      setList(p);
      if (p.length && !p.some((x) => String(x.id) === pid)) setPid(String(p[0].id));
    } catch { /* keep */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!pid) return;
    api<Record<string, unknown>>(`/api/protocols/${pid}`).then(setDetail).catch(() => setDetail(null));
  }, [pid]);

  async function act(label: string, method: string, path: string, body?: unknown) {
    setErr("");
    setMsg(`${label}…`);
    try {
      const r = await api<unknown>(path, { method, body: body === undefined ? "{}" : JSON.stringify(body) });
      setOut(r);
      setOutLabel(label);
      setMsg(`${label}: done`);
      load();
      setDetail(await api<Record<string, unknown>>(`/api/protocols/${pid}`).catch(() => detail));
    } catch (e) {
      setErr(e);
      setMsg("");
    }
  }

  const d = (detail || {}) as Record<string, unknown>;
  const arr = (k: string) => (Array.isArray(d[k]) ? (d[k] as Record<string, unknown>[]) : []);
  const showOut = out ? JSON.stringify(out, null, 2).slice(0, 4000) : "";
  const unavailable = !status || String(status.state) === "NOT_INSTALLED";

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Protocols</h1>
      <p className="rounded border border-zinc-800 p-2 text-xs text-zinc-500">SIMULATION ONLY — no live transactions. Private implementation stays hidden.</p>
      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {msg && <p className="text-xs text-zinc-400">{msg}</p>}
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <label>
          Project{" "}
          <select value={pid} onChange={(e) => setPid(e.target.value)} className="rounded bg-zinc-900 px-2 py-1" aria-label="Protocol project">
            {list.map((p) => (
              <option key={String(p.id)} value={String(p.id)}>{String(p.id)}</option>
            ))}
            <option value={pid}>{pid}</option>
          </select>
        </label>
        <input value={createId} onChange={(e) => setCreateId(e.target.value)} placeholder="new-protocol-id"
          className="rounded bg-zinc-900 px-2 py-1" aria-label="New protocol ID" />
        <ActionButton label="Create" onRun={() => act("create", "POST", "/api/protocols", { id: createId })} disabledReason={!createId ? "protocol ID required" : unavailable ? "module not installed" : ""} />
      </div>
      <div role="tablist" aria-label="Protocol sections" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => { setTab(t); setOut(null); setOutLabel(""); }}
            className={`rounded border px-2 py-1 text-sm ${tab === t ? "border-cyan-500 text-white" : "border-zinc-800 text-zinc-400"}`}>{t}</button>
        ))}
      </div>

      {tab === "Overview" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          {!status ? <p className="text-zinc-500">Not installed</p> : (
            <ul className="grid gap-2 md:grid-cols-2">
              <li>Status: <StatusBadge status={String(status.state || "UNKNOWN")} /></li>
              <li>Protocols: <span className="mono">{String(status.protocols ?? list.length)}</span></li>
              <li>Stale: <span className="mono">{String(status.stale ?? "—")}</span></li>
              <li>Alerts: <span className="mono">{String(status.alerts ?? "—")}</span></li>
              {list[0] && (<>
                <li>Chain: <span className="mono">{String(list[0].chain)}</span></li>
                <li>Freshness: <span className="mono">{String(list[0].assurance_freshness)}</span></li>
                <li>Open findings: <span className="mono">{String(list[0].open_findings)}</span></li>
                <li>Active alerts: <span className="mono">{String(list[0].active_alerts)}</span></li>
              </>)}
            </ul>
          )}
          <div className="mt-2 flex flex-wrap gap-2">
            <ActionButton label="Build map" onRun={() => act("map", "POST", `/api/protocols/${pid}/map`)} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Build IR" onRun={() => act("ir", "POST", `/api/protocols/${pid}/ir`)} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Full audit" onRun={() => act("audit", "POST", `/api/protocols/${pid}/verify`)} disabledReason={unavailable ? "module not installed" : ""} />
          </div>
        </section>
      )}
      {tab === "Architecture" && (
        <section>
          <GraphView title="Protocol map" nodes={(d.map as { nodes?: string[] } | undefined)?.nodes || ["DemoToken", "DemoVault", "PriceOracle"]}
            edges={(((d.map as { edges?: string[][] } | undefined)?.edges) || [["DemoVault", "DemoToken"]]).map((e) => ({ from: e[0], to: e[1] }))} />
        </section>
      )}
      {tab === "Asset Flows" && (
        <section className="overflow-x-auto rounded border border-zinc-800 text-sm">
          {arr("assets").length === 0 ? <Empty what="asset flows" /> : (
            <table className="w-full text-left text-xs">
              <thead><tr className="text-zinc-500">{["Asset", "Source", "Destination", "Trigger", "Authority", "Constraint"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
              <tbody>{arr("assets").map((a, i) => (
                <tr key={i} className="border-t border-zinc-800">{["asset", "source", "destination", "trigger", "authority", "constraint"].map((k) => <td key={k} className="px-2 py-1">{String(a[k])}</td>)}</tr>))}</tbody>
            </table>
          )}
        </section>
      )}
      {tab === "Authorities" && (
        <section className="grid gap-2 text-sm">
          {arr("authorities").map((a, i) => (
            <div key={i} className="rounded border border-zinc-800 p-3">
              <strong>{String(a.authority)}</strong> <span className="mono text-xs text-cyan-300">{String(a.capability)} → {String(a.target)}</span>
              <p className="text-xs text-zinc-500">blast radius {String((a as Record<string, unknown>).blast_radius || "UNKNOWN")} · conf {String(a.confidence)}</p>
            </div>))}
          {arr("authorities").length === 0 && <Empty what="authorities" />}
        </section>
      )}
      {tab === "Dependencies" && (
        <section className="overflow-x-auto rounded border border-zinc-800 text-sm">
          {arr("dependencies").length === 0 ? <Empty what="dependencies" /> : (
            <table className="w-full text-left text-xs">
              <thead><tr className="text-zinc-500">{["dependency", "type", "protocol", "role", "trust", "criticality"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
              <tbody>{arr("dependencies").map((x, i) => (
                <tr key={i} className="border-t border-zinc-800">{["dependency", "type", "protocol", "role", "trust", "criticality"].map((k) => <td key={k} className="px-2 py-1">{String(x[k])}</td>)}</tr>))}</tbody>
            </table>
          )}
        </section>
      )}
      {tab === "Specifications" && (
        <section className="space-y-2 text-sm">
          <ActionButton label="Derive specs" onRun={() => act("specs", "POST", `/api/protocols/${pid}/specs`)} disabledReason={unavailable ? "module not installed" : ""} />
          <div className="grid gap-2">
            {arr("specs").map((s, i) => (
              <div key={i} className="rounded border border-zinc-800 p-3">
                <p>{String(s.statement)}</p>
                <p className="mono text-xs text-zinc-500">{String(s.status)} · conf {String(s.confidence)}</p>
              </div>))}
            {arr("specs").length === 0 && !showOut && <Empty what="specs" />}
          </div>
        </section>
      )}
      {tab === "Invariants" && (
        <section className="space-y-2 text-sm">
          <ActionButton label="Derive invariants" onRun={() => act("invariants", "POST", `/api/protocols/${pid}/invariants`)} disabledReason={unavailable ? "module not installed" : ""} />
          <div className="grid gap-2">
            {arr("invariants").map((s, i) => (
              <div key={i} className="rounded border border-zinc-800 p-3">
                <p className="mono">{String(s.invariant)}</p>
                <p className="text-xs"><StatusBadge status={String(s.status)} /> <span className="text-zinc-500">{String(s.source)} · {String(s.tool)}</span></p>
                <p className="text-xs text-zinc-500">Fuzz pass ≠ proof.</p>
              </div>))}
            {arr("invariants").length === 0 && !showOut && <Empty what="invariants" />}
          </div>
        </section>
      )}
      {tab === "Threat Model" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <ul className="text-xs text-zinc-300"><li>Actors: user, keeper, owner, oracle</li><li>Assets: USDC, shares</li><li>Boundaries: vault ↔ oracle, proxy ↔ impl</li><li>Mitigations: timelock (missing), oracle fallback (review)</li></ul>
        </section>
      )}
      {tab === "Evidence" && (
        <section>
          <GraphView title="Evidence graph" nodes={["Finding ct-002", "Invariant totalAssets", "Fuzz seed 42", "Retest"]}
            edges={[{ from: "Finding ct-002", to: "Invariant totalAssets" }, { from: "Invariant totalAssets", to: "Fuzz seed 42" }, { from: "Fuzz seed 42", to: "Retest" }]} />
        </section>
      )}
      {tab === "Economic Twin" && (
        <section className="space-y-2 rounded border border-zinc-800 p-4 text-sm">
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-xs">
              Scenario
              <input value={scenario} onChange={(e) => setScenario(e.target.value)} className="mono ml-2 rounded bg-zinc-900 px-2 py-1" aria-label="Economic scenario" />
            </label>
            <ActionButton label="Run simulation" kind="primary" onRun={() => act("simulate", "POST", `/api/protocols/${pid}/simulate`, { scenario, seed: 42, runs: 20 })} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Run scenario" onRun={() => act("economic", "POST", `/api/protocols/${pid}/economic`, { scenario })} disabledReason={unavailable ? "module not installed" : ""} />
          </div>
          <p className="mono text-xs">config: {String((d.economic as Record<string, unknown> | undefined)?.config || "price -30%")}</p>
          <p className="text-xs">result: {String((d.economic as Record<string, unknown> | undefined)?.result || "—")}</p>
          <ul className="mt-2 text-xs text-zinc-400"><li>Price -30%</li><li>Liquidity -50%</li><li>Large withdrawal</li><li>Oracle delay</li></ul>
        </section>
      )}
      {tab === "Upgrades" && (
        <section className="space-y-2 rounded border border-zinc-800 p-4 text-sm">
          <div className="flex flex-wrap gap-2">
            <ActionButton label="Upgrade review" onRun={() => act("upgrade-review", "POST", `/api/protocols/${pid}/upgrade-review`)} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Change impact" onRun={() => act("change-impact", "POST", `/api/protocols/${pid}/regression`)} disabledReason={unavailable ? "module not installed" : ""} />
          </div>
          <p>Verdict: <StatusBadge status={String((d.upgrade as Record<string, unknown> | undefined)?.verdict || "REVIEW_REQUIRED")} /></p>
          <pre className="mono mt-2 max-h-48 overflow-auto text-xs">{JSON.stringify(d.upgrade || {}, null, 2).slice(0, 1500)}</pre>
        </section>
      )}
      {tab === "Deployment Guard" && (
        <section className="space-y-2 rounded border border-zinc-800 p-4 text-sm">
          <ActionButton label="Run deployment guard" onRun={() => act("deployment-guard", "POST", `/api/protocols/${pid}/deployment-guard`)} disabledReason={unavailable ? "module not installed" : ""} />
          <ul className="text-xs">{arr("guard").map((g, i) => <li key={i}>{String(g.item)} — {String(g.state)}</li>)}</ul>
          <p className="mt-2 text-xs text-zinc-500">No sign/broadcast button.</p>
        </section>
      )}
      {tab === "Monitoring" && (
        <section className="grid gap-2 text-sm">
          {arr("monitor").map((m, i) => (
            <div key={i} className="rounded border border-zinc-800 p-3">
              <StatusBadge status={String(m.kind)} /> <span className="text-xs">{String(m.message)}</span>
            </div>))}
          {arr("monitor").length === 0 && !status ? <Loading what="monitor" /> : arr("monitor").length === 0 && <Empty what="alerts" />}
        </section>
      )}
      {tab === "Incidents" && (
        <section className="grid gap-2 text-sm">
          {arr("incidents").map((m, i) => (
            <div key={i} className="rounded border border-zinc-800 p-3">
              <strong>{String(m.title)}</strong>
              <p className="mono text-xs text-zinc-500">{JSON.stringify(m.timeline)}</p>
            </div>))}
          {arr("incidents").length === 0 && <Empty what="incidents" />}
        </section>
      )}
      {tab === "Assurance" && (
        <section className="space-y-2 text-sm" aria-label="Assurance profile">
          <div className="flex flex-wrap gap-2">
            <ActionButton label="Refresh assurance" kind="primary" onRun={() => act("assure", "POST", `/api/protocols/${pid}/assure`)} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Regression" onRun={() => act("regression", "POST", `/api/protocols/${pid}/regression`)} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Generate report" onRun={() => act("report", "POST", `/api/protocols/${pid}/report`)} disabledReason={unavailable ? "module not installed" : ""} />
          </div>
          <div className="grid gap-2">
            {arr("assurance").map((a, i) => (
              <div key={i} className="flex items-center justify-between rounded border border-zinc-800 px-3 py-2">
                <span>{String(a.check)}</span><StatusBadge status={String(a.state)} />
              </div>))}
          </div>
          <p className="text-xs text-zinc-500">Stale reason: {String((d.freshness as Record<string, unknown> | undefined)?.reason || "—")}. No single misleading score.</p>
          {outLabel === "report" && <ReportViewer reports={[{ id: `${pid}-report`, kind: "markdown", title: `Protocol report (${pid})` }]} />}
        </section>
      )}
      {showOut && (
        <pre className="mono max-h-64 overflow-auto whitespace-pre-wrap rounded border border-zinc-800 p-2 text-xs">{outLabel}: {showOut}</pre>
      )}
    </div>
  );
}
