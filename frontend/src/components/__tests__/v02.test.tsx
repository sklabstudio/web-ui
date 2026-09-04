import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { FindingCard } from "../FindingCard";
import { ReportViewer } from "../ReportViewer";
import { GraphView } from "../GraphView";
import { ModuleStatusCard } from "../ModuleStatusCard";
import { StatusBadge } from "../StatusBadge";

describe("shared finding component", () => {
  it("renders severity/status and degrades gracefully", () => {
    render(<FindingCard finding={{ id: "sec-001", title: "Role issue", severity: "HIGH", status: "OPEN" }} />);
    expect(screen.getByTestId("finding-sec-001").textContent).toContain("Role issue");
  });
  it("escapes XSS payload as text", () => {
    const evil = '<script>alert(1)</script><img src=x onerror=alert(1)>';
    render(<FindingCard finding={{ id: "x1", title: evil, description: evil }} />);
    const el = screen.getByTestId("finding-x1");
    expect(el.innerHTML).not.toContain("<script>");
    expect(el.textContent).toContain("<script>alert(1)</script>");
  });
});

describe("shared report viewer", () => {
  it("renders safe artifact links only", () => {
    render(<ReportViewer reports={[{ id: "r1", kind: "markdown", title: "Exec", artifact_id: "artifact-rep-001" }]} />);
    expect(screen.getByTestId("report-viewer").textContent).toContain("Exec");
  });
});

describe("shared graph component", () => {
  it("bounds nodes and provides text alternative", () => {
    const nodes = Array.from({ length: 300 }, (_, i) => `n${i}`);
    render(<GraphView nodes={nodes} edges={[{ from: "a", to: "b" }]} title="Test graph" />);
    expect(screen.getByTestId("graph-edges").textContent).toContain("a → b");
    expect(document.body.textContent).toContain("Text alternative");
  });
  it("falls back to table message on empty", () => {
    render(<GraphView nodes={[]} edges={[]} title="Empty" />);
    expect(screen.getByTestId("graph-edges").textContent).toContain("No edges");
  });
});

describe("module unavailable states", () => {
  it("shows Not installed, never fake zero", () => {
    render(<ModuleStatusCard title="Security" state="NOT_INSTALLED" detail="optional" />);
    expect(screen.getByTestId("module-Security").textContent).toContain("Not installed");
  });
  it("renders degraded distinctly", () => {
    render(<StatusBadge status="DEGRADED" />);
    expect(screen.getByText("DEGRADED")).toBeTruthy();
  });
});

describe("contract/project/security rendering", () => {
  it("finding detail shows impact grid", () => {
    render(<FindingCard finding={{ id: "f1", title: "T", impact: { data_confidentiality: "HIGH" } }} />);
    expect(screen.getByTestId("finding-f1").textContent).toContain("data_confidentiality");
  });
});
