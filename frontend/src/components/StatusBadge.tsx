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
  const cls = color[status] || "border-zinc-700 text-zinc-300";
  return (
    <span className={`mono rounded border px-2 py-0.5 text-xs ${cls}`}>{status}</span>
  );
}
