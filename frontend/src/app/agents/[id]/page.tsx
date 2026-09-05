"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorNote, Facts, Loading } from "@/components/Ops";

export default function AgentDetail({ params }: { params: { id: string } }) {
  const [a, setA] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState<unknown>("");
  useEffect(() => {
    api<Record<string, unknown>>(`/api/agents/${params.id}`).then(setA).catch(setErr);
  }, [params.id]);
  if (err) return <ErrorNote error={err} />;
  if (!a) return <Loading what={`agent ${params.id}`} />;
  const caps = (a.capabilities as Record<string, string>) || {};
  const health = (a.health as Record<string, unknown>) || null;
  return (
    <div className="space-y-4">
      <h1 className="mono text-2xl font-bold">{String(a.id)}</h1>
      <Facts
        facts={[
          ["installed", String(a.installed)],
          ["version", String(a.version ?? "—")],
          ["auth", String(a.auth_ready)],
          ["status", String(a.status)],
          ["cost", String(a.cost_class || "unknown")],
          ["paid", String(a.paid ?? "—")],
          ["resume support", String(a.resume)],
          ["model selection", String(a.supports_model_selection)],
        ]}
      />
      <h2 className="font-semibold">Capabilities</h2>
      {Object.keys(caps).length === 0 ? (
        <p className="text-sm text-zinc-500">No capabilities reported.</p>
      ) : (
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
      )}
      {health && (
        <>
          <h2 className="font-semibold">Zero-cost health</h2>
          <pre className="mono max-h-64 overflow-auto whitespace-pre-wrap rounded border border-zinc-800 p-2 text-xs">
            {JSON.stringify(health, null, 2).slice(0, 3000)}
          </pre>
        </>
      )}
      <p className="text-xs text-zinc-500">Unsupported capabilities are never faked as supported.</p>
    </div>
  );
}
