"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [s, setS] = useState<Record<string, unknown> | null>(null);
  const [msg, setMsg] = useState("");
  useEffect(() => {
    api<Record<string, unknown>>("/api/settings").then(setS).catch(() => {});
  }, []);
  async function save() {
    try {
      const out = await api<Record<string, unknown>>("/api/settings", {
        method: "PUT",
        body: JSON.stringify(s),
      });
      setS(out);
      setMsg("Saved.");
    } catch (e) {
      setMsg(String(e));
    }
  }
  if (!s) return <p className="text-sm text-zinc-500">Loading…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="grid gap-2 text-sm md:grid-cols-2">
        <label>Default routing policy
          <input value={String(s.default_routing_policy)} onChange={(e) => setS({ ...s, default_routing_policy: e.target.value })}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Default routing policy" />
        </label>
        <label>Max attempts
          <input type="number" value={Number(s.max_attempts)} onChange={(e) => setS({ ...s, max_attempts: Number(e.target.value) })}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Max attempts" />
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={Boolean(s.require_approval_for_paid)}
            onChange={(e) => setS({ ...s, require_approval_for_paid: e.target.checked })} aria-label="Require approval for paid" />
          Require approval for paid
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={Boolean(s.auto_apply_patch)}
            onChange={(e) => setS({ ...s, auto_apply_patch: e.target.checked })} aria-label="Auto apply patch" />
          Auto-apply patch (default OFF)
        </label>
      </div>
      <p className="text-xs text-zinc-500">
        Allowed repo roots: {((s.allowed_repo_roots as string[]) || []).join(", ")}
      </p>
      <button onClick={save} className="rounded bg-cyan-500 px-3 py-1 text-sm font-semibold text-black">Save</button>
      {msg && <p className="text-xs">{msg}</p>}
    </div>
  );
}
