import { test, expect } from "@playwright/test";

test.describe("Agent Monitor", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    await page.locator("nav").getByText(/agent monitor/i).click();
    await page.waitForTimeout(1000);
  });

  test("loads agent monitor section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /agent monitor/i }).first()).toBeVisible({ timeout: 15000 });
  });

  test("shows agent metrics or empty state", async ({ page }) => {
    const metrics = page.getByText("Running").or(page.getByText("Completed")).or(page.getByText("No data"));
    await expect(metrics.first()).toBeVisible({ timeout: 10000 });
  });

  test("shows agent to provider mapping or empty state", async ({ page }) => {
    const mapping = page.getByText("Agent").or(page.getByText("No agents"));
    await expect(mapping.first()).toBeVisible({ timeout: 5000 });
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

test.describe("Operations", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    await page.locator("nav").getByText(/operations/i).click();
    await page.waitForTimeout(1000);
  });

  test("loads operations section", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /operations/i }).first()).toBeVisible({ timeout: 15000 });
  });

  test("shows operations content or empty state", async ({ page }) => {
    const content = page.getByText("Provider").or(page.getByText("No providers")).or(page.getByText("Operations"));
    await expect(content.first()).toBeVisible({ timeout: 10000 });
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

test.describe("Skills Engine", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    await page.locator("nav").getByText(/skills engine/i).click();
    await page.waitForTimeout(1000);
  });

  test("loads skills engine section", async ({ page }) => {
    const heading = page.getByRole("heading", { name: /skills/i }).or(page.getByText("Skills Studio"));
    await expect(heading.first()).toBeVisible({ timeout: 15000 });
  });

  test("shows skills content", async ({ page }) => {
    const content = page.getByText("Skills").or(page.getByText("Assignment")).or(page.getByText("Studio"));
    await expect(content.first()).toBeVisible({ timeout: 10000 });
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

test.describe("Analytics", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1500);
    await page.locator("nav").getByText(/analytics/i).click();
    await page.waitForTimeout(1000);
  });

  test("loads analytics section", async ({ page }) => {
    const heading = page.getByRole("heading", { name: /analytics/i }).or(page.getByText("Analytics"));
    await expect(heading.first()).toBeVisible({ timeout: 15000 });
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