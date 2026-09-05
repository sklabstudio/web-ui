import { test, expect, devices } from "@playwright/test";

// G. Responsive (mock): phone viewport keeps nav, forms, run controls,
// finding details and tables usable.
test.use({ ...devices["Pixel 7"] });

test("G. responsive: phone layout stays operable", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("Quick actions")).toBeVisible();

  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New Task" })).toBeVisible();
  await page.getByLabel("Task").fill("phone probe");
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  await expect(page.getByTestId("plan-preview")).toBeVisible({ timeout: 15000 });

  await page.goto("/runs");
  await expect(page.getByRole("heading", { name: "Runs" })).toBeVisible();

  await page.goto("/security");
  await page.getByRole("tab", { name: "Findings" }).click();
  await expect(page.getByText(/Role boundary/i).first()).toBeVisible({ timeout: 15000 });

  await page.goto("/contracts");
  await page.getByRole("tab", { name: "Tools" }).click();
  await expect(page.getByText("foundry").first()).toBeVisible({ timeout: 15000 });
});
