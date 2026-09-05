"use client";
import Link from "next/link";

const LINKS = [
  ["Dashboard", "/"],
  ["Repositories", "/repositories"],
  ["New Task", "/tasks/new"],
  ["Runs", "/runs"],
  ["Agents", "/agents"],
  ["Providers", "/providers"],
  ["Skills", "/skills"],
  ["Environments", "/environments"],
  ["Security", "/security"],
  ["Contracts", "/contracts"],
  ["Protocols", "/protocols"],
  ["Modules", "/modules"],
  ["Benchmarks", "/benchmarks"],
  ["Prompt Experiments", "/prompt-experiments"],
  ["Settings", "/settings"],
];

export function Nav() {
  return (
    <nav aria-label="Main" className="mx-auto max-w-6xl overflow-x-auto px-4 pb-3">
      <ul className="flex gap-2 text-sm">
        {LINKS.map(([label, href]) => (
          <li key={href}>
            <Link
              href={href}
              className="rounded border border-zinc-800 px-2 py-1 text-zinc-300 hover:border-zinc-500 hover:text-white"
            >
              {label}
            </Link>
          </li>
        ))}
        <li aria-disabled="true" title="Legacy packs">
          <span className="rounded border border-dashed border-zinc-800 px-2 py-1 text-zinc-600">
            CodeTrials
          </span>
        </li>
      </ul>
    </nav>
  );
}
