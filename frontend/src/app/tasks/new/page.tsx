"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { PlanPreview } from "@/components/PlanPreview";
import { ActionButton, Empty, ErrorNote, Facts, Loading } from "@/components/Ops";
import { StatusBadge } from "@/components/StatusBadge";

function Form() {
  const params = useSearchParams();
  const router = useRouter();
  const [repos, setRepos] = useState<Array<Record<string, unknown>>>([]);
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [skills, setSkills] = useState<Array<Record<string, unknown>>>([]);
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
  const [repoId, setRepoId] = useState("demo");
  const [ctx, setCtx] = useState<Record<string, unknown> | null>(null);
  const [resolved, setResolved] = useState<Record<string, unknown> | null>(null);
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<unknown>("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api<Array<Record<string, unknown>>>("/api/repos").then((r) => {
      setRepos(r);
      const match = r.find((x) => String(x.path) === (params.get("repo") || ""));
      if (match) setRepoId(String(match.id));
    }).catch(() => {});
    api<Array<Record<string, unknown>>>("/api/agents").then(setAgents).catch(() => {});
    api<Array<Record<string, unknown>>>("/api/providers").then(setProviders).catch(() => {});
    api<Array<Record<string, unknown>>>("/api/skills").then(setSkills).catch(() => {});
  }, [params]);

  const set = (k: string, v: unknown) => setForm((f) => ({ ...f, [k]: v }));
  const payload = () => ({ ...form, cost_budget: form.cost_budget ? Number(form.cost_budget) : null });

  async function inspectContext() {
    setError("");
    setNotice("");
    try {
      const c = await api<Record<string, unknown>>("/api/repos/context", {
        method: "POST",
        body: JSON.stringify({ path: form.repository }),
      });
      setCtx(c);
    } catch (e) {
      setError(e);
    }
  }

  async function resolveSkills() {
    setError("");
    try {
      const r = await api<Record<string, unknown>>("/api/skills/resolve", {
        method: "POST",
        body: JSON.stringify({ task: form.task, agent: form.agent }),
      });
      setResolved(r);
    } catch (e) {
      setError(e);
    }
  }

  async function doPlan() {
    setError("");
    setNotice("");
    try {
      const p = await api<Record<string, unknown>>("/api/runs/plan", {
        method: "POST",
        body: JSON.stringify(payload()),
      });
      setPlan(p);
    } catch (e) {
      setError(e);
    }
  }

  async function doRun() {
    setError("");
    try {
      const r = await api<{ id: string }>("/api/runs", {
        method: "POST",
        body: JSON.stringify(payload()),
      });
      router.push(`/runs/${r.id}`);
    } catch (e) {
      setError(e);
    }
  }

  const readyAgents = agents.filter((a) => a.installed && String(a.status) === "READY");
  const noAgents = agents.length > 0 && readyAgents.length === 0;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">New Task</h1>
      {noAgents && (
        <p role="note" className="rounded border border-amber-700 p-2 text-sm text-amber-300">
          No usable agents installed — planning will report AGENT_UNAVAILABLE honestly. Install an
          agent (see Agents) or use mock mode for trials.
        </p>
      )}
      {error ? <ErrorNote error={error} onRetry={doPlan} /> : null}
      {notice && <p className="text-sm text-zinc-400">{notice}</p>}

      <label className="block text-sm">
        Repository
        <select
          value={form.repository}
          onChange={(e) => {
            set("repository", e.target.value);
            const m = repos.find((x) => String(x.path) === e.target.value);
            if (m) setRepoId(String(m.id));
          }}
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
        ...or custom path under allowed roots
        <input
          value={form.repository}
          onChange={(e) => set("repository", e.target.value)}
          className="mono mt-1 block w-full rounded bg-zinc-900 p-2 text-xs"
          aria-label="Custom repository path"
          placeholder="/srv/sklab/repos/my-project"
        />
      </label>
      {repos.length === 0 && (
        <p className="text-xs text-zinc-500">
          No repositories discovered under allowed roots — enter a custom path above.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <ActionButton label="Inspect RepoContext" onRun={inspectContext} disabledReason={!form.task && !repoId ? "pick a repository" : ""} />
        {ctx && (
          <span className="mono text-xs text-zinc-400">
            fingerprint={String(ctx.fingerprint || ctx.context_fingerprint || "—")}
          </span>
        )}
      </div>
      {ctx && (
        <section aria-label="RepoContext" className="rounded border border-zinc-800 p-3 text-sm">
          <h3 className="font-semibold">RepoContext</h3>
          <Facts
            facts={Object.entries(ctx)
              .filter(([, v]) => typeof v === "string" || typeof v === "number" || typeof v === "boolean")
              .slice(0, 12)
              .map(([k, v]) => [k, String(v)])}
          />
        </section>
      )}

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

      <div className="grid gap-2 text-sm md:grid-cols-3">
        <label className="block">
          Agent
          <select value={form.agent} onChange={(e) => set("agent", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Agent">
            <option value="">auto-select</option>
            {agents.map((a) => (
              <option key={String(a.id)} value={String(a.id)}>
                {String(a.id)} ({String(a.status)}{a.live === false && !a.live ? ", mock" : ""})
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          Provider
          <select value={form.provider} onChange={(e) => set("provider", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Provider">
            <option value="">auto-select</option>
            {providers.map((p) => (
              <option key={String(p.id)} value={String(p.id)}>
                {String(p.label || p.id)} ({String(p.status)}{p.live === false ? ", stored" : ""})
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          Model
          <input value={form.model} onChange={(e) => set("model", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2 mono text-xs"
            aria-label="Model" placeholder="default for provider" />
        </label>
        <label className="block">
          Skill
          <select value={form.skill} onChange={(e) => set("skill", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Skill">
            <option value="">auto-resolve</option>
            {skills.map((s) => (
              <option key={String(s.id)} value={String(s.id)}>
                {String(s.id)} ({String(s.enabled ? "enabled" : "disabled")}, trust={String(s.trust_level)})
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          Execution mode
          <select value={form.routing_policy} onChange={(e) => set("routing_policy", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Execution mode">
            <option value="safe">safe (cheap first)</option>
            <option value="free">free only</option>
          </select>
        </label>
        <label className="block">
          Cost budget
          <input value={form.cost_budget} onChange={(e) => set("cost_budget", e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Cost budget" placeholder="Unknown" />
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={form.reprobox} onChange={(e) => set("reprobox", e.target.checked)} aria-label="Use ReproBox" />
          ReproBox
        </label>
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={form.verification} onChange={(e) => set("verification", e.target.checked)} aria-label="Verify with PatchBench" />
          Verify
        </label>
        <label className="flex items-center gap-1">
          Max attempts
          <input type="number" min={1} max={10} value={form.max_attempts}
            onChange={(e) => set("max_attempts", Number(e.target.value))}
            className="w-16 rounded bg-zinc-900 p-1" aria-label="Max attempts" />
        </label>
        <ActionButton label="Resolve skills" onRun={resolveSkills} disabledReason={!form.task ? "enter a task first" : ""} />
      </div>
      {resolved ? (
        <pre className="mono max-h-48 overflow-auto rounded border border-zinc-800 p-2 text-xs">
          {JSON.stringify(resolved, null, 2).slice(0, 3000)}
        </pre>
      ) : (
        skills.length === 0 && <Empty what="skills loaded" />
      )}

      <div className="flex gap-2">
        <ActionButton label="Plan" kind="primary" onRun={doPlan} disabledReason={!form.task ? "enter a task first" : ""} />
        <ActionButton label="Run" onRun={doRun} disabledReason={!plan ? "preview plan first" : ""} />
      </div>
      {plan && <PlanPreview plan={plan} />}
      {plan && (plan as { run_id?: string }).run_id && (
        <Link className="text-sm text-cyan-300 underline" href={`/runs/${String((plan as { run_id?: string }).run_id)}`}>
          Open planned run
        </Link>
      )}
      {agents.length === 0 && <Loading what="agents" />}
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
