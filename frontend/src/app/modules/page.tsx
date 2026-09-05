"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

export default function ModulesPage() {
  const [mods, setMods] = useState<Array<Record<string, unknown>>>([]);
  const [doctor, setDoctor] = useState<Record<string, unknown> | null>(null);
  const [sel, setSel] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<unknown>("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      setMods(await api<Array<Record<string, unknown>>>("/api/modules/full"));
    } catch (e) {
      setErr(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function runDoctor() {
    setErr("");
    try {
      setDoctor(await api<Record<string, unknown>>("/api/doctor"));
    } catch (e) {
      setErr(e);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Modules</h1>
        <div className="flex gap-2">
          <ActionButton label="Refresh" onRun={load} />
          <ActionButton label="Doctor" onRun={runDoctor} />
        </div>
      </div>
      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {loading ? (
        <Loading what="modules" />
      ) : mods.length === 0 ? (
        <Empty what="modules" />
      ) : (
        <ul className="grid gap-2 md:grid-cols-2">
          {mods.map((m) => (
            <li key={String(m.id)} className="rounded border border-zinc-800 p-3 text-sm">
              <div className="flex items-center justify-between">
                <strong>{String(m.name || m.id)}</strong>
                <StatusBadge status={String(m.state)} />
              </div>
              <div className="mono mt-1 text-xs text-zinc-500">
                {String(m.id)} · v{String(m.version ?? "—")} · {String(m.visibility || "public")}
                {m.mock ? " · mock" : ""}
              </div>
              {m.detail ? <p className="mt-1 text-xs text-zinc-400">{String(m.detail)}</p> : null}
              <button
                onClick={async () => {
                  try {
                    setSel(await api<Record<string, unknown>>(`/api/modules/${String(m.id)}`));
                  } catch (e) {
                    setErr(e);
                  }
                }}
                className="mt-2 rounded border border-zinc-700 px-2 py-0.5 text-xs"
              >
                Open module details
              </button>
            </li>
          ))}
        </ul>
      )}
      {sel && (
        <section aria-label="Module details" className="rounded border border-zinc-800 p-3 text-sm">
          <div className="flex items-center justify-between">
            <h2 className="mono font-semibold">{String(sel.id)}</h2>
            <button onClick={() => setSel(null)} className="rounded border border-zinc-700 px-2 py-0.5 text-xs">Close</button>
          </div>
          <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">
            {JSON.stringify(sel, null, 2).slice(0, 4000)}
          </pre>
        </section>
      )}
      {doctor && (
        <section aria-label="Doctor" className="rounded border border-zinc-800 p-3 text-sm">
          <h2 className="font-semibold">Doctor (zero-cost)</h2>
          <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">
            {JSON.stringify(doctor, null, 2).slice(0, 4000)}
          </pre>
        </section>
      )}
      <p className="text-xs text-zinc-500">
        Private modules are identified as private; their internals are never exposed.
      </p>
    </div>
  );
}
