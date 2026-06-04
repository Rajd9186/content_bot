import { test, expect } from "@playwright/test";

test.describe("Projects", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    await page.locator("nav").getByText(/projects/i).click();
    await page.waitForTimeout(1000);
  });

  test("loads projects section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /^projects$/i })).toBeVisible({ timeout: 15000 });
  });

  test("shows project workspace with tabs or empty state", async ({ page }) => {
    const overviewOrEmpty = page.getByText("Overview").or(page.getByText("No projects yet"));
    await expect(overviewOrEmpty.first()).toBeVisible({ timeout: 10000 });
  });

  test("has search input for projects", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search projects/i);
    await expect(searchInput).toBeVisible();
  });

  test("has new project creation input", async ({ page }) => {
    const newProjectInput = page.getByPlaceholder(/new project/i);
    await expect(newProjectInput).toBeVisible();
  });

  test("switches between tabs when present", async ({ page }) => {
    const memoriesTab = page.getByRole("button", { name: /memories/i }).first();
    if (await memoriesTab.isVisible()) {
      await memoriesTab.click();
      await page.waitForTimeout(500);
    }
    const pipelinesTab = page.getByRole("button", { name: /pipelines/i }).first();
    if (await pipelinesTab.isVisible()) {
      await pipelinesTab.click();
      await page.waitForTimeout(500);
    }
  });

  test("can type in project search", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search projects/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill("test");
      await expect(searchInput).toHaveValue("test");
    }
  });

  test("no critical console errors", async ({ page }) => {
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