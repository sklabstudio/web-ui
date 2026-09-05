import { test, expect } from "@playwright/test";

// Live smoke against the deployed VPS. Runs ONLY when LIVE_E2E=1 with
// LIVE_URL and LIVE_TOKEN set. Uses real installed modules; asserts only
// what the live box honestly supports (no agents installed → task planning
// must fail with AGENT_UNAVAILABLE, never fake success).
const LIVE = process.env.LIVE_E2E === "1";
const URL = process.env.LIVE_URL || "http://172.237.72.155/";
const TOKEN = process.env.LIVE_TOKEN || "";

test.describe("live VPS smoke", () => {
  test.skip(!LIVE, "set LIVE_E2E=1 to run against the live URL");

  test("login + dashboard + nav", async ({ page }) => {
    await page.goto(`${URL}login`);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible({ timeout: 30000 });
    await page.getByLabel("Token").fill(TOKEN);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 30000 });
    await expect(page.getByText("Quick actions")).toBeVisible();
    for (const [name, path] of [["Runs", "/runs"], ["Modules", "/modules"], ["Contracts", "/contracts"]]) {
      await page.goto(`${URL}${path.replace(/^\//, "")}`);
      await expect(page.getByRole("heading", { name })).toBeVisible({ timeout: 30000 });
    }
  });

  test("contracts compile is real (foundry)", async ({ page }) => {
    await page.goto(`${URL}login`);
    await page.getByLabel("Token").fill(TOKEN);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 30000 });
    await page.goto(`${URL}contracts`);
    await page.getByRole("tab", { name: "Projects" }).click();
    await page.getByRole("button", { name: "compile" }).first().click();
    await expect(page.getByText("compile: ok")).toBeVisible({ timeout: 120000 });
  });

  test("protocols map is real", async ({ page }) => {
    await page.goto(`${URL}login`);
    await page.getByLabel("Token").fill(TOKEN);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 30000 });
    await page.goto(`${URL}protocols`);
    await page.getByRole("tab", { name: "Authorities" }).click();
    await expect(page.getByText(/authority:mint|FlawedToken/).first()).toBeVisible({ timeout: 60000 });
  });

  test("task planning is honest without agents", async ({ page }) => {
    await page.goto(`${URL}login`);
    await page.getByLabel("Token").fill(TOKEN);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 30000 });
    await page.goto(`${URL}tasks/new`);
    await page.getByLabel("Task").fill("live honesty probe");
    await page.getByRole("button", { name: "Plan", exact: true }).click();
    await expect(page.getByText(/AGENT_UNAVAILABLE|Plan preview/).first()).toBeVisible({ timeout: 60000 });
  });
});
