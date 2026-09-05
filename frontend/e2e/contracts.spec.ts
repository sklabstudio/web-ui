import { test, expect } from "@playwright/test";

// C. Contract UI E2E (mock): login → Contracts → project → compile →
// analyze → finding → gas → report.
test("C. contracts: compile to report", async ({ page }) => {
  await page.goto("/contracts");
  await expect(page.getByRole("heading", { name: "Contracts" })).toBeVisible();
  await page.getByRole("tab", { name: "Projects" }).click();
  await expect(page.getByTestId("project-proj-demo")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "compile" }).first().click();
  await expect(page.getByText("compile: ok")).toBeVisible({ timeout: 15000 });
  await page.getByRole("tab", { name: "Analysis" }).click();
  await page.getByRole("button", { name: "Run analysis" }).click();
  await expect(page.getByText(/zero-address/i).first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("tab", { name: "Gas" }).click();
  await page.getByRole("button", { name: "Gas review" }).click();
  await expect(page.getByText(/Hotspots|hotspots/i).first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("tab", { name: "Upgrades" }).click();
  await expect(page.getByText("REVIEW_REQUIRED").first()).toBeVisible();
  await page.getByRole("tab", { name: "Reports" }).click();
  await expect(page.getByTestId("report-viewer")).toBeVisible();
});
