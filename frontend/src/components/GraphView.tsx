"use client";
import { useMemo, useState } from "react";

/**
 * Generic bounded graph view for API map / authority / protocol / asset-flow /
 * evidence / dependency graphs. Table-first with optional node list; never a
 * full graph editor. Includes text alternative for accessibility.
 */
export interface GraphEdge {
  from: string;
  to: string;
  label?: string;
}

export function GraphView({
  nodes,
  edges,
  title,
}: {
  nodes: string[];
  edges: GraphEdge[] | string[][];
  title?: string;
}) {
  const [q, setQ] = useState("");
  const normEdges: GraphEdge[] = useMemo(
    () =>
      (edges as unknown[]).map((e) =>
        Array.isArray(e) ? { from: String(e[0]), to: String(e[1]) } : (e as GraphEdge)
      ),
    [edges]
  );
  const shown = useMemo(() => {
    const query = q.toLowerCase();
    const n = nodes.filter((x) => x.toLowerCase().includes(query)).slice(0, 200);
    const e = normEdges
      .filter(
        (x) =>
          !query || x.from.toLowerCase().includes(query) || x.to.toLowerCase().includes(query)
      )
      .slice(0, 200);
    return { n, e };
  }, [nodes, normEdges, q]);
  return (
    <section aria-label={title || "Graph"} className="rounded border border-zinc-800 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold">{title || "Graph"}</h3>
        <label className="text-xs">
          Search{" "}
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Search graph"
            className="rounded bg-zinc-900 px-2 py-1"
          />
        </label>
      </div>
      <p className="mt-1 text-xs text-zinc-500">
        {shown.n.length} nodes · {shown.e.length} edges (bounded to 200). Table fallback below.
      </p>
      <ul className="mono mt-2 space-y-1 text-xs" data-testid="graph-edges">
        {shown.e.map((e, i) => (
          <li key={i} className="rounded border border-zinc-800 px-2 py-1">
            {e.from} → {e.to}
            {e.label ? ` (${e.label})` : ""}
          </li>
        ))}
        {shown.e.length === 0 && <li className="text-zinc-500">No edges match.</li>}
      </ul>
      <details className="mt-2 text-xs">
        <summary className="cursor-pointer text-zinc-400">Text alternative (nodes)</summary>
        <p className="mono mt-1 text-zinc-300">{shown.n.join(", ") || "No nodes."}</p>
      </details>
    </section>
  );
}
