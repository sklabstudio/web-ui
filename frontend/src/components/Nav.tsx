"use client";
import Link from "next/link";

const LINKS = [
  ["Home", "/"],
  ["Workspace", "/tasks/new"],
  ["Repos", "/repositories"],
  ["Runs", "/runs"],
  ["AppSec", "/security"],
  ["Contracts", "/contracts"],
  ["Protocols", "/protocols"],
  ["Skills", "/skills"],
  ["Agents", "/agents"],
  ["Providers", "/providers"],
  ["Modules", "/modules"],
  ["Settings", "/settings"],
];

export function Nav() {
  return (
    <nav aria-label="Main" className="mx-auto max-w-7xl overflow-x-auto px-4 pb-3">
      <ul className="flex gap-2 text-sm">
        {LINKS.map(([label, href]) => (
          <li key={href}>
            <Link
              href={href}
              className="rounded border border-zinc-800 px-2 py-1 text-zinc-300 hover:border-cyan-500 hover:text-white"
            >
              &gt; {label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
