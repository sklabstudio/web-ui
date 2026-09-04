"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { GraphView } from "@/components/GraphView";

const TABS = ["Overview", "Architecture", "Asset Flows", "Authorities", "Dependencies", "Specifications", "Invariants", "Threat Model", "Evidence", "Economic Twin", "Upgrades", "Deployment Guard", "Monitoring", "Incidents", "Assurance"] as const;

export default function ProtocolsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [list, setList] = useState<Record<string, unknown>[]>([]);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api<Record<string, unknown>>("/api/protocols/status").then(setStatus).catch(() => {});
    api<Record<string, unknown>[]>("/api/protocols").then((p) => {
      setList(p);
      if (p[0]) api<Record<string, unknown>>(`/api/protocols/${p[0].id}`).then(setDetail).catch(() => {});
    }).catch(() => {});
  }, []);

  const d = (detail || {}) as Record<string, unknown>;
  const arr = (k: string) => (Array.isArray(d[k]) ? (d[k] as Record<string, unknown>[]) : []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Protocols</h1>
      <p className="rounded border border-zinc-800 p-2 text-xs text-zinc-500">SIMULATION ONLY — no live transactions. Private implementation stays hidden.</p>
      <div role="tablist" aria-label="Protocol sections" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
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
          <table className="w-full text-left text-xs">
            <thead><tr className="text-zinc-500">{["Asset", "Source", "Destination", "Trigger", "Authority", "Constraint"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
            <tbody>{arr("assets").map((a, i) => (
              <tr key={i} className="border-t border-zinc-800">{["asset", "source", "destination", "trigger", "authority", "constraint"].map((k) => <td key={k} className="px-2 py-1">{String(a[k])}</td>)}</tr>))}</tbody>
          </table>
        </section>
      )}
      {tab === "Authorities" && (
        <section className="grid gap-2 text-sm">
          {arr("authorities").map((a, i) => (
            <div key={i} className="rounded border border-zinc-800 p-3">
              <strong>{String(a.authority)}</strong> <span className="mono text-xs text-cyan-300">{String(a.capability)} → {String(a.target)}</span>
              <p className="text-xs text-zinc-500">blast radius {String((a as Record<string, unknown>).blast_radius || "UNKNOWN")} · conf {String(a.confidence)}</p>
            </div>))}
          {arr("authorities").length === 0 && <p className="text-zinc-500">No data.</p>}
        </section>
      )}
      {tab === "Dependencies" && (
        <section className="overflow-x-auto rounded border border-zinc-800 text-sm">
          <table className="w-full text-left text-xs">
            <thead><tr className="text-zinc-500">{["dependency", "type", "protocol", "role", "trust", "criticality"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
            <tbody>{arr("dependencies").map((x, i) => (
              <tr key={i} className="border-t border-zinc-800">{["dependency", "type", "protocol", "role", "trust", "criticality"].map((k) => <td key={k} className="px-2 py-1">{String(x[k])}</td>)}</tr>))}</tbody>
          </table>
        </section>
      )}
      {tab === "Specifications" && (
        <section className="grid gap-2 text-sm">
          {arr("specs").map((s, i) => (
            <div key={i} className="rounded border border-zinc-800 p-3">
              <p>{String(s.statement)}</p>
              <p className="mono text-xs text-zinc-500">{String(s.status)} · conf {String(s.confidence)}</p>
            </div>))}
        </section>
      )}
      {tab === "Invariants" && (
        <section className="grid gap-2 text-sm">
          {arr("invariants").map((s, i) => (
            <div key={i} className="rounded border border-zinc-800 p-3">
              <p className="mono">{String(s.invariant)}</p>
              <p className="text-xs"><StatusBadge status={String(s.status)} /> <span className="text-zinc-500">{String(s.source)} · {String(s.tool)}</span></p>
              <p className="text-xs text-zinc-500">Fuzz pass ≠ proof.</p>
            </div>))}
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
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <p className="mono text-xs">config: {String((d.economic as Record<string, unknown> | undefined)?.config || "price -30%")}</p>
          <p className="text-xs">result: {String((d.economic as Record<string, unknown> | undefined)?.result || "—")}</p>
          <ul className="mt-2 text-xs text-zinc-400"><li>Price -30%</li><li>Liquidity -50%</li><li>Large withdrawal</li><li>Oracle delay</li></ul>
        </section>
      )}
      {tab === "Upgrades" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <p>Verdict: <StatusBadge status={String((d.upgrade as Record<string, unknown> | undefined)?.verdict || "REVIEW_REQUIRED")} /></p>
          <pre className="mono mt-2 overflow-auto text-xs">{JSON.stringify(d.upgrade || {}, null, 2).slice(0, 1500)}</pre>
        </section>
      )}
      {tab === "Deployment Guard" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
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
          {arr("monitor").length === 0 && <p className="text-zinc-500">No alerts.</p>}
        </section>
      )}
      {tab === "Incidents" && (
        <section className="grid gap-2 text-sm">
          {arr("incidents").map((m, i) => (
            <div key={i} className="rounded border border-zinc-800 p-3">
              <strong>{String(m.title)}</strong>
              <p className="mono text-xs text-zinc-500">{JSON.stringify(m.timeline)}</p>
            </div>))}
        </section>
      )}
      {tab === "Assurance" && (
        <section className="grid gap-2 text-sm" aria-label="Assurance profile">
          {arr("assurance").map((a, i) => (
            <div key={i} className="flex items-center justify-between rounded border border-zinc-800 px-3 py-2">
              <span>{String(a.check)}</span><StatusBadge status={String(a.state)} />
            </div>))}
          <p className="text-xs text-zinc-500">Stale reason: {String((d.freshness as Record<string, unknown> | undefined)?.reason || "—")}. No single misleading score.</p>
        </section>
      )}
    </div>
  );
}
