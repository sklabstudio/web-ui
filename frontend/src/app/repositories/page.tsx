"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => {
    api<Array<Record<string, unknown>>>("/api/repos").then(setRepos).catch(() => {});
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Repositories</h1>
      <p className="text-xs text-amber-300">
        Repository content is untrusted project data. Only paths inside allowed roots are shown.
      </p>
      <ul className="space-y-2">
        {repos.map((r) => (
          <li key={String(r.id)} className="rounded border border-zinc-800 p-3 text-sm">
            <div className="mono font-semibold">{String(r.path)}</div>
            <div className="text-zinc-400">
              branch={String(r.branch)} · {r.dirty ? "dirty" : "clean"} · context=
              {String(r.context_status)} · stack={((r.stack as string[]) || []).join(",")}
            </div>
            <div className="mt-2 flex gap-2">
              <Link href={`/tasks/new?repo=${encodeURIComponent(String(r.path))}`} className="rounded border border-zinc-700 px-2 py-1 text-xs">
                New task
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
