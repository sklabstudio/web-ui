"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { FindingCard, type SharedFinding } from "@/components/FindingCard";
import { ReportViewer } from "@/components/ReportViewer";
import { GraphView } from "@/components/GraphView";

const TABS = ["Overview", "Projects", "Contracts", "Tools", "Analysis", "Tests", "Fuzz", "Invariants", "Authorities", "Standards", "Upgrades", "Gas", "Reports"] as const;

export default function ContractsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [projects, setProjects] = useState<Record<string, unknown>[]>([]);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [findings, setFindings] = useState<SharedFinding[]>([]);
  const [tools, setTools] = useState<Record<string, unknown>[]>([]);
  const [testRes, setTestRes] = useState<Record<string, unknown> | null>(null);
  const [fuzz, setFuzz] = useState<Record<string, unknown> | null>(null);
  const [invs, setInvs] = useState<Record<string, unknown> | null>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api<Record<string, unknown>>("/api/contracts/status").then(setStatus).catch(() => {});
    api<Record<string, unknown>[]>("/api/contracts/projects").then((p) => {
      setProjects(p);
      if (p[0]) api<Record<string, unknown>>(`/api/contracts/projects/${p[0].id}`).then(setDetail).catch(() => {});
    }).catch(() => {});
    api<SharedFinding[]>("/api/contracts/findings").then(setFindings).catch(() => {});
    api<Record<string, unknown>[]>("/api/contracts/tools").then(setTools).catch(() => {});
  }, []);

  async function run(kind: string) {
    setMsg("");
    try {
      const r = await api<Record<string, unknown>>(`/api/contracts/projects/proj-demo/${kind}`, { method: "POST", body: "{}" });
      if (kind === "test") setTestRes(r);
      if (kind === "fuzz") setFuzz(r);
      if (kind === "invariants") setInvs(r);
      setMsg(`${kind}: ok`);
    } catch (e) { setMsg(String(e)); }
  }

  const inventory = (detail?.inventory || []) as Record<string, unknown>[];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Contracts</h1>
      <div role="tablist" aria-label="Contracts sections" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
            className={`rounded border px-2 py-1 text-sm ${tab === t ? "border-cyan-500 text-white" : "border-zinc-800 text-zinc-400"}`}>{t}</button>
        ))}
      </div>
      {msg && <p className="text-xs text-zinc-400">{msg}</p>}

      {tab === "Overview" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          {!status ? <p className="text-zinc-500">Not installed</p> : (
            <ul className="grid gap-2 md:grid-cols-2">
              <li>Toolkit: <StatusBadge status={String(status.state || "UNKNOWN")} /></li>
              <li>Projects: <span className="mono">{String(status.projects ?? "—")}</span></li>
              <li>Open findings: <span className="mono">{String(status.open_findings ?? "—")}</span></li>
              <li>Failing tests: <span className="mono">{String(status.failing_tests ?? "—")}</span></li>
              <li>Failing invariants: <span className="mono">{String(status.failing_invariants ?? "—")}</span></li>
              <li>Upgrade: <span className="mono">{String(status.latest_upgrade ?? "—")}</span></li>
            </ul>
          )}
        </section>
      )}
      {tab === "Projects" && (
        <section className="grid gap-2">
          {projects.map((p) => (
            <div key={String(p.id)} className="rounded border border-zinc-800 p-3 text-sm" data-testid={`project-${String(p.id)}`}>
              <div className="flex items-center justify-between"><strong>{String(p.name)}</strong><StatusBadge status={String(p.status)} /></div>
              <p className="text-zinc-400">{String(p.chain)} · {String(p.toolchain)} · {String(p.compiler)}</p>
              <div className="mt-1 flex flex-wrap gap-2 text-xs">
                {(["compile", "test", "analyze", "fuzz", "invariants"] as const).map((k) => (
                  <button key={k} onClick={() => run(k)} className="rounded border border-zinc-700 px-2 py-1">{k}</button>
                ))}
              </div>
              <p className="mt-1 text-xs text-zinc-500">No deployment button in v0.2.</p>
            </div>
          ))}
          {projects.length === 0 && <p className="text-sm text-zinc-500">Not installed</p>}
        </section>
      )}
      {tab === "Contracts" && (
        <section className="overflow-x-auto rounded border border-zinc-800 text-sm">
          <table className="w-full text-left text-xs">
            <thead><tr className="text-zinc-500">{["Contract", "Source", "Type", "Standard", "Upgradeability", "Authorities", "Functions"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
            <tbody>{inventory.map((c, i) => (
              <tr key={i} className="border-t border-zinc-800">
                <td className="px-2 py-1">{String(c.name)}</td><td className="mono px-2 py-1">{String(c.source)}</td>
                <td className="px-2 py-1">{String(c.kind)}</td><td className="px-2 py-1">{String(c.standard)}</td>
                <td className="px-2 py-1">{String(c.upgradeability)}</td><td className="px-2 py-1">{String((c.authorities as string[])?.join(", "))}</td>
                <td className="px-2 py-1">{String(c.functions)}</td>
              </tr>))}</tbody>
          </table>
        </section>
      )}
      {tab === "Tools" && (
        <section className="overflow-x-auto rounded border border-zinc-800 text-sm">
          <table className="w-full text-left text-xs">
            <thead><tr className="text-zinc-500">{["Tool", "Installed", "Version", "Status"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
            <tbody>{tools.map((t, i) => (
              <tr key={i} className="border-t border-zinc-800">
                <td className="px-2 py-1">{String(t.id)}</td><td className="px-2 py-1">{String(t.installed)}</td>
                <td className="mono px-2 py-1">{String(t.version ?? "—")}</td>
                <td className="px-2 py-1"><StatusBadge status={String(t.status)} /></td>
              </tr>))}</tbody>
          </table>
        </section>
      )}
      {tab === "Analysis" && (
        <section className="grid gap-2">{findings.map((f) => <FindingCard key={f.id} finding={f} />)}
          {findings.length === 0 && <p className="text-sm text-zinc-500">No findings.</p>}</section>
      )}
      {tab === "Tests" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <button onClick={() => run("test")} className="rounded bg-cyan-500 px-3 py-1 font-semibold text-black">Run tests</button>
          {testRes && <ul className="mt-2 text-xs"><li>Total {String(testRes.total)} · Passed {String(testRes.passed)} · Failed {String(testRes.failed)}</li></ul>}
          {!testRes && <p className="mt-2 text-xs text-zinc-500">total/passed/failed shown after run; failures show bounded logs.</p>}
        </section>
      )}
      {tab === "Fuzz" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <button onClick={() => run("fuzz")} className="rounded bg-cyan-500 px-3 py-1 font-semibold text-black">Run fuzz</button>
          {fuzz && <p className="mono mt-2 text-xs">seed {String(fuzz.seed)} · runs {String(fuzz.runs)} · counterexample: {String(fuzz.counterexample)}</p>}
        </section>
      )}
      {tab === "Invariants" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <button onClick={() => run("invariants")} className="rounded bg-cyan-500 px-3 py-1 font-semibold text-black">Run invariants</button>
          {invs && <pre className="mono mt-2 overflow-auto text-xs">{JSON.stringify(invs, null, 2).slice(0, 2000)}</pre>}
          <p className="mt-2 text-xs text-zinc-500">Sources labeled EXPLICIT / STANDARD_TEMPLATE / PRIVATE_MINED when provided.</p>
        </section>
      )}
      {tab === "Authorities" && (
        <section>
          <GraphView title="Authority graph" nodes={["Owner", "Keeper", "DemoVault", "DemoToken"]} edges={[{ from: "Owner", to: "upgrade" }, { from: "Owner", to: "pause" }, { from: "Owner", to: "mint" }, { from: "Keeper", to: "pause" }]} />
        </section>
      )}
      {tab === "Standards" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <ul className="text-xs"><li>ERC-20 — HIGH (transfer/approve events)</li><li>ERC-4626 — MEDIUM (vault shares)</li><li>UUPS — HIGH (EIP-1967 slots)</li><li>Ownable — HIGH</li></ul>
        </section>
      )}
      {tab === "Upgrades" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <p>Verdict: <StatusBadge status="REVIEW_REQUIRED" /></p>
          <ul className="mt-2 text-xs text-zinc-400"><li>storage: no collision</li><li>ABI: 1 added event</li><li>authorities: unchanged</li></ul>
        </section>
      )}
      {tab === "Gas" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <p className="text-xs text-zinc-400">Hotspots: deposit (42k), mint (31k). No dollar conversion without backend price context.</p>
        </section>
      )}
      {tab === "Reports" && (
        <section><ReportViewer reports={[{ id: "ct-rep-001", kind: "markdown", title: "Contract report (fixture)", artifact_id: "artifact-rep-ct-001" }]} /></section>
      )}
    </div>
  );
}
