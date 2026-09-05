"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { FindingCard, type SharedFinding } from "@/components/FindingCard";
import { ReportViewer } from "@/components/ReportViewer";
import { GraphView } from "@/components/GraphView";
import { ActionButton, Empty, ErrorNote, Facts, Loading } from "@/components/Ops";

const TABS = ["Overview", "Engagements", "Browser", "Live Traffic", "API Map", "Findings", "Simulations", "Impact", "Remediation", "Reports"] as const;

export default function SecurityPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [engs, setEngs] = useState<Record<string, unknown>[]>([]);
  const [engId, setEngId] = useState("eng-demo");
  const [traffic, setTraffic] = useState<Record<string, unknown>[]>([]);
  const [apiMap, setApiMap] = useState<Record<string, unknown>[]>([]);
  const [findings, setFindings] = useState<SharedFinding[]>([]);
  const [sims, setSims] = useState<Record<string, unknown>[]>([]);
  const [reports, setReports] = useState<{ id: string; kind: string; title: string; artifact_id?: string }[]>([]);
  const [browser, setBrowser] = useState<Record<string, unknown>>({});
  const [err, setErr] = useState<unknown>("");
  const [out, setOut] = useState("");
  const [form, setForm] = useState({ id: "", name: "", target_url: "", scope: "", trusted_auth_host: "", auth_mode: "none" });
  const [check, setCheck] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const st = await api<Record<string, unknown>>("/api/security/status");
      setStatus(st);
    } catch (e) {
      setErr(e);
      return;
    }
    try {
      const list = await api<Record<string, unknown>[]>("/api/security/engagements");
      setEngs(list);
      if (list.length && !list.some((e) => String(e.id) === engId)) setEngId(String(list[0].id));
    } catch { /* keep previous */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
    api<SharedFinding[]>("/api/security/findings").then(setFindings).catch(() => {});
    api<Record<string, unknown>[]>("/api/security/simulations").then(setSims).catch(() => {});
    api<{ id: string; kind: string; title: string; artifact_id?: string }[]>(`/api/security/reports`).then(setReports).catch(() => {});
    api<Record<string, unknown>>("/api/security/browser").then(setBrowser).catch(() => {});
  }, [load]);

  async function loadEngagementData(id: string) {
    setErr("");
    try {
      const [t, m] = await Promise.all([
        api<Record<string, unknown>[]>(`/api/security/engagements/${id}/traffic`),
        api<Record<string, unknown>[]>(`/api/security/engagements/${id}/api-map`),
      ]);
      setTraffic(t);
      setApiMap(m);
    } catch (e) {
      setErr(e);
    }
  }

  useEffect(() => {
    if (engId) loadEngagementData(engId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [engId]);

  async function runOp(label: string, fn: () => Promise<unknown>) {
    setErr("");
    setOut(`${label}…`);
    try {
      const r = await fn();
      setOut(`${label}: done — ${JSON.stringify(r).slice(0, 600)}`);
      load();
      if (engId) loadEngagementData(engId);
      setFindings(await api<SharedFinding[]>("/api/security/findings").catch(() => findings));
    } catch (e) {
      setErr(e);
      setOut("");
    }
  }

  const unavailable = !status || (status as { state?: string }).state === "NOT_INSTALLED";

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Security</h1>
      {err && !status ? (
        <ErrorNote error={err} onRetry={load} />
      ) : err ? (
        <ErrorNote error={err} />
      ) : null}
      {out && <p className="mono text-xs text-zinc-400">{out}</p>}
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <label>
          Engagement{" "}
          <select value={engId} onChange={(e) => setEngId(e.target.value)} className="rounded bg-zinc-900 px-2 py-1" aria-label="Active engagement">
            {engs.map((e) => (
              <option key={String(e.id)} value={String(e.id)}>{String(e.name || e.id)}</option>
            ))}
            <option value={engId}>{engId}</option>
          </select>
        </label>
      </div>
      <div role="tablist" aria-label="Security sections" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            className={`rounded border px-2 py-1 text-sm ${tab === t ? "border-cyan-500 text-white" : "border-zinc-800 text-zinc-400"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && (
        <section aria-label="Security overview" className="rounded border border-zinc-800 p-4 text-sm">
          {!status ? <p className="text-zinc-500">Not installed</p> : (
            <ul className="grid gap-2 md:grid-cols-2">
              <li>AppSec status: <StatusBadge status={String(status.state || "UNKNOWN")} /></li>
              <li>Active engagement: <span className="mono">{String(status.active_engagement || "—")}</span></li>
              <li>Scope: {String(status.target_scope || "—")}</li>
              <li>Endpoints: <span className="mono">{String(status.api_endpoints ?? "—")}</span></li>
              <li>Open findings: <span className="mono">{String(status.open_findings ?? "—")}</span></li>
              <li>Verified fixes: <span className="mono">{String(status.verified_fixes ?? "—")}</span></li>
              <li>Latest simulation: <span className="mono">{String(status.latest_simulation || "—")}</span></li>
              <li>Latest report: <span className="mono">{String(status.latest_report || "—")}</span></li>
            </ul>
          )}
        </section>
      )}

      {tab === "Engagements" && (
        <section aria-label="Engagements" className="space-y-3">
          <form
            className="grid gap-2 rounded border border-zinc-800 p-3 text-sm md:grid-cols-3"
            onSubmit={(e) => e.preventDefault()}
          >
            <h2 className="font-semibold md:col-span-3">New engagement</h2>
            {([["id", "Engagement ID"], ["name", "Name"], ["target_url", "Target URL"], ["scope", "Scope"], ["trusted_auth_host", "Trusted auth host"], ["auth_mode", "Auth mode"]] as const).map(([k, label]) => (
              <label key={k} className="block">
                {label}
                <input value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                  className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label={label} />
              </label>
            ))}
            <div className="md:col-span-3">
              <ActionButton label="Create" kind="primary" onRun={() => api("/api/security/engagements", { method: "POST", body: JSON.stringify(form) }).then(() => { setOut("Create engagement: done"); load(); })} disabledReason={!form.id ? "engagement ID required" : ""} />
            </div>
          </form>
          <div className="grid gap-2">
            {engs.map((e) => (
              <div key={String(e.id)} className="rounded border border-zinc-800 p-3 text-sm" data-testid={`eng-${String(e.id)}`}>
                <div className="flex items-center justify-between">
                  <strong>{String(e.name)}</strong>
                  <StatusBadge status={String(e.status)} />
                </div>
                <p className="text-zinc-400">{String(e.scope_summary)}</p>
                <p className="mono text-xs text-zinc-500">findings {String(e.finding_count)} · report {String(e.report_status)}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <ActionButton label="Open" onRun={async () => { setEngId(String(e.id)); setTab("Findings"); }} />
                  <ActionButton label="Run Audit" onRun={() => runOp("Audit", () => api(`/api/security/engagements/${String(e.id)}/audit`, { method: "POST", body: "{}" }))} disabledReason={unavailable ? "module not installed" : ""} />
                  <ActionButton label="Activate" onRun={() => runOp("Activate", () => api(`/api/security/engagements/${String(e.id)}/activate`, { method: "POST", body: "{}" }))} />
                  <ActionButton label="Close" kind="danger" onRun={() => runOp("Close", () => api(`/api/security/engagements/${String(e.id)}/close`, { method: "POST", body: "{}" }))} />
                </div>
              </div>
            ))}
            {engs.length === 0 && <Empty what={unavailable ? "engagements (module not installed)" : "engagements"} />}
          </div>
        </section>
      )}

      {tab === "Browser" && (
        <section aria-label="Browser" className="rounded border border-zinc-800 p-4 text-sm">
          {!Object.keys(browser).length ? <Loading what="browser status" /> : (
            <Facts facts={Object.entries(browser).slice(0, 12).map(([k, v]) => [k, String(v ?? "—")])} />
          )}
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <ActionButton label="Launch headless" onRun={() => runOp("Launch browser", () => api(`/api/security/engagements/${engId}/browser/launch`, { method: "POST", body: JSON.stringify({ headed: false }) }))} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Launch headed" onRun={() => runOp("Launch browser", () => api(`/api/security/engagements/${engId}/browser/launch`, { method: "POST", body: JSON.stringify({ headed: true }) }))} disabledReason={unavailable ? "module not installed" : ""} />
            <ActionButton label="Start capture" onRun={() => runOp("Capture", () => api(`/api/security/engagements/${engId}/capture`, { method: "POST", body: JSON.stringify({ scenario: "normal-api" }) }))} disabledReason={unavailable ? "module not installed" : ""} />
          </div>
          <p className="mt-2 text-xs text-zinc-500">Remote-debug port never exposed.</p>
        </section>
      )}

      {tab === "Live Traffic" && (
        <section aria-label="Live traffic" className="overflow-x-auto rounded border border-zinc-800 text-sm">
          <table className="w-full text-left text-xs">
            <thead><tr className="text-zinc-500">{["time", "method", "host", "path", "status", "type", "auth", "duration", "flow"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
            <tbody>
              {traffic.slice(0, 100).map((t, i) => (
                <tr key={i} className="border-t border-zinc-800">
                  <td className="mono px-2 py-1">{String(t.ts)}</td>
                  <td className="px-2 py-1">{String(t.method)}</td>
                  <td className="px-2 py-1">{String(t.host)}</td>
                  <td className="mono px-2 py-1">{String(t.path)}</td>
                  <td className="px-2 py-1">{String(t.status)}</td>
                  <td className="px-2 py-1">{String(t.kind)}</td>
                  <td className="px-2 py-1">{String(t.auth)}</td>
                  <td className="px-2 py-1">{String(t.duration_ms)}ms</td>
                  <td className="px-2 py-1">{String(t.flow)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {traffic.length === 0 && <Empty what="captured traffic" />}
          <p className="p-2 text-xs text-zinc-500">Headers/bodies redacted by backend. Bounded to 100 rows.</p>
        </section>
      )}

      {tab === "API Map" && (
        <section aria-label="API map" className="space-y-3 text-sm">
          <div className="overflow-x-auto rounded border border-zinc-800">
            <table className="w-full text-left text-xs">
              <thead><tr className="text-zinc-500">{["host", "route", "method", "auth", "Guest", "User", "Manager", "Admin"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
              <tbody>
                {apiMap.map((r, i) => {
                  const roles = (r.roles || {}) as Record<string, number>;
                  return (
                    <tr key={i} className="border-t border-zinc-800">
                      <td className="px-2 py-1">{String(r.host)}</td>
                      <td className="mono px-2 py-1">{String(r.route)}</td>
                      <td className="px-2 py-1">{String(r.method)}</td>
                      <td className="px-2 py-1">{String(r.auth)}</td>
                      {(["Guest", "User", "Manager", "Admin"] as const).map((role) => (
                        <td key={role} className={`mono px-2 py-1 ${roles[role] >= 400 ? "text-amber-300" : "text-emerald-300"}`}>{roles[role] ?? "—"}</td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <GraphView title="API map graph" nodes={apiMap.map((r) => String(r.route))} edges={apiMap.map((r) => ({ from: String(r.host), to: `${r.method} ${r.route}` }))} />
        </section>
      )}

      {tab === "Findings" && (
        <section aria-label="Findings" className="grid gap-2">
          {findings.map((f) => (
            <FindingCard
              key={f.id}
              finding={f}
              actions={
                <>
                  <ActionButton label="Retest" onRun={() => runOp(`Retest ${f.id}`, () => api("/api/security/retest", { method: "POST", body: JSON.stringify({ ref: f.id, engagement: engId }) }))} disabledReason={unavailable ? "module not installed" : ""} />
                  <Link href={`/tasks/new?repo=/srv/sklab/repos/demo`} className="rounded border border-zinc-700 px-2 py-1">
                    Request remediation
                  </Link>
                </>
              }
            />
          ))}
          {findings.length === 0 && <Empty what="findings" />}
        </section>
      )}

      {tab === "Simulations" && (
        <section aria-label="Simulations" className="space-y-3 text-sm">
          <form className="flex flex-wrap items-end gap-2 rounded border border-zinc-800 p-3"
            onSubmit={(e) => e.preventDefault()}>
            <label className="text-xs">
              Bounded check (empty = all)
              <input value={check} onChange={(e) => setCheck(e.target.value)} className="ml-2 rounded bg-zinc-900 px-2 py-1" aria-label="Simulation check" placeholder="ROLE_BOUNDARY_CHECK" />
            </label>
            <ActionButton label="Run simulation" kind="primary" onRun={() => runOp("Simulation", () => api(`/api/security/engagements/${engId}/simulate`, { method: "POST", body: JSON.stringify({ check }) }))} disabledReason={unavailable ? "module not installed" : ""} />
          </form>
          <div className="overflow-x-auto rounded border border-zinc-800">
            <table className="w-full text-left text-xs">
              <thead><tr className="text-zinc-500">{["simulation", "target", "role", "result", "requests", "duration", "impact"].map((h) => <th key={h} className="px-2 py-1">{h}</th>)}</tr></thead>
              <tbody>
                {sims.map((s, i) => (
                  <tr key={i} className="border-t border-zinc-800">
                    <td className="mono px-2 py-1">{String(s.simulation)}</td>
                    <td className="px-2 py-1">{String(s.target)}</td>
                    <td className="px-2 py-1">{String(s.role)}</td>
                    <td className="px-2 py-1"><StatusBadge status={String(s.result)} /></td>
                    <td className="px-2 py-1">{String(s.requests)}</td>
                    <td className="px-2 py-1">{String(s.duration_ms)}ms</td>
                    <td className="px-2 py-1">{String(s.impact)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="p-2 text-xs text-zinc-500">Bounded safe checks only — no destructive controls.</p>
        </section>
      )}

      {tab === "Impact" && (
        <section aria-label="Impact" className="grid gap-2">
          {findings.map((f) => (
            <div key={f.id} className="rounded border border-zinc-800 p-3 text-sm">
              <strong>{f.title}</strong>
              <dl className="mt-1 grid grid-cols-2 gap-1 text-xs md:grid-cols-3">
                {Object.entries((f as { impact?: Record<string, string> }).impact || {}).map(([k, v]) => (
                  <div key={k} className="flex justify-between rounded border border-zinc-800 px-2 py-1">
                    <dt className="text-zinc-500">{k}</dt><dd className="mono">{v}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-1 text-xs text-zinc-500">Impact provided by backend; never computed client-side.</p>
            </div>
          ))}
        </section>
      )}

      {tab === "Remediation" && (
        <section aria-label="Remediation" className="rounded border border-zinc-800 p-4 text-sm">
          <ol className="mono text-xs text-zinc-300">
            <li>Finding → Plan → Orchestrator → Patch → PatchBench → Re-test</li>
          </ol>
          <p className="mt-2 text-xs text-zinc-400">
            Pick a finding, request remediation (opens a prefilled task), then retest the exact
            finding from the Findings tab.
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {findings.slice(0, 5).map((f) => (
              <Link key={f.id} href="/tasks/new" className="rounded border border-zinc-700 px-2 py-1">
                Fix {f.id}
              </Link>
            ))}
          </div>
          <p className="mt-2 text-xs text-zinc-500">Never auto-applies or pushes.</p>
        </section>
      )}

      {tab === "Reports" && (
        <section aria-label="Reports" className="space-y-3">
          <ActionButton label="Generate report" onRun={() => runOp("Report", () => api(`/api/security/engagements/${engId}/report`, { method: "POST", body: "{}" }).then(async (r) => { setReports(await api<typeof reports>(`/api/security/reports`).catch(() => reports)); return r; }))} disabledReason={unavailable ? "module not installed" : ""} />
          <ReportViewer reports={reports} />
          <p className="mt-2 text-xs text-zinc-500">Safe artifact IDs only; no filesystem paths.</p>
        </section>
      )}
    </div>
  );
}
