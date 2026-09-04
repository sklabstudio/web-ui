"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { PlanPreview } from "@/components/PlanPreview";

function Form() {
  const params = useSearchParams();
  const router = useRouter();
  const [repos, setRepos] = useState<Array<Record<string, unknown>>>([]);
  const [form, setForm] = useState({
    repository: params.get("repo") || "/srv/sklab/repos/demo",
    task: "",
    agent: "",
    model: "",
    provider: "",
    skill: "",
    routing_policy: "safe",
    max_attempts: 3,
    timeout_seconds: 1200,
    cost_budget: "",
    reprobox: true,
    verification: true,
  });
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Array<Record<string, unknown>>>("/api/repos").then(setRepos).catch(() => {});
  }, []);

  const set = (k: string, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  async function doPlan() {
    setError("");
    setBusy(true);
    try {
      const p = await api<Record<string, unknown>>("/api/runs/plan", {
        method: "POST",
        body: JSON.stringify({ ...form, cost_budget: form.cost_budget ? Number(form.cost_budget) : null }),
      });
      setPlan(p);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function doRun() {
    setError("");
    setBusy(true);
    try {
      const r = await api<{ id: string }>("/api/runs", {
        method: "POST",
        body: JSON.stringify({ ...form, cost_budget: form.cost_budget ? Number(form.cost_budget) : null }),
      });
      router.push(`/runs/${r.id}`);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">New Task</h1>
      {error && <p role="alert" className="rounded border border-red-800 bg-red-950 p-2 text-sm">{error}</p>}
      <label className="block text-sm">
        Repository
        <select
          value={form.repository}
          onChange={(e) => set("repository", e.target.value)}
          className="mt-1 block w-full rounded bg-zinc-900 p-2"
          aria-label="Repository"
        >
          {repos.map((r) => (
            <option key={String(r.id)} value={String(r.path)}>{String(r.path)}</option>
          ))}
          <option value={form.repository}>{form.repository}</option>
        </select>
      </label>
      <label className="block text-sm">
        Task
        <textarea
          value={form.task}
          onChange={(e) => set("task", e.target.value)}
          rows={5}
          className="mt-1 block w-full rounded bg-zinc-900 p-2"
          placeholder="Describe the engineering task…"
          aria-label="Task"
        />
      </label>
      <details className="rounded border border-zinc-800 p-3 text-sm">
        <summary>Advanced controls</summary>
        <div className="mt-2 grid gap-2 md:grid-cols-2">
          {(["agent", "model", "provider", "skill", "routing_policy"] as const).map((k) => (
            <label key={k} className="block">
              {k}
              <input
                value={String(form[k])}
                onChange={(e) => set(k, e.target.value)}
                className="mt-1 block w-full rounded bg-zinc-900 p-2 mono text-xs"
                aria-label={k}
              />
            </label>
          ))}
          <label className="block">
            Max attempts
            <input type="number" min={1} max={10} value={form.max_attempts}
              onChange={(e) => set("max_attempts", Number(e.target.value))}
              className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Max attempts" />
          </label>
          <label className="block">
            Cost budget
            <input value={form.cost_budget} onChange={(e) => set("cost_budget", e.target.value)}
              className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Cost budget" placeholder="Unknown" />
          </label>
        </div>
      </details>
      <div className="flex gap-2">
        <button onClick={doPlan} disabled={busy || !form.task}
          className="rounded bg-cyan-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-50">
          Plan
        </button>
        <button onClick={doRun} disabled={busy || !plan}
          className="rounded border border-cyan-500 px-4 py-2 text-sm disabled:opacity-50" title={plan ? "" : "Preview plan first"}>
          Run
        </button>
      </div>
      {plan && <PlanPreview plan={plan} />}
    </div>
  );
}

export default function NewTaskPage() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <Form />
    </Suspense>
  );
}
