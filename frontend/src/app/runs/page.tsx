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
    await api(`/api/runs/${id}/${action}`, { method: "POST", body: "{}" });
    load();
  }

  const shown = runs.filter(
    (r) =>
      !filter ||
      String(r.status).includes(filter) ||
      String(r.task_summary).toLowerCase().includes(filter.toLowerCase())
  );
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Runs</h1>
        <ActionButton label="Refresh" onRun={load} />
      </div>
      {error ? <ErrorNote error={error} onRetry={load} /> : null}
      <label className="text-sm">
        Filter{" "}
        <input value={filter} onChange={(e) => setFilter(e.target.value)}
          className="rounded bg-zinc-900 px-2 py-1" aria-label="Filter runs" placeholder="status or text" />
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
              <li key={id} className="rounded border border-zinc-800 p-3">
                <Link href={`/runs/${id}`} className="mono text-cyan-300 underline">{id}</Link>{" "}
                {String(r.task_summary)} <StatusBadge status={String(r.status)} />
                <div className="mono text-xs text-zinc-500">
                  repo={String(r.repo)} · attempts={String(r.attempts)} · verification={String(r.verification)} · cost={String(r.cost ?? "Unknown")}
                  {r.live ? " · live" : ""}
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
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
