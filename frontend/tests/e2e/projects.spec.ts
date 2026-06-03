import { test, expect } from "@playwright/test";

test.describe("Projects", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.get_by_role("button", { name: /projects/i }).click();
    await page.waitForTimeout(500);
  });

  test("loads projects section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /projects/i })).toBeVisible({ timeout: 10000 });
  });

  test("shows project workspace with tabs", async ({ page }) => {
    await expect(page.getByText("Overview")).toBeVisible();
    await expect(page.getByText("Memories")).toBeVisible();
    await expect(page.getByText("Pipelines")).toBeVisible();
  });

  test("has search input for projects", async ({ page }) => {
    await expect(page.getByPlaceholder(/search projects/i)).toBeVisible();
  });

  test("has new project creation input", async ({ page }) => {
    await expect(page.getByPlaceholder(/new project/i)).toBeVisible();
  });

  test("switches between tabs", async ({ page }) => {
    await page.getByRole("button", { name: /memories/i }).click();
    await page.waitForTimeout(300);
    await page.getByRole("button", { name: /pipelines/i }).click();
    await page.waitForTimeout(300);
    await page.getByRole("button", { name: /overview/i }).click();
    await page.waitForTimeout(300);
  });

  test("can type in project search", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search projects/i);
    await searchInput.fill("test");
    await expect(searchInput).toHaveValue("test");
  });

  test("no critical console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("Warning") && !e.includes("404"))).toHaveLength(0);
  });
});