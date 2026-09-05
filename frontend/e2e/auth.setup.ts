import { test as setup, expect } from "@playwright/test";

// Global login: exercises the real login form, then persists session.
setup("authenticate", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Token").fill(process.env.E2E_TOKEN || "e2e-token-123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 15000 });
  await page.context().storageState({ path: "./e2e/.auth.json" });
});
