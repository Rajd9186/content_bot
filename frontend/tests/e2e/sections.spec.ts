import { test, expect } from "@playwright/test";

test.describe("Agent Monitor", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.get_by_role("button", { name: /agent monitor/i }).click();
    await page.waitForTimeout(500);
  });

  test("loads agent monitor section", async ({ page }) => {
    await expect(page.getByText("Agent Monitor")).toBeVisible({ timeout: 10000 });
  });

  test("shows agent metrics cards", async ({ page }) => {
    await page.waitForTimeout(1000);
    const agentSection = page.getByText(/agent/i).first();
    await expect(agentSection).toBeVisible();
  });

  test("shows provider stats", async ({ page }) => {
    await expect(page.getByText("Provider Stats")).toBeVisible();
  });

  test("no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("Warning") && !e.includes("404"))).toHaveLength(0);
  });
});

test.describe("Operations", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.get_by_role("button", { name: /operations/i }).click();
    await page.waitForTimeout(1000);
  });

  test("loads operations section", async ({ page }) => {
    await expect(page.getByText("Operations")).toBeVisible({ timeout: 10000 });
  });

  test("shows provider cards", async ({ page }) => {
    await expect(page.getByText(/groq|ollama|nvidia/i).first()).toBeVisible({ timeout: 15000 });
  });

  test("no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("Warning") && !e.includes("404"))).toHaveLength(0);
  });
});

test.describe("Skills Engine", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.get_by_role("button", { name: /skills engine/i }).click();
    await page.waitForTimeout(500);
  });

  test("loads skills engine section", async ({ page }) => {
    await expect(page.getByText("Skills Engine")).toBeVisible({ timeout: 10000 });
  });

  test("shows skills tabs", async ({ page }) => {
    await expect(page.getByText("Skills")).toBeVisible();
    await expect(page.getByText("Assignment")).toBeVisible();
    await expect(page.getByText("Compliance")).toBeVisible();
  });

  test("no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("Warning") && !e.includes("404"))).toHaveLength(0);
  });
});

test.describe("Analytics", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.get_by_role("button", { name: /analytics/i }).click();
    await page.waitForTimeout(500);
  });

  test("loads analytics section", async ({ page }) => {
    await expect(page.getByText("Analytics")).toBeVisible({ timeout: 10000 });
  });

  test("no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.reload();
    await page.waitForLoadState("networkidle");
    expect(errors.filter((e) => !e.includes("Warning") && !e.includes("404"))).toHaveLength(0);
  });
});