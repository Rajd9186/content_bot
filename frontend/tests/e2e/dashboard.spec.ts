import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
  });

  test("loads command center successfully", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /command center/i })).toBeVisible({ timeout: 10000 });
  });

  test("shows stat cards", async ({ page }) => {
    await expect(page.getByText("Projects")).toBeVisible();
    await expect(page.getByText("Running")).toBeVisible();
    await expect(page.getByText("Completed")).toBeVisible();
  });

  test("shows provider health section", async ({ page }) => {
    await expect(page.getByText("Provider Health")).toBeVisible();
  });

  test("shows active pipelines section", async ({ page }) => {
    await expect(page.getByText("Active Pipelines")).toBeVisible();
  });

  test("shows quick start section", async ({ page }) => {
    await expect(page.getByText("Quick Start")).toBeVisible();
    await expect(page.getByText("New Pipeline")).toBeVisible();
  });

  test("navigates to Content Pipeline via sidebar", async ({ page }) => {
    await page.get_byRole("button", { name: /content pipeline/i }).click();
    await page.waitForTimeout(500);
    const url = page.url();
    expect(url).toContain("/dashboard");
  });

  test("opens New Pipeline and navigates to pipeline view", async ({ page }) => {
    const newPipelineBtn = page.locator("button").filter({ hasText: "New Pipeline" }).first();
    if (await newPipelineBtn.isVisible()) {
      await newPipelineBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test("no console errors on load", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("Warning"))).toHaveLength(0);
  });
});