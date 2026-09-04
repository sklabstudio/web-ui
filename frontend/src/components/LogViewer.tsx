"use client";
import { useMemo, useState } from "react";
import type { RunEvent } from "@/lib/types";

/** Safe log viewer: renders untrusted text only, no HTML injection. */
export function LogViewer({ events }: { events: RunEvent[] }) {
  const [follow, setFollow] = useState(true);
  const [query, setQuery] = useState("");
  const [paused, setPaused] = useState(false);
  const shown = useMemo(() => {
    const q = query.toLowerCase();
    const list = events.slice(-500);
    if (!q) return list;
    return list.filter((e) => e.message.toLowerCase().includes(q));
  }, [events, query]);
  return (
    <section aria-label="Live logs" className="rounded border border-zinc-800">
      <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 p-2 text-xs">
        <label>
          Search{" "}
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="rounded bg-zinc-900 px-2 py-1"
            aria-label="Search logs"
          />
        </label>
        <button
          onClick={() => setFollow(!follow)}
          className="rounded border border-zinc-700 px-2 py-1"
          aria-pressed={follow}
        >
          Auto-follow: {follow ? "on" : "off"}
        </button>
        <button
          onClick={() => setPaused(!paused)}
          className="rounded border border-zinc-700 px-2 py-1"
          aria-pressed={paused}
        >
          {paused ? "Resume" : "Pause"}
        </button>
      </div>
      <div
        className="mono max-h-96 overflow-auto whitespace-pre-wrap p-3 text-xs leading-5"
        data-testid="log-view"
        aria-live={follow && !paused ? "polite" : "off"}
      >
        {(paused ? shown.slice(0, 50) : shown).map((e) => (
          <div key={e.seq} className={e.stream === "stderr" ? "text-amber-300" : "text-zinc-200"}>
            <span className="text-zinc-500">[{e.ts}] </span>
            <span className="text-cyan-400">[{e.type}] </span>
            {e.message}
          </div>
        ))}
      </div>
    </section>
  );
}
