"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { RunEvent } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { LogViewer } from "@/components/LogViewer";
import { DiffViewer } from "@/components/DiffViewer";
import { AttemptTimeline } from "@/components/AttemptTimeline";
import { ApprovalCard } from "@/components/ApprovalCard";
import { Timeline } from "@/components/Timeline";
import { ActionButton, Empty, ErrorNote, Facts, Loading } from "@/components/Ops";

const TERMINAL = ["COMPLETED", "FAILED", "CANCELLED"];

export default function RunDetailPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const [run, setRun] = useState<Record<string, unknown> | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [error, setError] = useState<unknown>("");
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const r = await api<Record<string, unknown>>(`/api/runs/${id}`);
      setRun(r);
    } catch (e) {
      setError(e);
    }
  }, [id]);

  useEffect(() => {
    refresh();
    const es = new EventSource(`/api/runs/${id}/events`);
    esRef.current = es;
    es.onopen = () => setConnected(true);
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
      setConnected(false);
      refresh();
    };
    pollRef.current = setInterval(refresh, 5000);
    return () => {
      es.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [id, refresh]);

  async function ctl(action: string, confirmMsg?: string) {
    if (confirmMsg && !confirm(confirmMsg)) return;
    setError("");
    try {
      await api(`/api/runs/${id}/${action}`, { method: "POST", body: "{}" });
      refresh();
    } catch (e) {
      setError(e);
    }
  }

  const approval = run?.approval as { reason: string; budget?: string; agent?: string; provider?: string } | null;
  const status = String(run?.status || "");
  const terminal = TERMINAL.includes(status);
  const gated = status === "WAITING_FOR_APPROVAL";
  const attempts = (run?.attempt_details as Array<Record<string, unknown>>) || [];
  const started = events[0]?.ts || String(run?.created_at || "");
  const elapsed = run ? `${Number(run.duration_seconds || 0).toFixed(0)}s` : "—";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="mono text-xl font-bold">Run {id}</h1>
        <span className="mono text-xs text-zinc-500" aria-live="polite">
          SSE: {connected ? "connected" : "reconnecting…"}
        </span>
      </div>
      {error ? <ErrorNote error={error} onRetry={refresh} /> : null}
      {!run ? (
        <Loading what="run" />
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <StatusBadge status={status} />
            <span className="mono text-xs text-zinc-400">
              agent={String(run.agent)} · model={String(run.model)} · provider={String(run.provider)} · env={String(run.environment)}
            </span>
          </div>
          <Facts
            facts={[
              ["Task", String(run.task_summary || run.task || "—").slice(0, 200)],
              ["Stage", status],
              ["Attempts", String(run.attempts ?? attempts.length)],
              ["Elapsed", elapsed],
              ["Started", started || "—"],
              ["Result", String(run.result_status || "—")],
              ["Verification", String(run.verification || "—")],
              ["Winning agent", String(run.winning_agent || "—")],
              ["Cost", String(run.cost ?? "Unknown")],
            ]}
          />
          {approval && (
            <ApprovalCard
              approval={approval}
              onApprove={() => ctl("approve")}
              onReject={() => ctl("reject", "Reject this approval? The run will stop.")}
            />
          )}
          <div className="flex flex-wrap gap-2 text-sm" role="group" aria-label="Run controls">
            {!terminal && !gated && (
              <ActionButton label="Cancel" kind="danger" onRun={() => ctl("cancel", "Cancel this run? Only this SKLab run will stop.")} />
            )}
            {(status === "FAILED" || status === "BLOCKED" || status === "CANCELLED") && (
              <ActionButton label="Retry" onRun={() => ctl("retry")} />
            )}
            {!terminal && !gated && <ActionButton label="Resume" onRun={() => ctl("resume")} />}
            <ActionButton label="Refresh" onRun={refresh} />
          </div>
          <section aria-label="Live timeline">
            <h3 className="mb-1 font-semibold">Timeline</h3>
            <Timeline events={events} />
          </section>
          <LogViewer events={events} />
          <section aria-label="Attempts">
            <h3 className="mb-1 font-semibold">Attempts</h3>
            <AttemptTimeline attempts={attempts} />
          </section>
          {run.verification_detail ? (
            <section aria-label="Verification" className="rounded border border-zinc-800 p-3 text-sm">
              <h3 className="font-semibold">Verification</h3>
              <pre className="mono mt-1 whitespace-pre-wrap text-xs">
                {(run.verification_detail as { verdict: string; score: number }).verdict}{" "}
                {(run.verification_detail as { score: number }).score ?? ""}/100
              </pre>
              {Array.isArray((run.verification_detail as { checks?: unknown[] }).checks) && (
                <ul className="mono mt-1 text-xs">
                  {((run.verification_detail as { checks: Array<Record<string, unknown>> }).checks || []).map((c, i) => (
                    <li key={i}>
                      {String(c.name)} — {String(c.status)}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : (
            <p className="text-xs text-zinc-500">Verification not yet available.</p>
          )}
          {run.patch ? (
            <DiffViewer patch={String(run.patch)} />
          ) : (
            <p className="text-xs text-zinc-500">Patch not yet available.</p>
          )}
          {Array.isArray(run.warnings) && (run.warnings as unknown[]).length > 0 && (
            <section aria-label="Warnings" className="rounded border border-amber-800 p-3 text-sm">
              <h3 className="font-semibold text-amber-200">Warnings</h3>
              <ul className="mt-1 list-disc pl-5 text-xs">
                {(run.warnings as string[]).map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </section>
          )}
          {run.result_status !== "VERIFIED_SUCCESS" && status === "COMPLETED" && (
            <p role="note" className="rounded border border-amber-700 p-2 text-sm text-amber-300">
              Unverified — do not treat as success merely because the agent exited 0.
            </p>
          )}
          <p className="text-sm">
            <Link href="/runs" className="text-cyan-300 underline">
              Back to runs
            </Link>
          </p>
          {events.length === 0 && <Empty what="events yet (stream connecting)" />}
        </>
      )}
    </div>
  );
}
