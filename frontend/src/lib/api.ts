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
  MODULE_NOT_INSTALLED: "Optional module is not installed. Install it or use mock mode.",
  MODULE_UNAVAILABLE: "Module is temporarily unavailable. Retry later.",
  PRIVATE_MODULE_UNAVAILABLE: "Private module is not installed locally. Status shown only.",
  BROWSER_UNAVAILABLE: "Browser engine unavailable. Check AppSec Lab status.",
  ENGAGEMENT_NOT_FOUND: "Engagement not found. Pick an existing engagement.",
  CONTRACT_TOOL_UNAVAILABLE: "Contract tool not installed. See Toolchain page.",
  COMPILE_FAILED: "Compilation failed. Open build log.",
  TEST_FAILED: "Tests failed. Open test output.",
  FUZZ_COUNTEREXAMPLE: "Fuzzer found a counterexample. Open the trace.",
  INVARIANT_FAILED: "An invariant failed. Open the counterexample.",
  UPGRADE_BLOCKED: "Upgrade is blocked. Review storage/ABI diff.",
  ASSURANCE_STALE: "Assurance is stale. Re-run affected checks.",
  MONITOR_DISCONNECTED: "Monitor disconnected. Check chain endpoint.",
  INCIDENT_DATA_INCOMPLETE: "Incident data incomplete. Some fields unavailable.",
};
