"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

function List({ title, path, render }: { title: string; path: string; render: (x: Record<string, unknown>) => React.ReactNode }) {
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => {
    api<Array<Record<string, unknown>>>(path).then(setItems).catch(() => {});
  }, [path]);
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-bold">{title}</h1>
      <ul className="space-y-2 text-sm">
        {items.map((x, i) => (
          <li key={i} className="rounded border border-zinc-800 p-3">{render(x)}</li>
        ))}
        {items.length === 0 && <li className="text-zinc-500">No data — empty state, not fake metrics.</li>}
      </ul>
    </div>
  );
}

export function EnvPage() {
  return <List title="Environments" path="/api/environments" render={(e) => (
    <><span className="mono font-semibold">{String(e.name)}</span> · {String(e.executor)} · fp={String(e.fingerprint)} · {String(e.image)}</>
  )} />;
}
export function BenchPage() {
  return <List title="Benchmarks" path="/api/benchmarks" render={(b) => (
    <><span className="mono font-semibold">{String(b.id)}</span> — {String(b.title)} · {String(b.stack)} · {String(b.difficulty)}</>
  )} />;
}
export function TrialsPage() {
  return <List title="CodeTrials" path="/api/codetrials" render={(c) => (
    <><span className="mono font-semibold">{String(c.id)}</span> — {String(c.task)} · winner={String(c.winner)}</>
  )} />;
}
export function PromptsPage() {
  return <List title="Prompt Experiments" path="/api/promptbench" render={(p) => (
    <><span className="mono font-semibold">{String(p.id)}</span> — {String(p.name)} · variants={String(p.variants)}</>
  )} />;
}
export function SkillsPage() {
  return <List title="Skills" path="/api/skills" render={(s) => (
    <><span className="mono font-semibold">{String(s.id)}</span> · {String(s.enabled ? "enabled" : "disabled")} · {String(s.source)} · trust={String(s.trust_level)}</>
  )} />;
}
