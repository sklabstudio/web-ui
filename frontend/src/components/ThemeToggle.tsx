"use client";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState("dark");
  useEffect(() => {
    const t = localStorage.getItem("sklab-theme") || "dark";
    setTheme(t);
    document.documentElement.classList.toggle("light", t === "light");
  }, []);
  function cycle() {
    const next = theme === "dark" ? "light" : "system";
    const resolved = next === "system" ? "dark" : next;
    setTheme(next);
    localStorage.setItem("sklab-theme", next);
    document.documentElement.classList.toggle("light", resolved === "light");
  }
  return (
    <button
      onClick={cycle}
      aria-label="Toggle theme"
      className="rounded border border-zinc-700 px-2 py-1 text-xs"
    >
      Theme: {theme}
    </button>
  );
}
