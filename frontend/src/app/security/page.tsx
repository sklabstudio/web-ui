"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { FindingCard, type SharedFinding } from "@/components/FindingCard";
import { ReportViewer } from "@/components/ReportViewer";
import { GraphView } from "@/components/GraphView";

const TABS = ["Overview", "Engagements", "Browser", "Live Traffic", "API Map", "Findings", "Simulations", "Impact", "Remediation", "Reports"] as const;

export default function SecurityPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [engs, setEngs] = useState<Record<string, unknown>[]>([]);
  const [traffic, setTraffic] = useState<Record<string, unknown>[]>([]);
  const [apiMap, setApiMap] = useState<Record<string, unknown>[]>([]);
  const [findings, setFindings] = useState<SharedFinding[]>([]);
  const [sims, setSims] = useState<Record<string, unknown>[]>([]);
  const [reports, setReports] = useState<[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<Record<string, unknown>>("/api/security/status").then(setStatus).catch((e) => setErr(String(e)));
    api<Record<string, unknown>[]>("/api/security/engagements").then(setEngs).catch(() => {});
    api<Record<string, unknown>[]>("/api/security/engagements/eng-demo/traffic").then(setTraffic).catch(() => {});
    api<Record<string, unknown>[]>("/api/security/engagements/eng-demo/api-map").then(setApiMap).catch(() => {});
    api<SharedFinding[]>("/api/security/findings").then(setFindings).catch(() => {});
    api<Record<string, unknown>[]>("/api/security/simulations").then(setSims).catch(() => {});
    api<[]>(`/api/security/reports`).then(setReports as never).catch(() => {});
  }, []);

  const unavailable = !status || (status as { state?: string }).state === "NOT_INSTALLED";
  const browser = (status?.browser || {}) as Record<string, unknown>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Security</h1>
      {err && !status && (
        <p role="alert" className="rounded border border-amber-800 bg-amber-950 p-2 text-sm">
          AppSec Lab unavailable — showing install state. {err}
        </p>
      )}
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
        <section aria-label="Engagements" className="grid gap-2">
          {engs.map((e) => (
            <div key={String(e.id)} className="rounded border border-zinc-800 p-3 text-sm" data-testid={`eng-${String(e.id)}`}>
              <div className="flex items-center justify-between">
                <strong>{String(e.name)}</strong>
                <StatusBadge status={String(e.status)} />
              </div>
              <p className="text-zinc-400">{String(e.scope_summary)}</p>
              <p className="mono text-xs text-zinc-500">findings {String(e.finding_count)} · report {String(e.report_status)}</p>
              <div className="mt-1 flex gap-2 text-xs">
                <span className="rounded border border-zinc-700 px-2 py-0.5">Open</span>
                <span className="rounded border border-zinc-700 px-2 py-0.5">Run Audit</span>
                <span className="rounded border border-zinc-700 px-2 py-0.5">View Findings</span>
                <span className="rounded border border-zinc-700 px-2 py-0.5">View Report</span>
              </div>
            </div>
          ))}
          {engs.length === 0 && <p className="text-sm text-zinc-500">{unavailable ? "Not installed" : "No engagements."}</p>}
        </section>
      )}

      {tab === "Browser" && (
        <section aria-label="Browser" className="rounded border border-zinc-800 p-4 text-sm">
          <ul className="grid gap-1 md:grid-cols-2">
            {["engine", "mode", "url", "flow", "title", "role", "captured_requests"].map((k) => (
              <li key={k} className="flex justify-between rounded border border-zinc-800 px-2 py-1">
                <span className="text-zinc-500">{k}</span>
                <span className="mono">{String(browser[k] ?? "—")}</span>
              </li>
            ))}
          </ul>
          <div className="mt-2 flex gap-2 text-xs">
            {["Start", "Stop", "Pause", "Resume"].map((a) => (
              <span key={a} className="rounded border border-zinc-700 px-2 py-1">{a}</span>
            ))}
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
          <p className="p-2 text-xs text-zinc-500">Headers/bodies redacted by backend. Bounded to 100 rows.</p>
        </section>
      )}

      {tab === "API Map" && (
        <section aria-label="API map" className="space-y-3 text-sm">
          <table className="w-full rounded border border-zinc-800 text-left text-xs">
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
          <GraphView title="API map graph" nodes={apiMap.map((r) => String(r.route))} edges={apiMap.map((r) => ({ from: String(r.host), to: `${r.method} ${r.route}` }))} />
        </section>
      )}

      {tab === "Findings" && (
        <section aria-label="Findings" className="grid gap-2">
          {findings.map((f) => <FindingCard key={f.id} finding={f} />)}
          {findings.length === 0 && <p className="text-sm text-zinc-500">No findings.</p>}
        </section>
      )}

      {tab === "Simulations" && (
        <section aria-label="Simulations" className="overflow-x-auto rounded border border-zinc-800 text-sm">
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
          <div className="mt-2 flex gap-2 text-xs">
            {["Prepare Fix", "Run Fix", "View Patch", "Verify"].map((a) => (
              <span key={a} className="rounded border border-zinc-700 px-2 py-1">{a}</span>
            ))}
          </div>
          <p className="mt-2 text-xs text-zinc-500">Never auto-applies or pushes.</p>
        </section>
      )}

      {tab === "Reports" && (
        <section aria-label="Reports">
          <ReportViewer reports={reports as never} />
          <p className="mt-2 text-xs text-zinc-500">Safe artifact IDs only; no filesystem paths.</p>
        </section>
      )}
    </div>
  );
}
