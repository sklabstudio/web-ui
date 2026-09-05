import { test, expect } from "@playwright/test";

// A. Coding UI E2E (mock): login → New Task → fixture task → skills → Start →
// live timeline → patch → verification → VERIFIED_SUCCESS.
test("A. coding: new task to verified success", async ({ page }) => {
  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New Task" })).toBeVisible();
  await page.getByLabel("Task").fill("Fix flaky auth timeout test");
  await page.getByRole("button", { name: "Resolve skills" }).click();
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  await expect(page.getByTestId("plan-preview")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Run", exact: true }).click();
  // lands on the live run page
  await expect(page.getByTestId("run-timeline")).toBeVisible({ timeout: 30000 });
  await expect(page.getByText("VERIFIED_SUCCESS")).toBeVisible({ timeout: 60000 });
  await expect(page.getByTestId("attempt-timeline")).toBeVisible();
  await expect(page.getByTestId("log-view")).toBeVisible();
});
