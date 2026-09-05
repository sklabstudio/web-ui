"use client";
import type { RunEvent } from "@/lib/types";

/** Friendly labels for known lifecycle events; unknown types render safely as-is. */
const LABELS: Record<string, string> = {
  TASK_CREATED: "Task created",
  RUN_CREATED: "Run created",
  INSPECTION_STARTED: "Inspecting repository",
  INSPECTION_COMPLETED: "Repository inspected",
  CONTEXT_READY: "Context ready",
  PLAN_CREATED: "Plan created",
  SKILLS_SELECTED: "Skills selected",
  AGENT_SELECTED: "Agent selected",
  AGENT_STARTED: "Agent started",
  PROVIDER_SELECTED: "Provider selected",
  WORKSPACE_READY: "Workspace ready",
  ATTEMPT_STARTED: "Attempt started",
  AGENT_EVENT: "Agent progress",
  PATCH_CREATED: "Patch created",
  PATCH_CAPTURED: "Patch captured",
  VERIFICATION_STARTED: "Verification started",
  VERIFICATION_COMPLETED: "Verification completed",
  VERIFICATION_FAILED: "Verification failed",
  VERIFIED_SUCCESS: "Verified success",
  RETRY_DECIDED: "Retry decided",
  RETRY_STARTED: "Retry started",
  APPROVAL_REQUIRED: "Approval required",
  APPROVAL_GRANTED: "Approval granted",
  APPROVAL_REJECTED: "Approval rejected",
  RUN_COMPLETED: "Run completed",
  RUN_FAILED: "Run failed",
  RUN_CANCELLED: "Run cancelled",
  SECURITY_SCAN_STARTED: "Security scan started",
  BROWSER_FLOW_STARTED: "Browser flow started",
  API_DISCOVERED: "API discovered",
  FINDING_CREATED: "Finding created",
  SIMULATION_STARTED: "Simulation started",
  SIMULATION_COMPLETED: "Simulation completed",
  CONTRACT_COMPILE_STARTED: "Compile started",
  CONTRACT_TEST_STARTED: "Tests started",
  FUZZ_STARTED: "Fuzzing started",
  INVARIANT_RESULT: "Invariant result",
  UPGRADE_REVIEW_COMPLETED: "Upgrade review completed",
  PROTOCOL_MAP_READY: "Protocol map ready",
  SPEC_DERIVED: "Spec derived",
  INVARIANT_DERIVED: "Invariant derived",
  ECONOMIC_SIM_STARTED: "Economic simulation started",
  ASSURANCE_UPDATED: "Assurance updated",
  MONITOR_ALERT: "Monitor alert",
  INCIDENT_RECONSTRUCTED: "Incident reconstructed",
};

export function eventLabel(type: string): string {
  return LABELS[type] || type.replace(/_/g, " ").toLowerCase();
}

/** Readable live timeline. Unknown event types render safely, never crash. */
export function Timeline({ events }: { events: RunEvent[] }) {
  return (
    <ol className="space-y-1 text-xs" data-testid="run-timeline" aria-label="Run timeline">
      {events.length === 0 && <li className="text-sm text-zinc-500">No events yet.</li>}
      {events.map((e) => (
        <li key={e.seq} className="flex gap-2 rounded border border-zinc-800 px-2 py-1">
          <span className="mono shrink-0 text-zinc-500">#{e.seq}</span>
          <span className="shrink-0 font-semibold text-cyan-300">{eventLabel(e.type)}</span>
          <span className="mono shrink-0 text-zinc-600">{e.type}</span>
          <span className="break-words text-zinc-300">{e.message}</span>
          <span className="mono ml-auto shrink-0 text-zinc-600">{e.ts}</span>
        </li>
      ))}
    </ol>
  );
}
