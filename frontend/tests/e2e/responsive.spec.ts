import { test, expect } from "@playwright/test";

test.describe("Responsive Design", () => {
  const viewports = [
    { name: "Mobile", width: 390, height: 844 },
    { name: "Tablet", width: 768, height: 1024 },
    { name: "Desktop", width: 1280, height: 800 },
    { name: "Large", width: 1920, height: 1080 },
  ];

  for (const vp of viewports) {
    test(`${vp.name} (${vp.width}x${vp.height}) - dashboard loads`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);
      await expect(page.getByRole("heading", { name: /command center/i })).toBeVisible({ timeout: 15000 });
    });

    test(`${vp.name} - sidebar behavior`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);

      if (vp.width < 768) {
        const hamburgerBtn = page.locator("button").filter({ hasText: /menu/i }).first();
        if (await hamburgerBtn.isVisible()) {
          await hamburgerBtn.click();
          await page.waitForTimeout(300);
        }
      }
    });

    test(`${vp.name} - Command Center stat cards`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);

      const stats = page.locator(".grid > div").filter({ hasText: /projects|running|completed/i });
      const count = await stats.count();
      expect(count).toBeGreaterThan(0);
    });

    test(`${vp.name} - no horizontal overflow`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);

      const body = page.locator("body");
      const overflow = await body.evaluate((el) => el.scrollWidth > el.clientWidth);
      expect(overflow).toBe(false);
    });

    test(`${vp.name} - projects section loads`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);
      if (vp.width < 768) {
        const hamburger = page.locator("button[aria-label='Toggle menu']").first();
        if (await hamburger.isVisible()) {
          await hamburger.click();
          await page.waitForTimeout(500);
        }
      }
      await page.locator("nav").getByText(/projects/i).click();
      await page.waitForTimeout(1000);
      const content = page.getByRole("heading", { name: /projects/i }).or(page.getByText("Browse Projects"));
      await expect(content.first()).toBeVisible({ timeout: 10000 });
    });

    test(`${vp.name} - pipeline section loads`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1500);
      if (vp.width < 768) {
        const hamburger = page.locator("button[aria-label='Toggle menu']").first();
        if (await hamburger.isVisible()) {
          await hamburger.click();
          await page.waitForTimeout(500);
        }
      }
      await page.locator("nav").getByText(/content pipeline/i).click();
      await page.waitForTimeout(1000);
      const content = page.getByText("Pipeline Graph").or(page.getByText("Topic"));
      await expect(content.first()).toBeVisible({ timeout: 10000 });
    });
  }
});