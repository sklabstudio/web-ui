"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => {
    api<Array<Record<string, unknown>>>("/api/agents").then(setAgents).catch(() => {});
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Agents</h1>
      <ul className="grid gap-2 md:grid-cols-2">
        {agents.map((a) => (
          <li key={String(a.id)} className="rounded border border-zinc-800 p-3 text-sm">
            <Link href={`/agents/${String(a.id)}`} className="mono font-semibold text-cyan-300 underline">
              {String(a.id)}
            </Link>{" "}
            <StatusBadge status={String(a.status)} />
            <div className="mono text-xs text-zinc-500">
              installed={String(a.installed)} · v={String(a.version)} · auth={String(a.auth_ready)}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
