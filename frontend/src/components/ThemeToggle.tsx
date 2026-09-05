"use client";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState("phosphor");
  useEffect(() => {
    const t = localStorage.getItem("sklab-theme") || "phosphor";
    setTheme(t);
    document.documentElement.dataset.theme = t === "amber" ? "amber" : "phosphor";
  }, []);
  function cycle() {
    const next = theme === "amber" ? "phosphor" : "amber";
    setTheme(next);
    localStorage.setItem("sklab-theme", next);
    document.documentElement.dataset.theme = next;
  }
  return (
    <button
      onClick={cycle}
      aria-label="Toggle theme"
      className="rounded border border-zinc-700 px-2 py-1 text-xs"
    >
      Mode: {theme}
    </button>
  );
}
