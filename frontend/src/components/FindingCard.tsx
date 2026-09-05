"use client";

/** Shared finding UI for Cyber/AppSec/Contracts/Protocols. Renders text only (XSS-safe). */
export interface SharedFinding {
  id: string;
  source?: string;
  severity?: string;
  confidence?: string;
  title: string;
  endpoint?: string | null;
  flow?: string | null;
  contract?: string | null;
  function?: string | null;
  status?: string;
  evidence_ref?: string | null;
  retest_status?: string | null;
  description?: string;
  remediation?: string;
  impact?: Record<string, string>;
}

export function FindingCard({
  finding,
  actions,
}: {
  finding: SharedFinding;
  actions?: React.ReactNode;
}) {
  const target =
    finding.endpoint || finding.flow || finding.contract || finding.evidence_ref || "—";
  return (
    <article
      data-testid={`finding-${finding.id}`}
      aria-label={`Finding ${finding.id}`}
      className="rounded border border-zinc-800 p-3 text-sm"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="mono rounded border border-zinc-700 px-2 py-0.5 text-xs">{finding.id}</span>
        <span className="rounded border border-red-800 px-2 py-0.5 text-xs text-red-300">
          {finding.severity || "UNKNOWN"}
        </span>
        <span className="rounded border border-zinc-700 px-2 py-0.5 text-xs text-zinc-300">
          {finding.status || "OPEN"}
        </span>
        {finding.confidence && (
          <span className="text-xs text-zinc-500">conf {finding.confidence}</span>
        )}
        {finding.source && <span className="text-xs text-zinc-500">{finding.source}</span>}
      </div>
      <h3 className="mt-2 font-semibold">{finding.title}</h3>
      <p className="mono mt-1 text-xs text-cyan-300">{target}</p>
      {finding.description && <p className="mt-2 text-zinc-300">{finding.description}</p>}
      {finding.remediation && (
        <p className="mt-1 text-xs text-zinc-400">Fix: {finding.remediation}</p>
      )}
      {finding.impact && Object.keys(finding.impact).length > 0 && (
        <dl className="mt-2 grid grid-cols-2 gap-1 text-xs md:grid-cols-3">
          {Object.entries(finding.impact).map(([k, v]) => (
            <div key={k} className="flex justify-between rounded border border-zinc-800 px-2 py-1">
              <dt className="text-zinc-500">{k}</dt>
              <dd className="mono">{v}</dd>
            </div>
          ))}
        </dl>
      )}
      {finding.retest_status && (
        <p className="mt-2 text-xs text-zinc-500">Retest: {finding.retest_status}</p>
      )}
      {actions && <div className="mt-2 flex flex-wrap gap-2 text-xs">{actions}</div>}
    </article>
  );
}
