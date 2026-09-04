"use client";
import { StatusBadge } from "./StatusBadge";

/** Module status card: never fakes READY; shows Not installed when absent. */
export function ModuleStatusCard({
  title,
  state,
  detail,
  extra,
}: {
  title: string;
  state?: string;
  detail?: string;
  extra?: React.ReactNode;
}) {
  const s = state || "UNKNOWN";
  const unavailable = ["NOT_INSTALLED", "UNAVAILABLE", "UNKNOWN"].includes(s);
  return (
    <div data-testid={`module-${title}`} className="rounded border border-zinc-800 p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{title}</h3>
        <StatusBadge status={s} />
      </div>
      {unavailable ? (
        <p className="mt-2 text-sm text-zinc-500">Not installed{detail ? ` — ${detail}` : ""}</p>
      ) : (
        <>
          {detail && <p className="mt-1 text-xs text-zinc-500">{detail}</p>}
          {extra}
        </>
      )}
    </div>
  );
}
