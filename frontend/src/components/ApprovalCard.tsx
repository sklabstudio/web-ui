"use client";

export function ApprovalCard({
  approval,
  onApprove,
  onReject,
}: {
  approval: { reason: string; budget?: string; agent?: string; provider?: string };
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <div
      role="alertdialog"
      aria-label="Approval required"
      className="rounded border border-amber-600 bg-amber-950 p-4"
      data-testid="approval-card"
    >
      <h3 className="font-semibold text-amber-200">Approval required</h3>
      <p className="mt-1 text-sm">{approval.reason}</p>
      <p className="mono mt-1 text-xs">
        Budget: {approval.budget || "Unknown"} · Agent: {approval.agent} · Provider:{" "}
        {approval.provider}
      </p>
      <p className="mt-1 text-xs text-amber-300">
        Cost estimates come from the backend only. Nothing is approved automatically.
      </p>
      <div className="mt-3 flex gap-2">
        <button
          onClick={onApprove}
          className="rounded bg-amber-500 px-3 py-1 text-sm font-semibold text-black"
        >
          Approve once
        </button>
        <button onClick={onReject} className="rounded border border-amber-500 px-3 py-1 text-sm">
          Reject
        </button>
      </div>
    </div>
  );
}
