"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ActionButton, ErrorNote, Loading } from "@/components/Ops";

export default function SettingsPage() {
  const [s, setS] = useState<Record<string, unknown> | null>(null);
  const [sys, setSys] = useState<Record<string, { state: string; detail?: string }> | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState<unknown>("");
  useEffect(() => {
    api<Record<string, unknown>>("/api/settings").then(setS).catch(setErr);
    api<Record<string, { state: string }>>("/api/system").then(setSys).catch(() => {});
  }, []);
  async function save() {
    setErr("");
    try {
      const out = await api<Record<string, unknown>>("/api/settings", {
        method: "PUT",
        body: JSON.stringify(s),
      });
      setS(out);
      setMsg("Saved.");
    } catch (e) {
      setErr(e);
    }
  }
  if (err && !s) return <ErrorNote error={err} />;
  if (!s) return <Loading what="settings" />;
  const set = (k: string, v: unknown) => setS({ ...s, [k]: v });
  const dict = (k: string) => JSON.stringify(s[k] ?? {});
  const setDict = (k: string, v: string) => {
    try {
      set(k, JSON.parse(v));
    } catch {
      /* keep editing */
    }
  };
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>
      {err ? <ErrorNote error={err} /> : null}
      <section aria-label="General" className="grid gap-2 text-sm md:grid-cols-2 rounded border border-zinc-800 p-3">
        <h2 className="font-semibold md:col-span-2">General</h2>
        <label>Default routing policy
          <input value={String(s.default_routing_policy)} onChange={(e) => set("default_routing_policy", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Default routing policy" />
        </label>
        <label>Max attempts
          <input type="number" value={Number(s.max_attempts)} onChange={(e) => set("max_attempts", Number(e.target.value))}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Max attempts" />
        </label>
        <label>Execution policy
          <input value={String(s.execution_policy ?? "safe")} onChange={(e) => set("execution_policy", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Execution policy" />
        </label>
        <label>Skill auto mode
          <select value={String(s.skill_auto_mode ?? s.skill_auto_install ?? "OFF")} onChange={(e) => { set("skill_auto_mode", e.target.value); set("skill_auto_install", e.target.value); }}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Skill auto mode">
            {(["OFF", "SAFE", "SMART", "FULL"] as const).map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={Boolean(s.require_approval_for_paid)}
            onChange={(e) => set("require_approval_for_paid", e.target.checked)} aria-label="Require approval for paid" />
          Require approval for paid
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={Boolean(s.auto_apply_patch)}
            onChange={(e) => set("auto_apply_patch", e.target.checked)} aria-label="Auto apply patch" />
          Auto-apply patch (default OFF)
        </label>
      </section>
      <section aria-label="Provider and agent defaults" className="grid gap-2 text-sm md:grid-cols-2 rounded border border-zinc-800 p-3">
        <h2 className="font-semibold md:col-span-2">Provider / Agent defaults</h2>
        <label>Provider default
          <input value={String(s.provider_default ?? "")} onChange={(e) => set("provider_default", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Provider default" placeholder="auto" />
        </label>
        <label>Agent default
          <input value={String(s.agent_default ?? "")} onChange={(e) => set("agent_default", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Agent default" placeholder="auto" />
        </label>
      </section>
      <section aria-label="Module policies" className="grid gap-2 text-sm rounded border border-zinc-800 p-3">
        <h2 className="font-semibold">Module policies (JSON)</h2>
        {([["appsec_safe_limits", "AppSec safe limits"], ["contract_tool_preferences", "Contract tool preferences"], ["protocol_assurance_defaults", "Protocol assurance defaults"], ["ui_preferences", "UI preferences"]] as const).map(([k, label]) => (
          <label key={k} className="block">{label}
            <textarea defaultValue={dict(k)} onBlur={(e) => setDict(k, e.target.value)} rows={2}
              className="mono mt-1 block w-full rounded bg-zinc-900 p-2 text-xs" aria-label={label} />
          </label>
        ))}
      </section>
      <p className="text-xs text-zinc-500">
        Allowed repo roots: {((s.allowed_repo_roots as string[]) || []).join(", ")}
      </p>
      <section aria-label="Integrations" className="rounded border border-zinc-800 p-3 text-sm">
        <h2 className="font-semibold">Integrations (status only — no credentials)</h2>
        {!sys ? <p className="text-zinc-500">Loading…</p> : (
          <ul className="mt-2 grid gap-1 md:grid-cols-2">
            {[["Security (AppSec Lab)", "appsec_lab"], ["Contracts (Toolkit)", "contract_toolkit"], ["Protocols (Intelligence)", "protocol_intelligence"], ["SKLab CLI", "sklab_cli"]].map(([label, key]) => (
              <li key={key} className="flex justify-between rounded border border-zinc-800 px-2 py-1">
                <span>{label}</span>
                <span className="mono text-xs">{sys[key]?.state || "UNKNOWN"}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <ActionButton label="Save" kind="primary" onRun={save} />
      {msg && <p className="text-xs">{msg}</p>}
    </div>
  );
}
