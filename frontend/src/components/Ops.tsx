"use client";
import { useState } from "react";
import { ERROR_HELP, normError } from "@/lib/api";

/** Normalized error display: what failed, why, what to do, optional retry. Never raw tracebacks. */
export function ErrorNote({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  if (!error) return null;
  const { code, message } = normError(error);
  const help = ERROR_HELP[code] || "Retry, or check system health.";
  return (
    <p role="alert" className="rounded border border-red-800 bg-red-950 p-3 text-sm">
      <span className="mono text-xs text-red-300">{code}</span>: {message}
      <span className="block text-xs text-zinc-400">{help}</span>
      {onRetry && (
        <button onClick={onRetry} className="mt-1 rounded border border-red-700 px-2 py-0.5 text-xs">
          Retry
        </button>
      )}
    </p>
  );
}

/** Async action button with loading/success/failed/disabled-with-reason states. Never a dead button. */
export function ActionButton({
  label,
  busyLabel,
  onRun,
  disabledReason,
  kind,
  testid,
}: {
  label: string;
  busyLabel?: string;
  onRun: () => Promise<void>;
  disabledReason?: string;
  kind?: "primary" | "danger" | "ghost";
  testid?: string;
}) {
  const [busy, setBusy] = useState(false);
  const cls =
    kind === "primary"
      ? "bg-cyan-500 text-black font-semibold"
      : kind === "danger"
        ? "border border-red-700 text-red-200"
        : "border border-zinc-700 text-zinc-200";
  return (
    <button
      data-testid={testid}
      type="button"
      disabled={busy || Boolean(disabledReason)}
      title={disabledReason || ""}
      onClick={async () => {
        setBusy(true);
        try {
          await onRun();
        } finally {
          setBusy(false);
        }
      }}
      className={`ops-button rounded px-3 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50 ${cls}`}
    >
      {busy ? busyLabel || `${label}…` : label}
      {disabledReason && !busy ? ` (${disabledReason})` : ""}
    </button>
  );
}

/** Small loading / empty placeholders for consistent states. */
export function Loading({ what }: { what?: string }) {
  return <p className="eyebrow">&gt; loading{what ? ` ${what}` : ""}...</p>;
}

export function Empty({ what }: { what: string }) {
  return <p className="text-sm text-zinc-500">&gt; NO {what.toUpperCase()} FOUND. Empty state, not fake data.</p>;
}

/** Generic key/value grid for detail DTOs (unknown-safe). */
export function Facts({ facts }: { facts: Array<[string, string]> }) {
  return (
    <dl className="grid gap-1 text-xs md:grid-cols-2">
      {facts.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-2 rounded border border-zinc-800 px-2 py-1">
          <dt className="text-zinc-500">{k}</dt>
          <dd className="mono break-all text-right">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
