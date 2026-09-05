"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { FindingCard, type SharedFinding } from "@/components/FindingCard";
import { ReportViewer } from "@/components/ReportViewer";
import { GraphView } from "@/components/GraphView";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

const TABS = ["Overview", "Projects", "Contracts", "Tools", "Analysis", "Tests", "Fuzz", "Invariants", "Authorities", "Standards", "Upgrades", "Gas", "Reports"] as const;

export default function ContractsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [projects, setProjects] = useState<Record<string, unknown>[]>([]);
  const [pid, setPid] = useState("proj-demo");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [findings, setFindings] = useState<SharedFinding[]>([]);
  const [tools, setTools] = useState<Record<string, unknown>[]>([]);
  const [out, setOut] = useState<Record<string, unknown> | null>(null);
  const [outLabel, setOutLabel] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState<unknown>("");
  const [create, setCreate] = useState({ id: "", kind: "custom" });
  const [imp, setImp] = useState({ id: "", filename: "Custom.sol", source: "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.24;\ncontract Custom {}\n" });
  const [ref, setRef] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      setStatus(await api<Record<string, unknown>>("/api/contracts/status"));
    } catch (e) { setErr(e); return; }
    try {
      const p = await api<Record<string, unknown>[]>("/api/contracts/projects");
      setProjects(p);
      if (p.length && !p.some((x) => String(x.id) === pid)) setPid(String(p[0].id));
    } catch { /* keep */ }
    try {
      setFindings(await api<SharedFinding[]>("/api/contracts/findings"));
    } catch { /* keep */ }
    try {
      setTools(await api<Record<string, unknown>[]>("/api/contracts/tools"));
    } catch { /* keep */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!pid) return;
    api<Record<string, unknown>>(`/api/contracts/projects/${pid}`).then(setDetail).catch(() => setDetail(null));
  }, [pid]);

  async function runOp(label: string, method: string, path: string, body?: unknown) {
    setErr("");
    setMsg(`${label}…`);
    try {
      const r = await api<Record<string, unknown>>(path, { method, body: body === undefined ? "{}" : JSON.stringify(body) });
      setOut(r);
      setOutLabel(label);
      setMsg(`${label}: ok`);
      load();
    } catch (e) {
      setErr(e);
      setMsg("");
    }
  }

  const run = (kind: string) => runOp(kind, "POST", `/api/contracts/projects/${pid}/${kind}`);
  const inventory = (detail?.inventory || []) as Record<string, unknown>[];
  const unavailable = !status || String(status.state) === "NOT_INSTALLED";
  const isMock = Boolean(status?.mock);
  const showOut = out ? JSON.stringify(out, null, 2).slice(0, 4000) : "";
  const graph = (out?.graph as Record<string, unknown> | undefined) || out || {};

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Contracts</h1>
      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {msg && <p className="text-xs text-zinc-400">{msg}</p>}
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <label>
          Project{" "}
          <select value={pid} onChange={(e) => setPid(e.target.value)} className="rounded bg-zinc-900 px-2 py-1" aria-label="Contract project">
            {projects.map((p) => (
              <option key={String(p.id)} value={String(p.id)}>{String(p.name || p.id)}</option>
            ))}
            <option value={pid}>{pid}</option>
          </select>
        </label>
      </div>
      <div role="tablist" aria-label="Contracts sections" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => { setTab(t); setOut(null); setOutLabel(""); }}
            className={`rounded border px-2 py-1 text-sm ${tab === t ? "border-cyan-500 text-white" : "border-zinc-800 text-zinc-400"}`}>{t}</button>
        ))}
      </div>

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
        <section className="space-y-3">
          <form className="grid gap-2 rounded border border-zinc-800 p-3 text-sm md:grid-cols-3" onSubmit={(e) => e.preventDefault()}>
            <h2 className="font-semibold md:col-span-3">New project (from template)</h2>
            <label className="block">ID
              <input value={create.id} onChange={(e) => setCreate({ ...create, id: e.target.value })}
                className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Project ID" />
            </label>
            <label className="block">Kind
              <select value={create.kind} onChange={(e) => setCreate({ ...create, kind: e.target.value })}
                className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Project kind">
                {(["custom", "token", "nft", "vault", "staking"] as const).map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </select>
            </label>
            <div className="flex items-end">
              <ActionButton label="Create" kind="primary"
                onRun={() => runOp("create", "POST", "/api/contracts/projects", create)}
                disabledReason={!create.id ? "project ID required" : unavailable ? "module not installed" : ""} />
            </div>
          </form>
          <form className="grid gap-2 rounded border border-zinc-800 p-3 text-sm" onSubmit={(e) => e.preventDefault()}>
            <h2 className="font-semibold">Import (paste Solidity)</h2>
            <div className="grid gap-2 md:grid-cols-2">
              <label className="block">ID
                <input value={imp.id} onChange={(e) => setImp({ ...imp, id: e.target.value })}
                  className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Import ID" />
              </label>
              <label className="block">Filename
                <input value={imp.filename} onChange={(e) => setImp({ ...imp, filename: e.target.value })}
                  className="mt-1 block w-full rounded bg-zinc-900 p-2 mono text-xs" aria-label="Filename" />
              </label>
            </div>
            <label className="block">Source
              <textarea value={imp.source} onChange={(e) => setImp({ ...imp, source: e.target.value })} rows={8}
                className="mono mt-1 block w-full rounded bg-zinc-900 p-2 text-xs" aria-label="Contract source" />
            </label>
            <div>
              <ActionButton label="Import" kind="primary"
                onRun={() => runOp("import", "POST", "/api/contracts/projects/import", { id: imp.id, files: { [imp.filename]: imp.source } })}
                disabledReason={!imp.id ? "project ID required" : unavailable ? "module not installed" : ""} />
            </div>
          </form>
          <div className="grid gap-2">
            {projects.map((p) => (
              <div key={String(p.id)} className="rounded border border-zinc-800 p-3 text-sm" data-testid={`project-${String(p.id)}`}>
                <div className="flex items-center justify-between"><strong>{String(p.name)}</strong><StatusBadge status={String(p.status)} /></div>
                <p className="text-zinc-400">{String(p.chain)} · {String(p.toolchain)} · {String(p.compiler)}</p>
                <div className="mt-1 flex flex-wrap gap-2 text-xs">
                  {(["compile", "test", "analyze", "fuzz", "invariants"] as const).map((k) => (
                    <ActionButton key={k} label={k} onRun={() => runOp(k, "POST", `/api/contracts/projects/${String(p.id)}/${k}`)} />
                  ))}
                </div>
                <p className="mt-1 text-xs text-zinc-500">No deployment button — build/test only.</p>
              </div>
            ))}
            {projects.length === 0 && <Empty what={unavailable ? "projects (module not installed)" : "projects"} />}
          </div>
        </section>
      )}
      {tab === "Contracts" && (
        <section className="overflow-x-auto rounded border border-zinc-800 text-sm">
          <table className="w-full text-left text-xs">
            <thead><tr className="text-zinc-500">{["Contract", "Source", "Type", "Standard", "Upgradeability", "Authorities", "Functions"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
            <tbody>{inventory.map((c, i) => (
              <tr key={i} className="border-t border-zinc-800">
                <td className="px-2 py-1">{String(c.name ?? `contract-${i}`)}</td><td className="mono px-2 py-1">{String(c.source ?? "—")}</td>
                <td className="px-2 py-1">{String(c.kind ?? "—")}</td><td className="px-2 py-1">{String(c.standard ?? "—")}</td>
                <td className="px-2 py-1">{String(c.upgradeability ?? "—")}</td><td className="px-2 py-1">{String(((c.authorities as string[]) || []).join(", ") || "—")}</td>
                <td className="px-2 py-1">{String(c.functions ?? "—")}</td>
              </tr>))}</tbody>
          </table>
          {inventory.length === 0 && <Empty what="contracts in inventory" />}
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
          <p className="p-2 text-xs text-zinc-500">Optional tools show OPTIONAL/UNAVAILABLE honestly and never break the page.</p>
        </section>
      )}
      {tab === "Analysis" && (
        <section className="space-y-2">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <ActionButton label="Run analysis" kind="primary" onRun={() => run("analyze")} />
            <label className="text-xs">
              Finding ref
              <input value={ref} onChange={(e) => setRef(e.target.value)} className="mono ml-2 rounded bg-zinc-900 px-2 py-1" aria-label="Finding ref" placeholder="ct-001" />
            </label>
            <ActionButton label="Prepare fix" onRun={() => runOp("remediate", "POST", `/api/contracts/projects/${pid}/remediate`, { ref })} disabledReason={!ref ? "finding ref required" : ""} />
            <ActionButton label="Verify fix" onRun={() => runOp("retest", "POST", `/api/contracts/projects/${pid}/retest`, { ref })} disabledReason={!ref ? "finding ref required" : ""} />
          </div>
          <div className="grid gap-2">{findings.map((f) => <FindingCard key={f.id} finding={f} />)}
            {findings.length === 0 && <Empty what="findings" />}</div>
          {showOut && <pre className="mono max-h-64 overflow-auto whitespace-pre-wrap rounded border border-zinc-800 p-2 text-xs">{outLabel}: {showOut}</pre>}
        </section>
      )}
      {tab === "Tests" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <ActionButton label="Run tests" kind="primary" onRun={() => run("test")} />
          {showOut ? <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">{showOut}</pre> : <p className="mt-2 text-xs text-zinc-500">total/passed/failed shown after run; failures show bounded logs.</p>}
        </section>
      )}
      {tab === "Fuzz" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <ActionButton label="Run fuzz" kind="primary" onRun={() => run("fuzz")} />
          {showOut ? <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">{showOut}</pre> : <p className="mt-2 text-xs text-zinc-500">Seed, runs and counterexamples shown after run.</p>}
        </section>
      )}
      {tab === "Invariants" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <ActionButton label="Run invariants" kind="primary" onRun={() => run("invariants")} />
          {showOut ? <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">{showOut}</pre> : <p className="mt-2 text-xs text-zinc-500">Sources labeled EXPLICIT / STANDARD_TEMPLATE / PRIVATE_MINED when provided.</p>}
        </section>
      )}
      {tab === "Authorities" && (
        <section className="space-y-2">
          <ActionButton label="Load authority graph" onRun={async () => {
            const g = await api<Record<string, unknown>>(`/api/contracts/projects/${pid}/graph?kind=authority`);
            setOut(g);
            setOutLabel("authority graph");
          }} />
           <GraphView title="Authority graph" nodes={(graph.nodes as string[]) || []} edges={((graph.edges as string[][]) || []).map((e) => ({ from: e[0], to: e[1] }))} />
        </section>
      )}
      {tab === "Standards" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <ul className="text-xs"><li>ERC-20 — HIGH (transfer/approve events)</li><li>ERC-4626 — MEDIUM (vault shares)</li><li>UUPS — HIGH (EIP-1967 slots)</li><li>Ownable — HIGH</li></ul>
        </section>
      )}
      {tab === "Upgrades" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <ActionButton label="Run upgrade review" onRun={() => runOp("upgrade-review", "POST", `/api/contracts/projects/${pid}/upgrade-review`)} />
           {showOut ? <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">{showOut}</pre> : isMock ? (
             <>
               <p className="mt-2">Verdict: <StatusBadge status="REVIEW_REQUIRED" /></p>
               <ul className="mt-2 text-xs text-zinc-400"><li>storage: no collision</li><li>ABI: 1 added event</li><li>authorities: unchanged</li></ul>
             </>
           ) : <p className="mt-2 text-xs text-zinc-500">No upgrade review has run for this project.</p>}
          <div className="mt-2 flex flex-wrap gap-2">
            <ActionButton label="Storage layout" onRun={async () => { const r = await api(`/api/contracts/projects/${pid}/storage`); setOut(r as Record<string, unknown>); setOutLabel("storage"); }} />
            <ActionButton label="ABI diff" onRun={async () => { const r = await api(`/api/contracts/projects/${pid}/abi-diff`); setOut(r as Record<string, unknown>); setOutLabel("abi-diff"); }} />
            <ActionButton label="Threat model" onRun={async () => { const r = await api(`/api/contracts/projects/${pid}/threat-model`); setOut(r as Record<string, unknown>); setOutLabel("threat-model"); }} />
          </div>
        </section>
      )}
      {tab === "Gas" && (
        <section className="rounded border border-zinc-800 p-4 text-sm">
          <div className="flex flex-wrap gap-2">
            <ActionButton label="Gas review" onRun={() => runOp("gas", "POST", `/api/contracts/projects/${pid}/gas`)} />
            <ActionButton label="Coverage" onRun={() => runOp("coverage", "POST", `/api/contracts/projects/${pid}/coverage`)} />
          </div>
          {showOut ? <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">{showOut}</pre> : <p className="mt-2 text-xs text-zinc-400">Hotspots shown after run. No dollar conversion without backend price context.</p>}
        </section>
      )}
      {tab === "Reports" && (
        <section className="space-y-2">
          <ActionButton label="Generate report" onRun={() => runOp("report", "POST", `/api/contracts/projects/${pid}/report`)} />
           <ReportViewer reports={((out?.reports as { id: string; kind: string; title: string; artifact_id?: string; content?: string }[]) || (isMock ? [{ id: "ct-rep-001", kind: "markdown", title: "Contract report (fixture)", artifact_id: "artifact-rep-ct-001" }] : []))} />
           {out && !Array.isArray(out?.reports) ? <pre className="mono max-h-64 overflow-auto whitespace-pre-wrap text-xs">{showOut}</pre> : null}
        </section>
      )}
      {!["Analysis", "Tests", "Fuzz", "Invariants", "Upgrades", "Gas", "Reports"].includes(tab) && showOut && (
        <pre className="mono max-h-64 overflow-auto whitespace-pre-wrap rounded border border-zinc-800 p-2 text-xs">{outLabel}: {showOut}</pre>
      )}
    </div>
  );
}
