const BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    credentials: "include",
  });
  if (res.status === 401 && typeof window !== "undefined") {
    const p = window.location.pathname;
    if (!p.startsWith("/login")) window.location.href = "/login";
  }
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      body = null;
    }
    throw new Error((body as { message?: string })?.message || `API ${res.status}`);
  }
  return (await res.json()) as T;
}

export const ERROR_HELP: Record<string, string> = {
  AUTH_REQUIRED: "Sign in, then retry.",
  PROVIDER_UNAVAILABLE: "Check Providers — a connection may need a key or login.",
  AGENT_UNAVAILABLE: "Check Agents — the agent may not be installed.",
  BUDGET_EXHAUSTED: "Raise the budget or use a free agent.",
  APPROVAL_REQUIRED: "Approve the paid step to continue.",
  VERIFICATION_FAILED: "Open the verification panel for failing checks.",
  RUN_CANCELLED: "Run was cancelled. Resume or start a new task.",
};
