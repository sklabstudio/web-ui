"use client";
import { useState } from "react";

export default function LoginPage() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ token: token || undefined, password: password || undefined }),
      });
      if (!res.ok) throw new Error("Invalid credentials");
      window.location.href = "/";
    } catch (err) {
      setMsg("Invalid credentials");
    }
  }
  return (
    <div className="mx-auto max-w-sm space-y-4">
      <h1 className="text-2xl font-bold">Sign in</h1>
      <form onSubmit={submit} className="space-y-2 text-sm" data-testid="login-form">
        <label className="block">Token
          <input type="password" autoComplete="off" value={token} onChange={(e) => setToken(e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Token" />
        </label>
        <label className="block">Password (if enabled)
          <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full rounded bg-zinc-900 p-2" aria-label="Password" />
        </label>
        <button className="rounded bg-cyan-500 px-3 py-1 font-semibold text-black">Sign in</button>
      </form>
      {msg && <p role="alert" className="text-sm text-red-300">{msg}</p>}
    </div>
  );
}
