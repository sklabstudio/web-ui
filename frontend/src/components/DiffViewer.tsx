"use client";
import { useState } from "react";

/** Read-only diff viewer with unified/side-by-side toggle. Text-only, no HTML injection. */
export function DiffViewer({ patch }: { patch: string }) {
  const [mode, setMode] = useState<"unified" | "side">("unified");
  const lines = (patch || "").split("\n");
  const added = lines.filter((l) => l.startsWith("+") && !l.startsWith("+++")).length;
  const removed = lines.filter((l) => l.startsWith("-") && !l.startsWith("---")).length;
  return (
    <section aria-label="Patch diff" className="rounded border border-zinc-800">
      <div className="flex items-center gap-2 border-b border-zinc-800 p-2 text-xs">
        <span className="mono">
          +{added} / -{removed}
        </span>
        <button
          onClick={() => setMode(mode === "unified" ? "side" : "unified")}
          className="rounded border border-zinc-700 px-2 py-1"
        >
          View: {mode === "unified" ? "unified" : "side-by-side"}
        </button>
        <button
          onClick={() => navigator.clipboard?.writeText(patch)}
          className="rounded border border-zinc-700 px-2 py-1"
        >
          Copy patch
        </button>
      </div>
      <pre
        data-testid="diff-view"
        className={`mono overflow-auto p-3 text-xs leading-5 ${
          mode === "side" ? "grid" : ""
        }`}
      >
        {lines.slice(0, 800).map((l, i) => (
          <div
            key={i}
            className={
              l.startsWith("+") && !l.startsWith("+++")
                ? "bg-emerald-950 text-emerald-200"
                : l.startsWith("-") && !l.startsWith("---")
                  ? "bg-red-950 text-red-200"
                  : "text-zinc-300"
            }
          >
            {l}
          </div>
        ))}
      </pre>
    </section>
  );
}
