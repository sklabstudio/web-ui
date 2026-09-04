"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function Dashboard() {
  const [system, setSystem] = useState<Record<string, { state: string }> | null>(null);
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Record<string, { state: string }>>("/api/system")
      .then(setSystem)
      .catch((e) => setError(String(e)));
    api<Array<Record<string, unknown>>>("/api/runs")
      .then(setRuns)
      .catch(() => {});
  }, []);

  const active = runs.filter((r) =>
    ["RUNNING_AGENT", "VERIFYING", "RETRYING", "WAITING_FOR_APPROVAL", "BLOCKED"].includes(
      String(r.status)
    )
  );
  const verified = runs.filter((r) => r.result_status === "VERIFIED_SUCCESS").length;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      {error && (
        <p role="alert" className="rounded border border-red-800 bg-red-950 p-2 text-sm">
          System unavailable: {error}. Showing degraded state.
        </p>
      )}
      <section aria-label="System health" className="rounded border border-zinc-800 p-4">
        <h2 className="font-semibold">System health</h2>
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

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded border border-zinc-800 p-4">
          <div className="text-xs text-zinc-500">Active runs</div>
          <div className="text-2xl font-bold">{active.length}</div>
        </div>
        <div className="rounded border border-zinc-800 p-4">
          <div className="text-xs text-zinc-500">Verified successes</div>
          <div className="text-2xl font-bold">{verified}</div>
        </div>
        <div className="rounded border border-zinc-800 p-4">
          <div className="text-xs text-zinc-500">Recent runs</div>
          <div className="text-2xl font-bold">{runs.length}</div>
        </div>
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
