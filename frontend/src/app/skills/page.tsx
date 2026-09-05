"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

export default function SkillsPage() {
  const [skills, setSkills] = useState<Array<Record<string, unknown>>>([]);
  const [q, setQ] = useState("");
  const [auto, setAuto] = useState("OFF");
  const [err, setErr] = useState<unknown>("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      setSkills(await api<Array<Record<string, unknown>>>("/api/skills"));
      const a = await api<{ mode?: string }>("/api/skills-auto").catch(() => ({ mode: "OFF" }));
      setAuto(String(a.mode || "OFF"));
    } catch (e) {
      setErr(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function op(label: string, fn: () => Promise<unknown>) {
    setErr("");
    setMsg(`${label}…`);
    try {
      await fn();
      setMsg(`${label}: done`);
      load();
    } catch (e) {
      setErr(e);
      setMsg("");
    }
  }

  const shown = skills.filter(
    (s) =>
      !q ||
      String(s.id).toLowerCase().includes(q.toLowerCase()) ||
      String(s.category || "").toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Skills</h1>
      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {msg && <p className="text-xs text-zinc-400">{msg}</p>}
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <label>
          Search{" "}
          <input value={q} onChange={(e) => setQ(e.target.value)} className="rounded bg-zinc-900 px-2 py-1" aria-label="Search skills" placeholder="id or category" />
        </label>
        <label>
          Auto mode{" "}
          <select value={auto} onChange={(e) => op("Set auto mode", () => api("/api/skills-auto", { method: "POST", body: JSON.stringify({ mode: e.target.value }) }))}
            className="rounded bg-zinc-900 px-2 py-1" aria-label="Skill auto mode">
            {(["OFF", "SAFE", "SMART", "FULL"] as const).map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </label>
        <span className="text-xs text-zinc-500">Install never means global enable.</span>
      </div>
      {loading ? (
        <Loading what="skills" />
      ) : shown.length === 0 ? (
        <Empty what="skills match" />
      ) : (
        <ul className="grid gap-2 md:grid-cols-2">
          {shown.map((s) => (
            <li key={String(s.id)} className="rounded border border-zinc-800 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="mono font-semibold">{String(s.id)}</span>
                <StatusBadge status={s.enabled ? "SAFE" : "UNKNOWN"} />
              </div>
              <div className="mono mt-1 text-xs text-zinc-500">
                {String(s.enabled ? "enabled" : "disabled")} · {String(s.source)} · trust={String(s.trust_level)} · risk={String(s.risk || "—")}
              </div>
              <div className="mt-1 text-xs text-zinc-400">
                perms={(Array.isArray(s.permissions) ? (s.permissions as string[]).join(", ") : "—")}
                {s.version ? ` · v${String(s.version)}` : ""}
                {s.live === false || s.mock ? " · mock" : ""}
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                {s.enabled ? (
                  <ActionButton label="Disable" onRun={() => op(`Disable ${String(s.id)}`, () => api(`/api/skills/${String(s.id)}/disable`, { method: "POST", body: "{}" }))} />
                ) : (
                  <ActionButton label="Enable for task" onRun={() => op(`Enable ${String(s.id)}`, () => api(`/api/skills/${String(s.id)}/enable`, { method: "POST", body: JSON.stringify({ task_scoped: true }) }))} />
                )}
                <ActionButton label="Inspect" onRun={async () => {
                  const d = await api<Record<string, unknown>>(`/api/skills/${String(s.id)}`);
                  setDetail(d);
                  const a = await api<Record<string, unknown>>(`/api/skills/${String(s.id)}/audit`).catch(() => null);
                  if (a) setDetail({ ...d, audit: a });
                }} />
              </div>
            </li>
          ))}
        </ul>
      )}
      {detail && (
        <section aria-label="Skill detail" className="rounded border border-zinc-800 p-3 text-sm">
          <div className="flex items-center justify-between">
            <h2 className="mono font-semibold">{String(detail.id)}</h2>
            <button onClick={() => setDetail(null)} className="rounded border border-zinc-700 px-2 py-0.5 text-xs">Close</button>
          </div>
          <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs">
            {JSON.stringify(detail, null, 2).slice(0, 4000)}
          </pre>
        </section>
      )}
    </div>
  );
}
