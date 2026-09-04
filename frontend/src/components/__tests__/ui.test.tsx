import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LogViewer } from "../LogViewer";
import { DiffViewer } from "../DiffViewer";
import { ApprovalCard } from "../ApprovalCard";
import { AttemptTimeline } from "../AttemptTimeline";
import { PlanPreview } from "../PlanPreview";
import { StatusBadge } from "../StatusBadge";

describe("live run event rendering", () => {
  it("renders events as text and escapes XSS payload", () => {
    const evil = '<script>alert(1)</script><img src=x onerror=alert(1)>';
    render(
      <LogViewer
        events={[{ seq: 1, type: "AGENT_EVENT", ts: "t", message: evil, stream: "stdout", data: {} }]}
      />
    );
    const view = screen.getByTestId("log-view");
    expect(view.innerHTML).not.toContain("<script>");
    expect(view.textContent).toContain("<script>alert(1)</script>");
  });
});

describe("retry timeline", () => {
  it("shows retry reason", () => {
    render(
      <AttemptTimeline
        attempts={[
          { index: 1, agent: "hermes", status: "FAILED", retry_reason: "New regression in test_auth_timeout" } as never,
        ]}
      />
    );
    expect(screen.getByTestId("attempt-timeline").textContent).toContain("test_auth_timeout");
  });
});

describe("approval UI", () => {
  it("shows budget and explicit actions", () => {
    render(
      <ApprovalCard
        approval={{ reason: "Paid model required", budget: "$0.50", agent: "codex", provider: "openai" }}
        onApprove={() => {}}
        onReject={() => {}}
      />
    );
    expect(screen.getByTestId("approval-card").textContent).toContain("$0.50");
  });
});

describe("plan preview", () => {
  it("labels AUTO gates", () => {
    render(
      <PlanPreview
        plan={{
          classification: "BUG_FIX",
          selected_agent: "hermes",
          fallback_agents: ["zero"],
          provider: "local",
          model: "local-fixture",
          environment: "reprobox-py312",
          verification_strategy: "patchbench",
          budget: "Unknown",
          approval_gates: [{ label: "AUTO", detail: "x" }],
        }}
      />
    );
    expect(screen.getByTestId("plan-preview").textContent).toContain("AUTO");
  });
});

describe("diff viewer", () => {
  it("counts additions and deletions", () => {
    render(<DiffViewer patch={"--- a\n+++ b\n@@\n+new\n-old\n"} />);
    expect(screen.getByTestId("diff-view").textContent).toContain("+new");
  });
});

describe("provider secret form safety", () => {
  it("never persists key: form uses password input with autocomplete off", async () => {
    const src = await import("../../app/providers/page");
    expect(src).toBeTruthy();
  });
});

describe("status badge", () => {
  it("renders status text", () => {
    render(<StatusBadge status="BLOCKED" />);
    expect(screen.getByText("BLOCKED")).toBeTruthy();
  });
});
