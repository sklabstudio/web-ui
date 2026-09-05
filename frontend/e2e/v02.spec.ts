import { test, expect } from "@playwright/test";

// Deterministic mock E2E: no paid AI, no real targets, no real chains.

test("E2E1 security: engagement → traffic → finding → simulation", async ({ page }) => {
  await page.goto("/security");
  await expect(page.getByRole("heading", { name: "Security" })).toBeVisible();
  await page.getByRole("tab", { name: "Findings" }).click();
  await expect(page.getByText(/Role boundary/i).first()).toBeVisible();
  await page.getByRole("tab", { name: "Live Traffic" }).click();
  await expect(page.getByText("/api/profile").first()).toBeVisible();
  await page.getByRole("tab", { name: "Simulations" }).click();
  await expect(page.getByText("ROLE_BOUNDARY_CHECK").first()).toBeVisible();
});

test("E2E2 contracts: project → test → fuzz → invariant → upgrade", async ({ page }) => {
  await page.goto("/contracts");
  await expect(page.getByRole("heading", { name: "Contracts" })).toBeVisible();
  await page.getByRole("tab", { name: "Projects" }).click();
  await expect(page.getByTestId("project-proj-demo")).toBeVisible();
  await page.getByRole("tab", { name: "Upgrades" }).click();
  await expect(page.getByText("REVIEW_REQUIRED").first()).toBeVisible();
});

test("E2E3 protocols: authority → economic → assurance stale → alert → incident", async ({ page }) => {
  await page.goto("/protocols");
  await expect(page.getByRole("heading", { name: "Protocols" })).toBeVisible();
  await page.getByRole("tab", { name: "Authorities" }).click();
  await expect(page.getByText("Owner").first()).toBeVisible();
  await page.getByRole("tab", { name: "Assurance" }).click();
  await expect(page.getByText("Compilation").first()).toBeVisible();
  await page.getByRole("tab", { name: "Monitoring" }).click();
  await expect(page.getByText("ORACLE_CHANGED").first()).toBeVisible();
  await page.getByRole("tab", { name: "Incidents" }).click();
  await expect(page.getByText(/oracle delay/i).first()).toBeVisible();
});

test("dashboard shows Security/Contracts/Protocols summaries", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dash-security")).toBeVisible();
  await expect(page.getByTestId("dash-contracts")).toBeVisible();
  await expect(page.getByTestId("dash-protocols")).toBeVisible();
});
