import { StatusBadge } from "./StatusBadge";

export function AttemptTimeline({ attempts }: { attempts: Array<Record<string, unknown>> }) {
  if (!attempts?.length) return <p className="text-sm text-zinc-500">No attempts yet.</p>;
  return (
    <ol className="space-y-3" data-testid="attempt-timeline">
      {attempts.map((a, i) => (
        <li key={i} className="rounded border border-zinc-800 p-3 text-sm">
          <div className="flex items-center gap-2">
            <strong>Attempt {(a.index as number) ?? i + 1}</strong>
            <StatusBadge status={String(a.status || "UNKNOWN")} />
            {typeof a.verifier_score === "number" && (
              <span className="mono text-xs text-zinc-400">
                {String(a.verifier_verdict)} {String(a.verifier_score)}/100
              </span>
            )}
          </div>
          <div className="mono mt-1 text-xs text-zinc-400">
            Agent: {String(a.agent)} · Model: {String(a.model)} · {String(a.duration_seconds)}s ·
            fp={String(a.patch_fingerprint)}
          </div>
          {Boolean(a.retry_reason) && (
            <p className="mt-1 text-xs text-amber-300">
              Retry reason: {String(a.retry_reason)}. Next: same agent + exact verifier evidence.
            </p>
          )}
        </li>
      ))}
    </ol>
  );
}
