"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ErrorNote } from "@/components/Ops";

const ACTIONS = [
  ["New Task", "/tasks/new", "Start a repo-scoped coding run"],
  ["Clone / Open Repo", "/repositories", "Bring a workspace into the console"],
  ["New AppSec Engagement", "/security", "Scope a safe local engagement"],
  ["Analyze Contract", "/contracts", "Import, compile, and verify"],
  ["Create Protocol Project", "/protocols", "Initialize protocol assurance"],
] as const;

const ACTIVE = [
  "RUNNING_AGENT",
  "VERIFYING",
  "RETRYING",
  "WAITING_FOR_APPROVAL",
  "BLOCKED",
  "PREPARING",
  "PLANNING",
];

type ServiceState = { state: string; detail?: string };

function Metric({ label, value, tone = "" }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="border border-zinc-800 p-3">
      <div className="eyebrow">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${tone}`}>{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [system, setSystem] = useState<Record<string, ServiceState> | null>(null);
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [sec, setSec] = useState<Record<string, unknown> | null>(null);
  const [con, setCon] = useState<Record<string, unknown> | null>(null);
  const [pro, setPro] = useState<Record<string, unknown> | null>(null);
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<unknown>("");

  useEffect(() => {
    api<Record<string, ServiceState>>("/api/system").then(setSystem).catch(setError);
    api<Array<Record<string, unknown>>>("/api/runs").then(setRuns).catch(() => {});
    api<Record<string, unknown>>("/api/security/status").then(setSec).catch(() => setSec(null));
    api<Record<string, unknown>>("/api/contracts/status").then(setCon).catch(() => setCon(null));
    api<Record<string, unknown>>("/api/protocols/status").then(setPro).catch(() => setPro(null));
    api<Array<Record<string, unknown>>>("/api/agents").then(setAgents).catch(() => {});
    api<Array<Record<string, unknown>>>("/api/providers").then(setProviders).catch(() => {});
  }, []);

  const active = runs.filter((r) => ACTIVE.includes(String(r.status)));
  const waiting = runs.filter((r) => String(r.status) === "WAITING_FOR_APPROVAL");
  const verified = runs.filter((r) => r.result_status === "VERIFIED_SUCCESS").length;
  const readyAgents = agents.filter((a) => a.installed && String(a.status) === "READY").length;
  const readyProviders = providers.filter((p) => String(p.status) === "READY").length;
  const readiness = system
    ? Object.values(system).filter((service) => service.state === "READY").length
    : 0;
  const moduleCards: Array<{ label: string; data: Record<string, unknown> | null; href: string; fact: string; key: string }> = [
    { label: "Security", data: sec, href: "/security", fact: "Open findings", key: "open_findings" },
    { label: "Contracts", data: con, href: "/contracts", fact: "Projects", key: "projects" },
    { label: "Protocols", data: pro, href: "/protocols", fact: "Monitored", key: "protocols" },
  ];

  return (
    <div className="space-y-5">
      <section className="term-frame">
        <div className="term-bar flex items-center justify-between px-4 py-2">
          <span>operator console / home</span>
          <span className="phos">{system ? "CONNECTED" : "CONNECTING..."}</span>
        </div>
        <div className="grid gap-6 p-5 md:grid-cols-[1.3fr_0.7fr]">
          <div>
            <p className="eyebrow">SKLAB WORKSTATION</p>
            <h1 className="mt-2 text-3xl font-semibold">Dashboard</h1>
            <p className="mt-3 max-w-2xl text-sm text-zinc-400">
              Operate from the browser: select a workspace, launch a bounded run, and inspect the evidence before anything is applied.
            </p>
            <div className="mt-5 flex flex-wrap gap-2 text-sm">
              <Link href="/tasks/new" className="ops-button rounded bg-cyan-500 px-4 py-2 font-semibold text-black">New Task</Link>
              <Link href="/repositories" className="ops-button rounded border border-zinc-700 px-4 py-2">Open Workspace</Link>
              <Link href="/runs" className="ops-button rounded border border-zinc-700 px-4 py-2">Inspect Runs</Link>
            </div>
          </div>
          <div className="border border-zinc-800 p-4">
            <div className="eyebrow">EXECUTION QUEUE</div>
            <div className="mt-3 flex items-end justify-between">
              <span className="text-sm text-zinc-400">active / approval</span>
              <span className="mono text-2xl text-cyan-300">{active.length} / {waiting.length}</span>
            </div>
            <div className="mt-4 border-t border-zinc-800 pt-3 text-xs text-zinc-500">
              {active.length ? `${active.length} run${active.length === 1 ? "" : "s"} require attention.` : "> queue idle / awaiting input"}
            </div>
            <Link href="/runs" className="mt-3 inline-block text-sm text-cyan-300 underline">Open run control</Link>
          </div>
        </div>
      </section>

      {error ? <ErrorNote error={error} onRetry={() => window.location.reload()} /> : null}

      <section aria-label="Primary actions">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="eyebrow">Quick actions / primary actions</h2>
          <span className="text-xs text-zinc-500">browser-operated / no terminal handoff</span>
        </div>
        <div className="workspace-grid grid-cols-1 md:grid-cols-5">
          {ACTIONS.map(([label, href, desc]) => (
            <Link key={href} href={href} className="action-link min-h-28">
              <span className="font-semibold text-cyan-300">{label}</span>
              <span className="mt-2 block text-xs text-zinc-500">{desc}</span>
            </Link>
          ))}
        </div>
      </section>

      <section aria-label="Operational overview">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="eyebrow">OPERATIONAL OVERVIEW</h2>
          <Link href="/modules" className="text-xs text-cyan-300 underline">doctor / module matrix</Link>
        </div>
        <div className="grid gap-1 bg-zinc-800 md:grid-cols-4">
          <Metric label="Active runs" value={active.length} tone={active.length ? "text-cyan-300" : ""} />
          <Metric label="Waiting approval" value={waiting.length} tone={waiting.length ? "text-amber-300" : ""} />
          <Metric label="Verified successes" value={verified} tone="text-emerald-300" />
          <Metric label="Agents / providers" value={`${readyAgents} / ${readyProviders}`} tone={readyAgents ? "text-emerald-300" : "text-amber-300"} />
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-[1.15fr_0.85fr]">
        <div className="term-frame p-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Run queue</h2>
            <Link href="/runs" className="text-xs text-cyan-300 underline">all runs</Link>
          </div>
          {active.length === 0 && waiting.length === 0 ? (
            <div className="mt-4 border-t border-zinc-800 pt-4 text-sm text-zinc-500">
              &gt; NO ACTIVE RUNS. Start a task to create the first evidence timeline.
            </div>
          ) : (
            <ul className="mt-3 text-sm">
              {[...waiting, ...active].slice(0, 6).map((run) => (
                <li key={String(run.id)} className="data-row flex flex-wrap items-center justify-between gap-2">
                  <Link href={`/runs/${String(run.id)}`} className="mono text-cyan-300 underline">{String(run.id)}</Link>
                  <span className="min-w-0 flex-1 truncate">{String(run.task_summary || run.task || "untitled task")}</span>
                  <StatusBadge status={String(run.status)} />
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="term-frame p-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Readiness</h2>
            <span className="mono text-xs text-cyan-300">{readiness}/{system ? Object.keys(system).length : "-"}</span>
          </div>
          <ul className="mt-3 text-sm">
            {[
              ["agent adapters", agents.length ? (readyAgents ? "READY" : "NOT_CONFIGURED") : "LOADING"],
              ["provider connections", providers.length ? (readyProviders ? "READY" : "NOT_CONFIGURED") : "LOADING"],
              ["AppSec Lab", String(sec?.state || "UNAVAILABLE")],
              ["Contract Toolkit", String(con?.state || "UNAVAILABLE")],
              ["Protocol Intelligence", String(pro?.state || "UNAVAILABLE")],
            ].map(([label, state]) => (
              <li key={label} className="data-row flex items-center justify-between gap-2">
                <span>{label}</span><StatusBadge status={state} />
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3" aria-label="Module work areas">
        {moduleCards.map(({ label, data, href, fact, key }) => (
          <div key={label} data-testid={`dash-${String(label).toLowerCase()}`} className="term-frame p-4">
            <div className="flex items-center justify-between"><h2 className="font-semibold">{label}</h2><StatusBadge status={String(data?.state || "UNAVAILABLE")} /></div>
            <p className="mt-3 text-sm text-zinc-400">{fact}: <span className="mono text-zinc-100">{String(data?.[key] ?? "—")}</span></p>
            <Link href={href} className="mt-3 inline-block text-sm text-cyan-300 underline">Open {label}</Link>
          </div>
        ))}
      </section>

      <details className="term-frame p-4" open>
        <summary className="cursor-pointer font-semibold">System health / raw module states</summary>
        {!system ? <p className="mt-3 text-sm text-zinc-500">Loading system state...</p> : (
          <ul className="mt-3 grid gap-1 text-xs md:grid-cols-3">
            {Object.entries(system).map(([key, value]) => (
              <li key={key} className="flex items-center justify-between border border-zinc-800 px-2 py-1">
                <span className="mono">{key}</span><StatusBadge status={value.state} />
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-xs text-zinc-500">Unavailable metrics remain unavailable. No mock values are promoted in live mode.</p>
      </details>
    </div>
  );
}
