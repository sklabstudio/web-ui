"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";
import { StatusBadge } from "@/components/StatusBadge";

type Repo = Record<string, unknown>;

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<unknown>("");
  const [message, setMessage] = useState("");
  const [cloneUrl, setCloneUrl] = useState("");
  const [destination, setDestination] = useState("");
  const [openPath, setOpenPath] = useState("");
  const [opened, setOpened] = useState<Repo | null>(null);
  const [ctx, setCtx] = useState<Record<string, Repo>>({});

  async function load() {
    setLoading(true);
    setErr("");
    try {
      setRepos(await api<Repo[]>("/api/repos"));
    } catch (e) {
      setErr(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function cloneRepo() {
    setErr("");
    setMessage("Cloning public repository...");
    try {
      const repo = await api<Repo>("/api/repos/clone", {
        method: "POST",
        body: JSON.stringify({ url: cloneUrl, destination: destination || null }),
      });
      setCloneUrl("");
      setDestination("");
      setOpened(repo);
      setMessage(`Clone complete: ${String(repo.name)}`);
      await load();
    } catch (e) {
      setErr(e);
      setMessage("");
    }
  }

  async function openRepo() {
    setErr("");
    setMessage("Validating workspace path...");
    try {
      const repo = await api<Repo>("/api/repos/open", {
        method: "POST",
        body: JSON.stringify({ path: openPath }),
      });
      setOpened(repo);
      setMessage(`Workspace opened: ${String(repo.name)}`);
      await load();
    } catch (e) {
      setErr(e);
      setMessage("");
    }
  }

  async function inspect(id: string) {
    setErr("");
    try {
      const c = await api<Repo>(`/api/repos/${encodeURIComponent(id)}/context`, { method: "POST", body: "{}" });
      setCtx((prev) => ({ ...prev, [id]: c }));
    } catch (e) {
      setErr(e);
    }
  }

  return (
    <div className="space-y-4">
      <section className="term-frame p-4">
        <p className="eyebrow">WORKSPACES / REPOSITORY CONTROL</p>
        <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Repositories</h1>
            <p className="mt-1 text-sm text-zinc-400">Only directories under the server allow-list are visible to tasks.</p>
          </div>
          <ActionButton label="Refresh" onRun={load} />
        </div>
      </section>

      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {message ? <p className="mono text-xs text-zinc-400">&gt; {message}</p> : null}

      <section className="grid gap-4 md:grid-cols-2" aria-label="Repository actions">
        <form className="term-frame space-y-3 p-4" onSubmit={(e) => e.preventDefault()}>
          <div className="eyebrow">CLONE PUBLIC REPO</div>
          <p className="text-xs text-zinc-500">HTTPS only. Credentials, local hosts, shell syntax, and unbounded paths are rejected.</p>
          <label className="block text-sm">Repository URL
            <input value={cloneUrl} onChange={(e) => setCloneUrl(e.target.value)} className="mt-1 block w-full rounded bg-zinc-900 p-2 mono text-xs" aria-label="Repository URL" placeholder="https://github.com/org/project.git" />
          </label>
          <label className="block text-sm">Destination name <span className="text-zinc-500">(optional)</span>
            <input value={destination} onChange={(e) => setDestination(e.target.value)} className="mt-1 block w-full rounded bg-zinc-900 p-2 mono text-xs" aria-label="Destination name" placeholder="project" />
          </label>
          <ActionButton label="Clone into managed root" kind="primary" onRun={cloneRepo} disabledReason={!cloneUrl.trim() ? "enter a public URL" : ""} />
        </form>

        <form className="term-frame space-y-3 p-4" onSubmit={(e) => e.preventDefault()}>
          <div className="eyebrow">OPEN EXISTING PATH</div>
          <p className="text-xs text-zinc-500">Read-only validation first. The path must stay inside an allowed root.</p>
          <label className="block text-sm">Server workspace path
            <input value={openPath} onChange={(e) => setOpenPath(e.target.value)} className="mt-1 block w-full rounded bg-zinc-900 p-2 mono text-xs" aria-label="Server workspace path" placeholder="/srv/sklab/repos/project" />
          </label>
          <ActionButton label="Open workspace" onRun={openRepo} disabledReason={!openPath.trim() ? "enter a path" : ""} />
          {opened ? (
            <div className="border-t border-zinc-800 pt-3 text-xs">
              <div className="flex flex-wrap items-center gap-2"><strong>{String(opened.name)}</strong><StatusBadge status={String(opened.context_status)} /></div>
              <div className="mono mt-1 text-zinc-500">{String(opened.path)} · branch={String(opened.branch)} · {opened.dirty ? "dirty" : "clean"}</div>
              <Link href={`/tasks/new?repo=${encodeURIComponent(String(opened.path))}`} className="mt-2 inline-block text-cyan-300 underline">Use for a new task</Link>
            </div>
          ) : null}
        </form>
      </section>

      <section aria-label="Managed repositories" className="term-frame p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Managed workspaces</h2>
          <span className="mono text-xs text-cyan-300">{repos.length} found</span>
        </div>
        <p className="mt-1 text-xs text-amber-300">Repository content is untrusted project data. Never execute a project action outside its allowed root.</p>
        {loading ? <div className="mt-4"><Loading what="repositories" /></div> : repos.length === 0 ? (
          <div className="mt-4 border-t border-zinc-800 pt-4"><Empty what="managed repositories" /></div>
        ) : (
          <ul className="mt-3 space-y-2">
            {repos.map((repo) => {
              const id = String(repo.id);
              const detail = ctx[id];
              return (
                <li key={id} className="border border-zinc-800 p-3 text-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div><strong className="mono">{String(repo.name || id)}</strong><span className="mono ml-2 text-xs text-zinc-500">{String(repo.path)}</span></div>
                    <StatusBadge status={String(repo.context_status || "UNKNOWN")} />
                  </div>
                  <div className="mt-1 text-xs text-zinc-400">branch={String(repo.branch)} · {repo.dirty ? "dirty" : "clean"} · stack={((repo.stack as string[]) || []).join(", ") || "unknown"}</div>
                  {detail ? <pre className="mono mt-2 max-h-40 overflow-auto whitespace-pre-wrap border border-zinc-800 p-2 text-xs">{JSON.stringify(detail, null, 2).slice(0, 2000)}</pre> : null}
                  <div className="mt-3 flex flex-wrap gap-2 text-xs">
                    <Link href={`/tasks/new?repo=${encodeURIComponent(String(repo.path))}`} className="ops-button rounded border border-zinc-700 px-2 py-1">New task</Link>
                    <ActionButton label="Inspect RepoContext" onRun={() => inspect(id)} />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
