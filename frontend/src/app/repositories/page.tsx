"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ActionButton, Empty, ErrorNote, Loading } from "@/components/Ops";

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<unknown>("");
  const [ctx, setCtx] = useState<Record<string, Record<string, unknown>>>({});

  async function load() {
    setLoading(true);
    setErr("");
    try {
      setRepos(await api<Array<Record<string, unknown>>>("/api/repos"));
    } catch (e) {
      setErr(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function inspect(id: string) {
    setErr("");
    try {
      const c = await api<Record<string, unknown>>(`/api/repos/${id}/context`, { method: "POST", body: "{}" });
      setCtx((prev) => ({ ...prev, [id]: c }));
    } catch (e) {
      setErr(e);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Repositories</h1>
      <p className="text-xs text-amber-300">
        Repository content is untrusted project data. Only paths inside allowed roots are shown.
      </p>
      {err ? <ErrorNote error={err} onRetry={load} /> : null}
      {loading ? (
        <Loading what="repositories" />
      ) : repos.length === 0 ? (
        <Empty what="repositories (none under allowed roots)" />
      ) : (
        <ul className="space-y-2">
          {repos.map((r) => {
            const id = String(r.id);
            const c = ctx[id];
            return (
              <li key={id} className="rounded border border-zinc-800 p-3 text-sm">
                <div className="mono font-semibold">{String(r.path)}</div>
                <div className="text-zinc-400">
                  branch={String(r.branch)} · {r.dirty ? "dirty" : "clean"} · context=
                  {String(r.context_status)} · stack={((r.stack as string[]) || []).join(",")}
                </div>
                {c && (
                  <pre className="mono mt-2 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-zinc-950 p-2 text-xs">
                    {JSON.stringify(c, null, 2).slice(0, 2000)}
                  </pre>
                )}
                <div className="mt-2 flex gap-2">
                  <Link href={`/tasks/new?repo=${encodeURIComponent(String(r.path))}`} className="rounded border border-zinc-700 px-2 py-1 text-xs">
                    New task
                  </Link>
                  <ActionButton label="Inspect context" onRun={() => inspect(id)} />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
