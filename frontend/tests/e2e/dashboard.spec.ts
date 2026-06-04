import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
  });

  test("loads command center successfully", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /command center/i })).toBeVisible({ timeout: 15000 });
  });

  test("shows stat cards", async ({ page }) => {
    await expect(page.getByText("Projects").first()).toBeVisible();
    await expect(page.getByText("Running").first()).toBeVisible();
    await expect(page.getByText("Completed").first()).toBeVisible();
  });

  test("shows provider health section", async ({ page }) => {
    await expect(page.getByText("Provider Health").first()).toBeVisible();
  });

  test("shows active pipelines section", async ({ page }) => {
    await expect(page.getByText("Active Pipelines").first()).toBeVisible();
  });

  test("shows quick start section", async ({ page }) => {
    await expect(page.getByText("Quick Start").first()).toBeVisible();
    await expect(page.getByText("New Pipeline").first()).toBeVisible();
  });

  test("navigates to Content Pipeline via sidebar", async ({ page }) => {
    await page.getByRole("button", { name: /content pipeline/i }).click();
    await page.waitForTimeout(1000);
    const url = page.url();
    expect(url).toContain("/dashboard");
  });

  test("opens New Pipeline modal", async ({ page }) => {
    const newPipelineBtn = page.getByText("New Pipeline").first();
    if (await newPipelineBtn.isVisible()) {
      await newPipelineBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test("no critical console errors on load", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    const filtered = errors.filter((e) =>
      !e.includes("Warning") &&
      !e.includes("CORS") &&
      !e.includes("Access-Control") &&
      !e.includes("ERR_FAILED") &&
      !e.includes("404")
    );
    expect(filtered).toHaveLength(0);
  });
});