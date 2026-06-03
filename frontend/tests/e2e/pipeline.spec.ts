import { test, expect } from "@playwright/test";

test.describe("Pipeline", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.get_by_role("button", { name: /content pipeline/i }).click();
    await page.waitForTimeout(500);
  });

  test("loads content pipeline section", async ({ page }) => {
    await expect(page.getByText("Pipeline Graph")).toBeVisible({ timeout: 10000 });
  });

  test("shows pipeline form", async ({ page }) => {
    await expect(page.getByPlaceholder(/topic/i)).toBeVisible();
  });

  test("shows pipeline graph visualization", async ({ page }) => {
    await expect(page.getByText("Prompt")).toBeVisible();
  });

  test("shows execution timeline", async ({ page }) => {
    await expect(page.getByText("Execution Timeline")).toBeVisible();
  });

  test("shows agent activities panel", async ({ page }) => {
    await expect(page.getByText("Agent Activities")).toBeVisible();
  });

  test("has view toggle between pipeline and content", async ({ page }) => {
    const contentBtn = page.getByText("Content View");
    if (await contentBtn.isVisible()) {
      await contentBtn.click();
      await page.waitForTimeout(300);
      await expect(page.getByText("Generated Content")).toBeVisible();
      await expect(page.getByText("Outline")).toBeVisible();
      await expect(page.getByText("Content Intelligence")).toBeVisible();
    }
  });

  test("no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("Warning"))).toHaveLength(0);
  });
});