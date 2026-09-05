import { test, expect } from "@playwright/test";

// B. AppSec UI E2E (mock): login → Security → new engagement → audit →
// finding → retest → report.
test("B. appsec: engagement to retested finding", async ({ page }) => {
  await page.goto("/security");
  await expect(page.getByRole("heading", { name: "Security" })).toBeVisible();
  await page.getByRole("tab", { name: "Engagements" }).click();
  await page.getByLabel("Engagement ID").fill("eng-e2e");
  await page.getByLabel("Target URL").fill("http://fixture.local/");
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByTestId("eng-eng-e2e")).toBeVisible({ timeout: 15000 });
  await page.getByRole("tab", { name: "Browser" }).click();
  await page.getByRole("button", { name: "Launch headless" }).click();
  await page.getByRole("tab", { name: "Findings" }).click();
  await expect(page.getByText(/Role boundary/i).first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Retest" }).first().click();
  await page.getByRole("tab", { name: "Simulations" }).click();
  await expect(page.getByText("ROLE_BOUNDARY_CHECK").first()).toBeVisible();
  await page.getByRole("tab", { name: "Reports" }).click();
  await expect(page.getByTestId("report-viewer")).toBeVisible();
});
