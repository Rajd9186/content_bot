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
      await page.waitForLoadState("networkidle");
      await expect(page.getByRole("heading", { name: /command center/i })).toBeVisible({ timeout: 10000 });
    });

    test(`${vp.name} - sidebar behavior`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("networkidle");

      if (vp.width < 768) {
        const hamburgerBtn = page.locator("button").filter({ hasText: /☰|menu/i }).first();
        if (await hamburgerBtn.isVisible()) {
          await hamburgerBtn.click();
          await page.waitForTimeout(300);
        }
      }
    });

    test(`${vp.name} - Command Center stat cards`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("networkidle");

      const stats = page.locator(".grid > div").filter({ hasText: /projects|running|completed/i });
      const count = await stats.count();
      expect(count).toBeGreaterThan(0);
    });

    test(`${vp.name} - no horizontal overflow`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("networkidle");

      const body = page.locator("body");
      const overflow = await body.evaluate((el) => el.scrollWidth > el.clientWidth);
      expect(overflow).toBe(false);
    });

    test(`${vp.name} - projects section`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("networkidle");
      await page.get_by_role("button", { name: /projects/i }).click();
      await page.waitForTimeout(500);
      await expect(page.getByRole("heading", { name: /projects/i })).toBeVisible();
    });

    test(`${vp.name} - pipeline section`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/dashboard");
      await page.waitForLoadState("networkidle");
      await page.get_by_role("button", { name: /content pipeline/i }).click();
      await page.waitForTimeout(500);
      await expect(page.getByText("Pipeline Graph")).toBeVisible();
    });
  }
});