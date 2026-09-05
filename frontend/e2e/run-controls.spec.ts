import { test, expect } from "@playwright/test";

// E. Run controls E2E (mock): cancel / retry / approve / reject deterministically.
test("E. run controls: cancel, retry, approve, reject", async ({ page }) => {
  page.on("dialog", (d) => d.accept());
  // cancel + retry on a normal run
  await page.goto("/tasks/new");
  await page.getByLabel("Task").fill("control probe task");
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  await expect(page.getByTestId("plan-preview")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await expect(page.getByTestId("run-timeline")).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByText("CANCELLED").first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByText("RETRYING").first()).toBeVisible({ timeout: 15000 });

  // approve / reject on paid-model gated runs
  await page.goto("/tasks/new");
  await page.getByLabel("Task").fill("paid probe");
  await page.getByLabel("Model").fill("paid-gpt");
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  await expect(page.getByTestId("plan-preview")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await expect(page.getByTestId("approval-card")).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "Approve once" }).click();
  await expect(page.getByText("RUNNING_AGENT").first()).toBeVisible({ timeout: 15000 });

  await page.goto("/tasks/new");
  await page.getByLabel("Task").fill("paid probe 2");
  await page.getByLabel("Model").fill("paid-gpt");
  await page.getByRole("button", { name: "Plan", exact: true }).click();
  await expect(page.getByTestId("plan-preview")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await expect(page.getByTestId("approval-card")).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "Reject" }).click();
  await expect(page.getByText("CANCELLED").first()).toBeVisible({ timeout: 15000 });
});
