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
