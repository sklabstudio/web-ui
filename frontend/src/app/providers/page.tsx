"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [form, setForm] = useState({ id: "openai", api_key: "", default_model: "" });
  const [msg, setMsg] = useState("");

  async function load() {
    try {
      setProviders(await api<Array<Record<string, unknown>>>("/api/providers"));
    } catch {
      /* ignore */
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      await api("/api/providers", { method: "POST", body: JSON.stringify(form) });
      // Immediately discard key from frontend state — never persist.
      setForm({ id: form.id, api_key: "", default_model: "" });
      (document.getElementById("api-key-input") as HTMLInputElement | null)?.setAttribute("value", "");
      setMsg("Saved. Key discarded from browser state and never re-displayed.");
      load();
    } catch (err) {
      setMsg(String(err));
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Providers</h1>
      <ul className="grid gap-2 md:grid-cols-2">
        {providers.map((p) => (
          <li key={String(p.id)} className="rounded border border-zinc-800 p-3 text-sm">
            <span className="mono font-semibold">{String(p.label || p.id)}</span>{" "}
            <StatusBadge status={String(p.status)} />
            <div className="mono text-xs text-zinc-500">
              type={String(p.type)} · model={String(p.default_model)} · enabled={String(p.enabled)}
            </div>
          </li>
        ))}
      </ul>
      <form onSubmit={submit} className="space-y-2 rounded border border-zinc-800 p-3 text-sm" data-testid="provider-form">
        <h2 className="font-semibold">Add API-key provider</h2>
        <label className="block">
          Provider ID
          <input value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Provider ID" />
        </label>
        <label className="block">
          API key (entered once, never stored in browser)
          <input id="api-key-input" type="password" autoComplete="off" value={form.api_key}
            onChange={(e) => setForm({ ...form, api_key: e.target.value })}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="API key" />
        </label>
        <button className="rounded bg-cyan-500 px-3 py-1 font-semibold text-black">Save securely</button>
        {msg && <p className="text-xs text-zinc-400">{msg}</p>}
      </form>
    </div>
  );
}
