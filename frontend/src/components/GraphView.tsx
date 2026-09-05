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
  const [zoom, setZoom] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);
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
  const related = useMemo(() => {
    if (!selected) return [];
    return normEdges.filter((e) => e.from === selected || e.to === selected);
  }, [selected, normEdges]);
  return (
    <section aria-label={title || "Graph"} className="rounded border border-zinc-800 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold">{title || "Graph"}</h3>
        <div className="flex items-center gap-2 text-xs">
          <label>
            Search{" "}
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Search graph"
              className="rounded bg-zinc-900 px-2 py-1"
            />
          </label>
          <div className="flex items-center gap-1" role="group" aria-label="Zoom">
            <button
              onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)))}
              className="rounded border border-zinc-700 px-2 py-1"
              aria-label="Zoom out"
            >
              −
            </button>
            <span className="mono text-zinc-400" aria-live="polite">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.min(2.5, +(z + 0.25).toFixed(2)))}
              className="rounded border border-zinc-700 px-2 py-1"
              aria-label="Zoom in"
            >
              +
            </button>
            <button
              onClick={() => {
                setZoom(1);
                setSelected(null);
              }}
              className="rounded border border-zinc-700 px-2 py-1"
            >
              Fit
            </button>
          </div>
        </div>
      </div>
      <p className="mt-1 text-xs text-zinc-500">
        {shown.n.length} nodes · {shown.e.length} edges (bounded to 200). Table fallback below.
      </p>
      <div className="mt-2 max-h-72 overflow-auto rounded border border-zinc-900 p-2">
        <ul
          className="mono space-y-1 text-xs"
          data-testid="graph-edges"
          style={{ fontSize: `${0.75 * zoom}rem` }}
        >
          {shown.e.map((e, i) => (
            <li key={i} className="rounded border border-zinc-800 px-2 py-1">
              <button
                onClick={() => setSelected(e.from)}
                className="text-cyan-300 underline"
                title="Select source node"
              >
                {e.from}
              </button>{" "}
              →{" "}
              <button
                onClick={() => setSelected(e.to)}
                className="text-cyan-300 underline"
                title="Select target node"
              >
                {e.to}
              </button>
              {e.label ? ` (${e.label})` : ""}
            </li>
          ))}
          {shown.e.length === 0 && <li className="text-zinc-500">No edges match.</li>}
        </ul>
      </div>
      {selected && (
        <div className="mt-2 rounded border border-cyan-800 p-2 text-xs" data-testid="graph-node-detail">
          <div className="flex items-center justify-between">
            <strong className="mono">{selected}</strong>
            <button onClick={() => setSelected(null)} className="rounded border border-zinc-700 px-2 py-0.5">
              Clear
            </button>
          </div>
          <ul className="mono mt-1 space-y-0.5 text-zinc-300">
            {related.length === 0 && <li>No edges touch this node.</li>}
            {related.slice(0, 50).map((e, i) => (
              <li key={i}>
                {e.from} → {e.to}
                {e.label ? ` (${e.label})` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      <details className="mt-2 text-xs">
        <summary className="cursor-pointer text-zinc-400">Text alternative (nodes)</summary>
        <p className="mono mt-1 text-zinc-300">{shown.n.join(", ") || "No nodes."}</p>
      </details>
    </section>
  );
}
