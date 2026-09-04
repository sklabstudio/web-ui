"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { RunEvent } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { LogViewer } from "@/components/LogViewer";
import { DiffViewer } from "@/components/DiffViewer";
import { AttemptTimeline } from "@/components/AttemptTimeline";
import { ApprovalCard } from "@/components/ApprovalCard";

const STAGES = ["Inspecting", "Planning", "Preparing", "Running Agent", "Capturing Patch", "Verifying", "Retrying", "Completed"];

export default function RunDetailPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const [run, setRun] = useState<Record<string, unknown> | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [error, setError] = useState("");
  const esRef = useRef<EventSource | null>(null);

  async function refresh() {
    try {
      const r = await api<Record<string, unknown>>(`/api/runs/${id}`);
      setRun(r);
    } catch (e) {
      setError(String(e));
    }
  }

  useEffect(() => {
    refresh();
    const es = new EventSource(`/api/runs/${id}/events`);
    esRef.current = es;
    es.onmessage = (m) => {
      try {
        const e = JSON.parse(m.data) as RunEvent;
        setEvents((prev) => {
          if (prev.some((p) => p.seq === e.seq)) return prev;
          return [...prev, e].sort((a, b) => a.seq - b.seq);
        });
      } catch {
        /* ignore malformed */
      }
    };
    es.onerror = () => {
      // reconnect safely: refetch state, EventSource auto-retries
      refresh();
    };
    const poll = setInterval(refresh, 3000);
    return () => {
      es.close();
      clearInterval(poll);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function cancel() {
    if (!confirm("Cancel this run? Only the current SKLab run will stop.")) return;
    await api(`/api/runs/${id}/cancel`, { method: "POST", body: "{}" });
    refresh();
  }
  async function resume() {
    await api(`/api/runs/${id}/resume`, { method: "POST", body: "{}" });
    refresh();
  }

  const approval = run?.approval as { reason: string; budget?: string; agent?: string; provider?: string } | null;

  return (
    <div className="space-y-4">
      <h1 className="mono text-xl font-bold">Run {id}</h1>
      {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
      {run ? (
        <>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <StatusBadge status={String(run.status)} />
            <span className="mono text-xs text-zinc-400">
              agent={String(run.agent)} · model={String(run.model)} · provider={String(run.provider)} · env={String(run.environment)}
            </span>
          </div>
          <ol className="flex flex-wrap gap-1 text-xs" aria-label="Run stages">
            {STAGES.map((s) => (
              <li key={s} className="rounded border border-zinc-800 px-2 py-1 text-zinc-400">{s}</li>
            ))}
          </ol>
          {approval && (
            <ApprovalCard approval={approval} onApprove={resume} onReject={cancel} />
          )}
          <div className="flex gap-2 text-sm">
            <button onClick={cancel} className="rounded border border-red-700 px-3 py-1">Cancel</button>
            {(run.status === "BLOCKED" || run.status === "WAITING_FOR_APPROVAL" || run.status === "FAILED") && (
              <button onClick={resume} className="rounded border border-cyan-600 px-3 py-1">Resume</button>
            )}
          </div>
          <LogViewer events={events} />
          <AttemptTimeline attempts={(run.attempt_details as Array<Record<string, unknown>>) || []} />
          {run.verification_detail && (
            <section aria-label="Verification" className="rounded border border-zinc-800 p-3 text-sm">
              <h3 className="font-semibold">Verification</h3>
              <pre className="mono mt-1 whitespace-pre-wrap text-xs">
                {(run.verification_detail as { verdict: string; score: number }).verdict}{" "}
                {(run.verification_detail as { score: number }).score ?? ""}/100
              </pre>
            </section>
          )}
          {run.patch ? (
            <DiffViewer patch={String(run.patch)} />
          ) : (
            <p className="text-xs text-zinc-500">Patch not yet available.</p>
          )}
          {run.result_status !== "VERIFIED_SUCCESS" && run.status === "COMPLETED" && (
            <p role="note" className="rounded border border-amber-700 p-2 text-sm text-amber-300">
              Unverified — do not treat as success merely because the agent exited 0.
            </p>
          )}
        </>
      ) : (
        <p className="text-sm text-zinc-500">Loading run…</p>
      )}
    </div>
  );
}
