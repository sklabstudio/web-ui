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
    const detail = (body as { detail?: { code?: string; message?: string }; message?: string }) || {};
    const code = detail.detail?.code || "";
    const message = detail.detail?.message || detail.message || `API ${res.status}`;
    throw new Error(code ? `[${code}] ${message}` : message);
  }
  return (await res.json()) as T;
}

export const ERROR_HELP: Record<string, string> = {
  AUTH_REQUIRED: "Sign in, then retry.",
  PROVIDER_UNAVAILABLE: "Check Providers — a connection may need a key or login.",
  AGENT_UNAVAILABLE: "Check Agents — no usable agent is installed. Install one or use mock mode for trials.",
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
  NOT_FOUND: "Not found. It may have been removed — refresh the list.",
  BAD_REQUEST: "Check the highlighted fields and retry.",
};

/** Extract a normalized {code, message} from any API failure. */
export function normError(e: unknown): { code: string; message: string } {
  const raw = String((e as Error)?.message || e || "Request failed");
  // api() throws Error(message) where message may be the backend detail message.
  return { code: guessCode(raw), message: raw.replace(/^Error:\s*/, "") };
}

function guessCode(msg: string): string {
  const m = msg.match(/\[([A-Z_]+)\]/);
  if (m) return m[1];
  for (const code of Object.keys(ERROR_HELP)) {
    if (msg.toLowerCase().includes(code.toLowerCase().replace(/_/g, " ").slice(0, 12))) return code;
  }
  if (/401|unauthor|sign in/i.test(msg)) return "AUTH_REQUIRED";
  if (/404|not found/i.test(msg)) return "NOT_FOUND";
  if (/invalid|rejected|must be/i.test(msg)) return "BAD_REQUEST";
  return "MODULE_UNAVAILABLE";
}
