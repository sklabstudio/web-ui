import { test, expect } from "@playwright/test";

// D. Protocol UI E2E (mock): login → Protocols → map → specs →
// simulation → assurance.
test("D. protocols: map to assurance", async ({ page }) => {
  await page.goto("/protocols");
  await expect(page.getByRole("heading", { name: "Protocols" })).toBeVisible();
  await page.getByRole("tab", { name: "Authorities" }).click();
  await expect(page.getByText("Owner").first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("tab", { name: "Economic Twin" }).click();
  await page.getByRole("button", { name: "Run simulation" }).click();
  await expect(page.getByText(/simulate.*done|insolvency/i).first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("tab", { name: "Assurance" }).click();
  await expect(page.getByText("Compilation").first()).toBeVisible();
  await page.getByRole("button", { name: "Refresh assurance" }).click();
  await page.getByRole("tab", { name: "Monitoring" }).click();
  await expect(page.getByText("ORACLE_CHANGED").first()).toBeVisible();
  await page.getByRole("tab", { name: "Incidents" }).click();
  await expect(page.getByText(/oracle delay/i).first()).toBeVisible();
});
