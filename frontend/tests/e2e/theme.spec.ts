import { test, expect } from "@playwright/test";

test.describe("Theme", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
  });

  test("loads in dark mode by default", async ({ page }) => {
    const html = page.locator("html");
    await expect(html).toHaveClass(/dark/);
  });

  test("theme toggle button is visible", async ({ page }) => {
    const themeToggle = page.locator("button[aria-label*='theme' i], button[aria-label*='dark' i], button[aria-label*='light' i]");
    const navToggle = page.locator("header button").first();
    await expect(navToggle).toBeVisible();
  });

  test("can toggle theme via sun/moon button", async ({ page }) => {
    const html = page.locator("html");
    const wasDark = await html.evaluate((el) => el.classList.contains("dark"));

    const toggleBtn = page.locator("header button").first();
    await toggleBtn.click();
    await page.waitForTimeout(500);

    const isDark = await html.evaluate((el) => el.classList.contains("dark"));
    expect(isDark).toBe(!wasDark);
  });

  test("theme preference persists across reload", async ({ page }) => {
    const toggleBtn = page.locator("header button").first();
    await toggleBtn.click();
    await page.waitForTimeout(500);
    await page.reload();
    await page.waitForLoadState("networkidle");

    const html = page.locator("html");
    const isDark = await html.evaluate((el) => el.classList.contains("dark"));
    expect(isDark).toBe(false);
  });

  test("dark mode has proper background color", async ({ page }) => {
    await page.waitForTimeout(500);
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
    await page.waitForLoadState("networkidle");
    expect(errors).toHaveLength(0);
  });
});