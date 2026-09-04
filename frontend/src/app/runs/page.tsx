"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function RunsPage() {
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [filter, setFilter] = useState("");
  useEffect(() => {
    api<Array<Record<string, unknown>>>("/api/runs").then(setRuns).catch(() => {});
  }, []);
  const shown = runs.filter((r) =>
    !filter || String(r.status).includes(filter) || String(r.task_summary).toLowerCase().includes(filter.toLowerCase())
  );
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Runs</h1>
      <label className="text-sm">
        Filter{" "}
        <input value={filter} onChange={(e) => setFilter(e.target.value)}
          className="rounded bg-zinc-900 px-2 py-1" aria-label="Filter runs" placeholder="status or text" />
      </label>
      <ul className="space-y-2 text-sm">
        {shown.map((r) => (
          <li key={String(r.id)} className="rounded border border-zinc-800 p-3">
            <Link href={`/runs/${String(r.id)}`} className="mono text-cyan-300 underline">{String(r.id)}</Link>{" "}
            {String(r.task_summary)} <StatusBadge status={String(r.status)} />
            <div className="mono text-xs text-zinc-500">
              repo={String(r.repo)} · attempts={String(r.attempts)} · verification={String(r.verification)} · cost={String(r.cost ?? "Unknown")}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
