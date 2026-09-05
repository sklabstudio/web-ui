"use client";
import { useState } from "react";

/** Shared report viewer: Markdown/JSON summary/SARIF metadata + safe artifact view/download. */
export interface ReportRef {
  id: string;
  kind: string;
  title: string;
  created_at?: string;
  artifact_id?: string;
  content?: string;
}

export function ReportViewer({ reports }: { reports: ReportRef[] }) {
  const [open, setOpen] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState("");
  if (!reports || reports.length === 0)
    return <p className="text-sm text-zinc-500">No reports yet.</p>;

  async function view(id: string, artifact: string) {
    try {
      const res = await fetch(`/api/artifacts/${encodeURIComponent(artifact)}`, {
        credentials: "include",
      });
      const data = await res.json();
      const text =
        typeof data?.content === "string" ? data.content : JSON.stringify(data, null, 2);
      setOpen((o) => ({ ...o, [id]: text.slice(0, 8000) }));
    } catch (e) {
      setOpen((o) => ({ ...o, [id]: `Could not load artifact: ${String(e)}` }));
    }
  }

  function viewContent(id: string, content: string) {
    setOpen((o) => ({ ...o, [id]: content.slice(0, 8000) }));
  }

  async function copySummary(r: ReportRef) {
    const text = `${r.title || r.id} (${r.kind}) — ${r.id}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(r.id);
      setTimeout(() => setCopied(""), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <ul data-testid="report-viewer" className="space-y-2 text-sm">
      {reports.map((r) => (
        <li key={r.id} className="rounded border border-zinc-800 px-3 py-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="font-medium">{r.title || r.id}</div>
              <div className="mono text-xs text-zinc-500">
                {r.kind} · {r.id}
              </div>
            </div>
            <div className="flex gap-2 text-xs">
              {r.content ? (
                <button
                  onClick={() => viewContent(r.id, r.content as string)}
                  className="mono rounded border border-zinc-700 px-2 py-1 text-cyan-300"
                >
                  {open[r.id] ? "Hide" : "View"}
                </button>
              ) : r.artifact_id ? (
                <>
                  <button
                    onClick={() => view(r.id, r.artifact_id as string)}
                    className="mono rounded border border-zinc-700 px-2 py-1 text-cyan-300"
                  >
                    {open[r.id] ? "Hide" : "View"}
                  </button>
                  <a
                    className="mono rounded border border-zinc-700 px-2 py-1 text-cyan-300 underline"
                    href={`/api/artifacts/${encodeURIComponent(r.artifact_id)}`}
                  >
                    download artifact
                  </a>
                </>
              ) : (
                <span className="text-xs text-zinc-500">no artifact</span>
              )}
              <button
                onClick={() => copySummary(r)}
                className="mono rounded border border-zinc-700 px-2 py-1"
              >
                {copied === r.id ? "Copied" : "Copy summary"}
              </button>
            </div>
          </div>
          {open[r.id] && (
            <pre className="mono mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-zinc-950 p-2 text-xs">
              {open[r.id]}
            </pre>
          )}
        </li>
      ))}
    </ul>
  );
}
