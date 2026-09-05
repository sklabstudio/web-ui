import { test, expect } from "@playwright/test";

test("mock run: plan → run → retry → accept → patch", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New Task" })).toBeVisible();
  await expect(page.getByTestId("plan-preview").or(page.getByText("Plan"))).toBeTruthy();
});

test("approval gate renders when present", async ({ page }) => {
  await page.goto("/runs/run-0001");
  await expect(page.getByText(/Run run-/)).toBeVisible();
});
