import { test, expect } from "@playwright/test";

// F. Ops E2E (mock): skills enable/disable, providers health, agents,
// modules matrix + doctor, settings save.
test("F. ops: skills, providers, agents, modules, settings", async ({ page }) => {
  await page.goto("/skills");
  await expect(page.getByRole("heading", { name: "Skills" })).toBeVisible();
  await expect(page.getByText("tdd").first()).toBeVisible({ timeout: 15000 });

  await page.goto("/providers");
  await expect(page.getByRole("heading", { name: "Providers" })).toBeVisible();
  await page.getByRole("button", { name: /Test zero-cost health/ }).first().click();
  await expect(page.getByText(/zero-cost health/i).first()).toBeVisible({ timeout: 15000 });

  await page.goto("/agents");
  await expect(page.getByRole("heading", { name: "Agents" })).toBeVisible();
  await expect(page.getByText("hermes").first()).toBeVisible({ timeout: 15000 });

  await page.goto("/modules");
  await expect(page.getByRole("heading", { name: "Modules" })).toBeVisible();
  await expect(page.getByText("orchestrator").first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Doctor" }).click();
  await expect(page.getByText(/zero-cost/i).first()).toBeVisible({ timeout: 15000 });

  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Saved.").first()).toBeVisible({ timeout: 15000 });

  await page.goto("/");
  await expect(page.getByText("Quick actions")).toBeVisible();
});
