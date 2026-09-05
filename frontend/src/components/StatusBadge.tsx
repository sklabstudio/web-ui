export function StatusBadge({ status }: { status: string }) {
  const color: Record<string, string> = {
    COMPLETED: "border-emerald-600 text-emerald-300",
    VERIFIED_SUCCESS: "border-emerald-600 text-emerald-300",
    ACCEPT: "border-emerald-600 text-emerald-300",
    FAILED: "border-red-700 text-red-300",
    REJECT: "border-red-700 text-red-300",
    BLOCKED: "border-amber-600 text-amber-300",
    WAITING_FOR_APPROVAL: "border-amber-600 text-amber-300",
    RUNNING_AGENT: "border-cyan-600 text-cyan-300",
    VERIFYING: "border-cyan-600 text-cyan-300",
  };
  const extra: Record<string, string> = {
     READY: "border-emerald-600 text-emerald-300",
     INSTALLED: "border-emerald-600 text-emerald-300",
     AUTHENTICATED: "border-emerald-600 text-emerald-300",
     CONFIGURED: "border-emerald-600 text-emerald-300",
    VERIFIED: "border-emerald-600 text-emerald-300",
    FIXED_VERIFIED: "border-emerald-600 text-emerald-300",
    PASS: "border-emerald-600 text-emerald-300",
    SAFE: "border-emerald-600 text-emerald-300",
    OPEN: "border-red-700 text-red-300",
    CONFIRMED: "border-red-700 text-red-300",
    FAILED: "border-red-700 text-red-300",
    BLOCKED: "border-amber-600 text-amber-300",
    REVIEW_REQUIRED: "border-amber-600 text-amber-300",
    STALE: "border-amber-600 text-amber-300",
    PARTIAL: "border-amber-600 text-amber-300",
     NOT_INSTALLED: "border-zinc-700 text-zinc-500",
     NOT_AUTHENTICATED: "border-amber-600 text-amber-300",
     NOT_CONFIGURED: "border-amber-600 text-amber-300",
    UNAVAILABLE: "border-zinc-700 text-zinc-500",
    UNKNOWN: "border-zinc-700 text-zinc-400",
    NOT_TESTED: "border-zinc-700 text-zinc-400",
    INCONCLUSIVE: "border-zinc-700 text-zinc-300",
  };
  const cls = color[status] || extra[status] || "border-zinc-700 text-zinc-300";
  return (
    <span className={`mono rounded border px-2 py-0.5 text-xs ${cls}`}>{status}</span>
  );
}
