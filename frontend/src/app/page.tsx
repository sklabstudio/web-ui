"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ErrorNote } from "@/components/Ops";

const QUICK = [
  ["New Task", "/tasks/new", "Start an AI engineering task"],
  ["New AppSec Engagement", "/security", "Scope a security engagement"],
  ["Analyze Contract", "/contracts", "Compile, test and analyze"],
  ["Create Protocol Project", "/protocols", "Map and assure a protocol"],
  ["View Runs", "/runs", "Inspect and control runs"],
  ["Skills", "/skills", "Review skill trust and scope"],
  ["Providers & Agents", "/providers", "Check connections and agents"],
  ["Modules", "/modules", "Full module health matrix"],
] as const;

export default function Dashboard() {
  const [system, setSystem] = useState<Record<string, { state: string; detail?: string }> | null>(null);
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [sec, setSec] = useState<Record<string, unknown> | null>(null);
  const [con, setCon] = useState<Record<string, unknown> | null>(null);
  const [pro, setPro] = useState<Record<string, unknown> | null>(null);
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<unknown>("");

  useEffect(() => {
    api<Record<string, { state: string }>>("/api/system")
      .then(setSystem)
      .catch((e) => setError(e));
    api<Array<Record<string, unknown>>>("/api/runs")
      .then(setRuns)
      .catch(() => {});
    api<Record<string, unknown>>("/api/security/status").then(setSec).catch(() => setSec(null));
    api<Record<string, unknown>>("/api/contracts/status").then(setCon).catch(() => setCon(null));
    api<Record<string, unknown>>("/api/protocols/status").then(setPro).catch(() => setPro(null));
    api<Array<Record<string, unknown>>>("/api/agents").then(setAgents).catch(() => {});
    api<Array<Record<string, unknown>>>("/api/providers").then(setProviders).catch(() => {});
  }, []);

  const active = runs.filter((r) =>
    ["RUNNING_AGENT", "VERIFYING", "RETRYING", "WAITING_FOR_APPROVAL", "BLOCKED", "PREPARING", "PLANNING"].includes(
      String(r.status)
    )
  );
  const waiting = runs.filter((r) => String(r.status) === "WAITING_FOR_APPROVAL");
  const verified = runs.filter((r) => r.result_status === "VERIFIED_SUCCESS").length;
  const readyAgents = agents.filter((a) => String(a.status) === "READY").length;
  const readyProviders = providers.filter((p) => String(p.status) === "READY").length;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      {error ? <ErrorNote error={error} onRetry={() => window.location.reload()} /> : null}

      <section aria-label="Quick actions" className="rounded border border-zinc-800 p-4">
        <h2 className="font-semibold">Quick actions</h2>
        <ul className="mt-2 grid gap-2 text-sm md:grid-cols-4">
          {QUICK.map(([label, href, desc]) => (
            <li key={href + label}>
              <Link
                href={href}
                className="block rounded border border-zinc-700 px-3 py-2 hover:border-cyan-500"
              >
                <span className="font-semibold text-cyan-300">{label}</span>
                <span className="block text-xs text-zinc-500">{desc}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section aria-label="System health" className="rounded border border-zinc-800 p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">System health</h2>
          <Link href="/modules" className="text-sm text-cyan-300 underline">
            Module health
          </Link>
        </div>
        {!system ? (
          <p className="text-sm text-zinc-500">Loading…</p>
        ) : (
          <ul className="mt-2 grid grid-cols-2 gap-2 text-sm md:grid-cols-3">
            {Object.entries(system).map(([k, v]) => (
              <li key={k} className="flex items-center justify-between rounded border border-zinc-800 px-2 py-1">
                <span className="mono">{k}</span>
                <StatusBadge status={v.state === "READY" ? "COMPLETED" : v.state} />
              </li>
            ))}
          </ul>
        )}
        <p className="mt-2 text-xs text-zinc-500">
          Unavailable metrics show UNAVAILABLE — never fake zero.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <div className="rounded border border-zinc-800 p-4">
          <div className="text-xs text-zinc-500">Active runs</div>
          <div className="text-2xl font-bold">{active.length}</div>
        </div>
        <div className="rounded border border-zinc-800 p-4">
          <div className="text-xs text-zinc-500">Waiting for approval</div>
          <div className="text-2xl font-bold">{waiting.length}</div>
        </div>
        <div className="rounded border border-zinc-800 p-4">
          <div className="text-xs text-zinc-500">Verified successes</div>
          <div className="text-2xl font-bold">{verified}</div>
        </div>
        <div className="rounded border border-zinc-800 p-4">
          <div className="text-xs text-zinc-500">Agents / Providers ready</div>
          <div className="text-2xl font-bold">
            {readyAgents}/{readyProviders}
          </div>
        </div>
      </section>

      <section aria-label="Module summaries" className="grid gap-4 md:grid-cols-3">
        <div className="rounded border border-zinc-800 p-4" data-testid="dash-security">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Security</h2>
            {sec ? <StatusBadge status={String((sec as Record<string, unknown>).state || "UNKNOWN")} /> : null}
          </div>
          {!sec ? (
            <p className="mt-2 text-sm text-zinc-500">Not installed</p>
          ) : (
            <ul className="mt-2 text-sm text-zinc-300">
              <li>Open findings: <span className="mono">{String(sec.open_findings ?? "—")}</span></li>
              <li>Endpoints: <span className="mono">{String(sec.api_endpoints ?? "—")}</span></li>
              <li>Latest report: <span className="mono">{String(sec.latest_report ?? "—")}</span></li>
            </ul>
          )}
          <Link href="/security" className="mt-2 inline-block text-sm text-cyan-300 underline">Open Security</Link>
        </div>
        <div className="rounded border border-zinc-800 p-4" data-testid="dash-contracts">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Contracts</h2>
            {con ? <StatusBadge status={String((con as Record<string, unknown>).state || "UNKNOWN")} /> : null}
          </div>
          {!con ? (
            <p className="mt-2 text-sm text-zinc-500">Not installed</p>
          ) : (
            <ul className="mt-2 text-sm text-zinc-300">
              <li>Projects: <span className="mono">{String(con.projects ?? "—")}</span></li>
              <li>Open findings: <span className="mono">{String(con.open_findings ?? "—")}</span></li>
              <li>Upgrade: <span className="mono">{String(con.latest_upgrade ?? "—")}</span></li>
            </ul>
          )}
          <Link href="/contracts" className="mt-2 inline-block text-sm text-cyan-300 underline">Open Contracts</Link>
        </div>
        <div className="rounded border border-zinc-800 p-4" data-testid="dash-protocols">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Protocols</h2>
            {pro ? <StatusBadge status={String((pro as Record<string, unknown>).state || "UNKNOWN")} /> : null}
          </div>
          {!pro ? (
            <p className="mt-2 text-sm text-zinc-500">Not installed</p>
          ) : (
            <ul className="mt-2 text-sm text-zinc-300">
              <li>Monitored: <span className="mono">{String(pro.protocols ?? "—")}</span></li>
              <li>Stale: <span className="mono">{String(pro.stale ?? "—")}</span></li>
              <li>Alerts: <span className="mono">{String(pro.alerts ?? "—")}</span></li>
            </ul>
          )}
          <Link href="/protocols" className="mt-2 inline-block text-sm text-cyan-300 underline">Open Protocols</Link>
        </div>
      </section>

      <section aria-label="Waiting for approval" className="rounded border border-amber-800 p-4">
        <h2 className="font-semibold">Waiting for approval</h2>
        {waiting.length === 0 ? (
          <p className="text-sm text-zinc-500">Nothing gated.</p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm">
            {waiting.map((r) => (
              <li key={String(r.id)}>
                <Link className="mono text-cyan-300 underline" href={`/runs/${String(r.id)}`}>
                  {String(r.id)}
                </Link>{" "}
                {String(r.task_summary)} <StatusBadge status={String(r.status)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-label="Active runs" className="rounded border border-zinc-800 p-4">
        <h2 className="font-semibold">Active runs</h2>
        {active.length === 0 ? (
          <p className="text-sm text-zinc-500">No active runs.</p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm">
            {active.map((r) => (
              <li key={String(r.id)}>
                <Link className="mono text-cyan-300 underline" href={`/runs/${String(r.id)}`}>
                  {String(r.id)}
                </Link>{" "}
                {String(r.task_summary)} <StatusBadge status={String(r.status)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-label="Recent runs" className="rounded border border-zinc-800 p-4">
        <h2 className="font-semibold">Recent runs</h2>
        <ul className="mt-2 space-y-1 text-sm">
          {runs.slice(0, 10).map((r) => (
            <li key={String(r.id)}>
              <Link className="mono text-cyan-300 underline" href={`/runs/${String(r.id)}`}>
                {String(r.id)}
              </Link>{" "}
              {String(r.task_summary)} <StatusBadge status={String(r.status)} />
            </li>
          ))}
        </ul>
        <Link href="/tasks/new" className="mt-3 inline-block rounded bg-cyan-500 px-3 py-1 text-sm font-semibold text-black">
          New task
        </Link>
      </section>
    </div>
  );
}
