"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";
import Link from "next/link";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [form, setForm] = useState({ id: "openai", api_key: "", default_model: "" });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState<unknown>("");
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState("");
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      setProviders(await api<Array<Record<string, unknown>>>("/api/providers"));
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
        <div><p className="eyebrow">CONNECTIONS / AGENT READINESS</p><h1 className="mt-1 text-2xl font-bold">Providers</h1></div>
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
      <section className="term-frame p-4" aria-label="Agent readiness">
        <div className="flex items-center justify-between"><h2 className="font-semibold">Agent readiness</h2><Link href="/agents" className="text-xs text-cyan-300 underline">Open agent details</Link></div>
        {agents.length === 0 ? <p className="mt-3 text-sm text-zinc-500">No adapter catalog returned.</p> : (
          <ul className="mt-3 grid gap-2 md:grid-cols-2">
            {agents.map((agent) => {
              const installed = Boolean(agent.installed);
              const authenticated = Boolean(agent.auth_ready);
              const state = !installed ? "NOT_INSTALLED" : !authenticated ? "NOT_AUTHENTICATED" : String(agent.status || "AVAILABLE");
              return <li key={String(agent.id)} className="border border-zinc-800 p-3 text-sm"><div className="flex items-center justify-between"><Link href={`/agents/${String(agent.id)}`} className="mono text-cyan-300 underline">{String(agent.id)}</Link><StatusBadge status={state} /></div><div className="mono mt-1 text-xs text-zinc-500">installed={String(installed)} · authenticated={String(authenticated)} · version={String(agent.version || "—")}</div><p className="mt-2 text-xs text-zinc-400">{state === "NOT_INSTALLED" ? "Install the supported CLI on the workstation." : state === "NOT_AUTHENTICATED" ? "Authenticate using the CLI's native login flow." : "Available for task routing."}</p></li>;
            })}
          </ul>
        )}
      </section>
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
