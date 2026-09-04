export type RunStatus =
  | "CREATED" | "INSPECTING" | "PLANNING" | "WAITING_FOR_APPROVAL"
  | "PREPARING" | "RUNNING_AGENT" | "CAPTURING_PATCH" | "VERIFYING"
  | "RETRYING" | "COMPLETED" | "FAILED" | "CANCELLED" | "BLOCKED";

export interface RunEvent {
  seq: number;
  type: string;
  ts: string;
  message: string;
  stream?: string;
  data?: Record<string, unknown>;
}

export interface RunSummary {
  id: string;
  task_summary: string;
  repo: string;
  status: string;
  attempts: number;
  winning_agent?: string | null;
  verification: string;
  duration_seconds: number;
  cost?: string | null;
}

export type ModuleState = "READY" | "DEGRADED" | "UNAVAILABLE" | "NOT_INSTALLED" | "UNKNOWN";

export interface ModuleStatus {
  name: string;
  capability: string;
  state: ModuleState;
  version?: string | null;
  detail?: string;
  mock?: boolean;
}

export interface SharedFinding {
  id: string;
  source?: string;
  severity?: string;
  confidence?: string;
  title: string;
  endpoint?: string | null;
  flow?: string | null;
  contract?: string | null;
  status?: string;
  evidence_ref?: string | null;
  retest_status?: string | null;
  description?: string;
}

export const EXTENDED_EVENTS = [
  "SECURITY_SCAN_STARTED", "BROWSER_FLOW_STARTED", "API_DISCOVERED",
  "FINDING_CREATED", "SIMULATION_STARTED", "SIMULATION_COMPLETED",
  "CONTRACT_COMPILE_STARTED", "CONTRACT_TEST_STARTED", "FUZZ_STARTED",
  "INVARIANT_RESULT", "UPGRADE_REVIEW_COMPLETED",
  "PROTOCOL_MAP_READY", "SPEC_DERIVED", "INVARIANT_DERIVED",
  "ECONOMIC_SIM_STARTED", "ASSURANCE_UPDATED", "MONITOR_ALERT",
  "INCIDENT_RECONSTRUCTED",
];
