"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<unknown>("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      setAgents(await api<Array<Record<string, unknown>>>("/api/agents"));
    } catch (e) {
      setErr(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Agents</h1>
        <ActionButton label="Refresh" onRun={load} />
      </div>
      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {loading ? (
        <Loading what="agents" />
      ) : agents.length === 0 ? (
        <>
          <Empty what="agents (none installed)" />
          <p className="text-xs text-zinc-500">
            No usable agent is installed. Task execution will report AGENT_UNAVAILABLE honestly
            until an agent is installed on the workstation.
          </p>
        </>
      ) : (
        <ul className="grid gap-2 md:grid-cols-2">
          {agents.map((a) => (
            <li key={String(a.id)} className="rounded border border-zinc-800 p-3 text-sm">
              <Link href={`/agents/${String(a.id)}`} className="mono font-semibold text-cyan-300 underline">
                {String(a.id)}
              </Link>{" "}
              <StatusBadge status={String(a.status)} />
              <div className="mono text-xs text-zinc-500">
                installed={String(a.installed)} · v={String(a.version)} · auth={String(a.auth_ready)}
                {a.live ? " · live" : ""}
                {a.paid ? " · paid" : ""}
              </div>
              <div className="mono text-xs text-zinc-600">
                cost={String(a.cost_class || "unknown")} · resume={String(a.resume)} · models={String(a.supports_model_selection)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
