import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorNote } from "../Ops";
import { Timeline } from "../Timeline";
import { GraphView } from "../GraphView";

describe("v0.3 error UX", () => {
  it("shows code, message and actionable help", () => {
    render(<ErrorNote error={new Error("[AGENT_UNAVAILABLE] no agents installed")} />);
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("AGENT_UNAVAILABLE");
    expect(alert.textContent).toContain("no agents installed");
    expect(alert.textContent).toContain("Agents");
  });
  it("shows retry action when provided", () => {
    render(<ErrorNote error={new Error("boom")} onRetry={() => {}} />);
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });
});

describe("v0.3 live timeline", () => {
  it("labels known events and renders unknown types safely", () => {
    render(
      <Timeline
        events={[
          { seq: 1, type: "AGENT_STARTED", ts: "t", message: "go", stream: "stdout", data: {} },
          { seq: 2, type: "FUTURE_WEIRD_EVENT", ts: "t", message: "x", stream: "stdout", data: {} },
        ]}
      />
    );
    const tl = screen.getByTestId("run-timeline");
    expect(tl.textContent).toContain("Agent started");
    expect(tl.textContent).toContain("FUTURE_WEIRD_EVENT");
  });
  it("handles empty state", () => {
    render(<Timeline events={[]} />);
    expect(document.body.textContent).toContain("No events yet");
  });
});

describe("v0.3 graph interactions", () => {
  it("supports zoom controls and node selection", () => {
    render(<GraphView nodes={["a", "b"]} edges={[{ from: "a", to: "b" }]} title="G" />);
    expect(screen.getByRole("button", { name: "Zoom in" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Fit" })).toBeTruthy();
  });
});
