"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [form, setForm] = useState({ id: "openai", api_key: "", default_model: "" });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState<unknown>("");
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      setProviders(await api<Array<Record<string, unknown>>>("/api/providers"));
    } catch (e) {
      setErr(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    setErr("");
    try {
      await api("/api/providers", { method: "POST", body: JSON.stringify(form) });
      // Immediately discard key from frontend state — never persist.
      setForm({ id: form.id, api_key: "", default_model: "" });
      (document.getElementById("api-key-input") as HTMLInputElement | null)?.setAttribute("value", "");
      setMsg("Saved. Key discarded from browser state and never re-displayed.");
      load();
    } catch (error) {
      setErr(error);
    }
  }

  async function test(id: string) {
    setTesting(id);
    setErr("");
    try {
      const r = await api<Record<string, unknown>>(`/api/providers/${id}/test`, { method: "POST", body: "{}" });
      setMsg(`${id}: zero-cost health ${r.ok ? "OK" : "NOT READY"} (${String(r.status)})`);
    } catch (e) {
      setErr(e);
    } finally {
      setTesting("");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Providers</h1>
        <ActionButton label="Refresh" onRun={load} />
      </div>
      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {loading ? (
        <Loading what="providers" />
      ) : providers.length === 0 ? (
        <Empty what="providers (none configured)" />
      ) : (
        <ul className="grid gap-2 md:grid-cols-2">
          {providers.map((p) => (
            <li key={String(p.id)} className="rounded border border-zinc-800 p-3 text-sm">
              <span className="mono font-semibold">{String(p.label || p.id)}</span>{" "}
              <StatusBadge status={String(p.status)} />
              <div className="mono text-xs text-zinc-500">
                type={String(p.type)} · model={String(p.default_model)} · enabled={String(p.enabled)}
                {p.live ? " · live" : ""}
              </div>
              <div className="mt-2">
                <ActionButton label={testing === String(p.id) ? "Testing…" : "Test zero-cost health"} onRun={() => test(String(p.id))} />
              </div>
            </li>
          ))}
        </ul>
      )}
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
        <label className="block">
          Default model
          <input value={form.default_model} onChange={(e) => setForm({ ...form, default_model: e.target.value })}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Default model" />
        </label>
        <button className="rounded bg-cyan-500 px-3 py-1 font-semibold text-black">Save securely</button>
        {msg && <p className="text-xs text-zinc-400">{msg}</p>}
      </form>
    </div>
  );
}
