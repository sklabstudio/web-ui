"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function AgentDetail({ params }: { params: { id: string } }) {
  const [a, setA] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    api<Record<string, unknown>>(`/api/agents/${params.id}`).then(setA).catch(() => {});
  }, [params.id]);
  if (!a) return <p className="text-sm text-zinc-500">Loading…</p>;
  const caps = (a.capabilities as Record<string, string>) || {};
  return (
    <div className="space-y-4">
      <h1 className="mono text-2xl font-bold">{String(a.id)}</h1>
      <table className="w-full text-sm">
        <tbody>
          {Object.entries(caps).map(([k, v]) => (
            <tr key={k} className="border-b border-zinc-800">
              <td className="py-1">{k}</td>
              <td className="mono py-1 text-right">{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-zinc-500">Unsupported capabilities are never faked as supported.</p>
    </div>
  );
}
