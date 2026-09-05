"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

const TERMINAL = ["COMPLETED", "FAILED", "CANCELLED"];

export default function RunsPage() {
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setRuns(await api<Array<Record<string, unknown>>>("/api/runs"));
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function ctl(id: string, action: string) {
    try {
      await api(`/api/runs/${id}/${action}`, { method: "POST", body: "{}" });
      await load();
    } catch (e) {
      setError(e);
    }
  }

  const shown = runs.filter(
    (r) =>
      !filter ||
      String(r.status).includes(filter) ||
      String(r.task_summary).toLowerCase().includes(filter.toLowerCase())
  );
  return (
    <div className="space-y-4">
      <div className="term-frame flex flex-wrap items-end justify-between gap-3 p-4">
        <div><p className="eyebrow">EXECUTION / CONTROL PLANE</p><h1 className="mt-1 text-2xl font-bold">Runs</h1></div>
        <ActionButton label="Refresh" onRun={load} />
      </div>
      {error ? <ErrorNote error={error} onRetry={load} /> : null}
      <label className="block border border-zinc-800 p-3 text-sm">
        <span className="eyebrow mr-2">Filter</span>
        <input value={filter} onChange={(e) => setFilter(e.target.value)}
          className="rounded bg-zinc-900 px-2 py-1" aria-label="Filter runs" placeholder="status or task text" />
      </label>
      {loading ? (
        <Loading what="runs" />
      ) : shown.length === 0 ? (
        <Empty what="runs match" />
      ) : (
        <ul className="space-y-2 text-sm">
          {shown.map((r) => {
            const id = String(r.id);
            const terminal = TERMINAL.includes(String(r.status));
            const gated = String(r.status) === "WAITING_FOR_APPROVAL";
            return (
              <li key={id} className="term-frame p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Link href={`/runs/${id}`} className="mono text-cyan-300 underline">{id}</Link>
                  <StatusBadge status={String(r.status)} />
                  {r.result_status ? <StatusBadge status={String(r.result_status)} /> : null}
                </div>
                <p className="mt-2">{String(r.task_summary || r.task || "untitled task")}</p>
                <div className="mono mt-1 text-xs text-zinc-500">
                  repo={String(r.repo || "—")} · attempts={String(r.attempts)} · agent={String(r.winning_agent || "pending")} · verification={String(r.verification)} · cost={String(r.cost ?? "Unknown")}
                  {r.live ? " · LIVE API" : ""}
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {!terminal && !gated && (
                    <ActionButton label="Cancel" kind="danger" onRun={() => ctl(id, "cancel")} />
                  )}
                  {(String(r.status) === "FAILED" || String(r.status) === "BLOCKED" || String(r.status) === "CANCELLED") && (
                    <ActionButton label="Retry" onRun={() => ctl(id, "retry")} />
                  )}
                  {gated && (
                    <>
                      <ActionButton label="Approve" kind="primary" onRun={() => ctl(id, "approve")} />
                      <ActionButton label="Reject" kind="danger" onRun={() => ctl(id, "reject")} />
                    </>
                  )}
                  {(String(r.status) === "BLOCKED" || String(r.status) === "CANCELLED") && (
                    <ActionButton label="Resume" onRun={() => ctl(id, "resume")} />
                  )}
                  <Link href={`/runs/${id}`} className="ops-button rounded border border-zinc-700 px-3 py-1 text-sm">Open inspector</Link>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
