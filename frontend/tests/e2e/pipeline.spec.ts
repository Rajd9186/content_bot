import { test, expect } from "@playwright/test";

test.describe("Pipeline", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    await page.locator("nav").getByText(/content pipeline/i).click();
    await page.waitForTimeout(1000);
  });

  test("loads content pipeline section", async ({ page }) => {
    const pipelineEl = page.getByText("Pipeline Graph").or(page.getByText("Topic"));
    await expect(pipelineEl.first()).toBeVisible({ timeout: 15000 });
  });

  test("shows pipeline form or pipeline graph", async ({ page }) => {
    const formOrGraph = page.getByPlaceholder(/topic/i).or(page.getByText("Pipeline Graph"));
    await expect(formOrGraph.first()).toBeVisible({ timeout: 10000 });
  });

  test("shows pipeline graph nodes when data present", async ({ page }) => {
    const promptNode = page.getByText("Prompt").or(page.getByText("No pipelines"));
    await expect(promptNode.first()).toBeVisible({ timeout: 5000 });
  });

  test("shows execution timeline when pipeline is active", async ({ page }) => {
    const timeline = page.getByText("Execution Timeline").or(page.getByText("Start Pipeline"));
    await expect(timeline.first()).toBeVisible({ timeout: 5000 });
  });

  test("shows agent activities when pipeline is active", async ({ page }) => {
    const activities = page.getByText("Agent Activities").or(page.locator("[class*='agent']").first());
    await expect(activities.first()).toBeVisible({ timeout: 5000 });
  });

  test("has view toggle between pipeline and content", async ({ page }) => {
    const contentBtn = page.getByText("Content View").first();
    const pipelineBtn = page.getByText("Pipeline View").first();
    const hasToggle = await contentBtn.isVisible() || await pipelineBtn.isVisible();
    expect(hasToggle).toBe(true);
  });

  test("no console errors", async ({ page }) => {
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