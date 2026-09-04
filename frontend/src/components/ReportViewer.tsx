"use client";

/** Shared report viewer: Markdown/JSON summary/SARIF metadata + safe artifact download. */
export interface ReportRef {
  id: string;
  kind: string;
  title: string;
  created_at?: string;
  artifact_id?: string;
}

export function ReportViewer({ reports }: { reports: ReportRef[] }) {
  if (!reports || reports.length === 0)
    return <p className="text-sm text-zinc-500">No reports yet.</p>;
  return (
    <ul data-testid="report-viewer" className="space-y-2 text-sm">
      {reports.map((r) => (
        <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded border border-zinc-800 px-3 py-2">
          <div>
            <div className="font-medium">{r.title || r.id}</div>
            <div className="mono text-xs text-zinc-500">
              {r.kind} · {r.id}
            </div>
          </div>
          {r.artifact_id ? (
            <a
              className="mono rounded border border-zinc-700 px-2 py-1 text-xs text-cyan-300 underline"
              href={`/api/artifacts/${encodeURIComponent(r.artifact_id)}`}
            >
              download artifact
            </a>
          ) : (
            <span className="text-xs text-zinc-500">no artifact</span>
          )}
        </li>
      ))}
    </ul>
  );
}
