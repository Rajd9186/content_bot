import { test, expect } from "@playwright/test";

test.describe("Theme", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
  });

  test("loads in dark mode by default", async ({ page }) => {
    const html = page.locator("html");
    await expect(html).toHaveClass(/dark/);
  });

  test("theme toggle button is visible", async ({ page }) => {
    const themeToggle = page.locator("button[aria-label='Toggle theme']").first();
    await expect(themeToggle).toBeVisible();
  });

  test("can toggle theme via theme button", async ({ page }) => {
    const html = page.locator("html");
    const wasDark = await html.evaluate((el) => el.classList.contains("dark"));

    const toggleBtn = page.locator("button[aria-label='Toggle theme']").first();
    await toggleBtn.click();
    await page.waitForTimeout(500);

    const isDark = await html.evaluate((el) => el.classList.contains("dark"));
    expect(isDark).toBe(!wasDark);
  });

  test("theme preference persists across reload", async ({ page }) => {
    const toggleBtn = page.locator("button[aria-label='Toggle theme']").first();
    await toggleBtn.click();
    await page.waitForTimeout(500);
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);

    const html = page.locator("html");
    const isDark = await html.evaluate((el) => el.classList.contains("dark"));
    expect(isDark).toBe(false);
  });

  test("dark mode has proper background color", async ({ page }) => {
    const bg = await page.locator("body").evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.backgroundColor;
    });
    expect(bg).not.toBe("rgba(0, 0, 0, 0)");
  });

  test("no theme-related console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error" && msg.text().toLowerCase().includes("theme")) {
        errors.push(msg.text());
      }
    });
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    expect(errors).toHaveLength(0);
  });
});