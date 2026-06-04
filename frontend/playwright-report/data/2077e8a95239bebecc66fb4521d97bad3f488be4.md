# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: sections.spec.ts >> Skills Engine >> loads skills engine section
- Location: tests\e2e\sections.spec.ts:91:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: /skills/i }).or(getByText('Skills Studio')).first()
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 15000ms
  - waiting for getByRole('heading', { name: /skills/i }).or(getByText('Skills Studio')).first()

```

```yaml
- dialog "Unhandled Runtime Error":
  - navigation:
    - button "previous" [disabled]:
      - img "previous"
    - button "next" [disabled]:
      - img "next"
    - text: 1 of 1 error Next.js (14.2.35) is outdated
    - link "(learn more)":
      - /url: https://nextjs.org/docs/messages/version-staleness
  - button "Close"
  - heading "Unhandled Runtime Error" [level=1]
  - paragraph: "ReferenceError: useEffect is not defined"
  - heading "Source" [level=2]
  - link "src\\components\\skills\\SkillsStudio.tsx (352:3) @ useEffect":
    - text: src\components\skills\SkillsStudio.tsx (352:3) @ useEffect
    - img
  - text: "350 | }, [filterCategory]); 351 | > 352 | useEffect(() => { | ^ 353 | loadSkills(); 354 | }, [loadSkills]); 355 |"
  - heading "Call Stack" [level=2]
  - button "Show collapsed frames"
```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | 
  3   | test.describe("Agent Monitor", () => {
  4   |   test.beforeEach(async ({ page }) => {
  5   |     await page.goto("/dashboard");
  6   |     await page.waitForLoadState("domcontentloaded");
  7   |     await page.waitForTimeout(1500);
  8   |     await page.locator("nav").getByText(/agent monitor/i).click();
  9   |     await page.waitForTimeout(1000);
  10  |   });
  11  | 
  12  |   test("loads agent monitor section", async ({ page }) => {
  13  |     await expect(page.getByRole("heading", { name: /agent monitor/i }).first()).toBeVisible({ timeout: 15000 });
  14  |   });
  15  | 
  16  |   test("shows agent metrics or empty state", async ({ page }) => {
  17  |     const metrics = page.getByText("Running").or(page.getByText("Completed")).or(page.getByText("No data"));
  18  |     await expect(metrics.first()).toBeVisible({ timeout: 10000 });
  19  |   });
  20  | 
  21  |   test("shows agent to provider mapping or empty state", async ({ page }) => {
  22  |     const mapping = page.getByText("Agent").or(page.getByText("No agents"));
  23  |     await expect(mapping.first()).toBeVisible({ timeout: 5000 });
  24  |   });
  25  | 
  26  |   test("no console errors", async ({ page }) => {
  27  |     const errors: string[] = [];
  28  |     page.on("console", (msg) => {
  29  |       if (msg.type() === "error") errors.push(msg.text());
  30  |     });
  31  |     await page.reload();
  32  |     await page.waitForLoadState("domcontentloaded");
  33  |     await page.waitForTimeout(1500);
  34  |     const filtered = errors.filter((e) =>
  35  |       !e.includes("Warning") &&
  36  |       !e.includes("CORS") &&
  37  |       !e.includes("Access-Control") &&
  38  |       !e.includes("ERR_FAILED") &&
  39  |       !e.includes("404")
  40  |     );
  41  |     expect(filtered).toHaveLength(0);
  42  |   });
  43  | });
  44  | 
  45  | test.describe("Operations", () => {
  46  |   test.beforeEach(async ({ page }) => {
  47  |     await page.goto("/dashboard");
  48  |     await page.waitForLoadState("domcontentloaded");
  49  |     await page.waitForTimeout(1500);
  50  |     await page.locator("nav").getByText(/operations/i).click();
  51  |     await page.waitForTimeout(1000);
  52  |   });
  53  | 
  54  |   test("loads operations section", async ({ page }) => {
  55  |     await expect(page.getByRole("heading", { name: /operations/i }).first()).toBeVisible({ timeout: 15000 });
  56  |   });
  57  | 
  58  |   test("shows operations content or empty state", async ({ page }) => {
  59  |     const content = page.getByText("Provider").or(page.getByText("No providers")).or(page.getByText("Operations"));
  60  |     await expect(content.first()).toBeVisible({ timeout: 10000 });
  61  |   });
  62  | 
  63  |   test("no console errors", async ({ page }) => {
  64  |     const errors: string[] = [];
  65  |     page.on("console", (msg) => {
  66  |       if (msg.type() === "error") errors.push(msg.text());
  67  |     });
  68  |     await page.reload();
  69  |     await page.waitForLoadState("domcontentloaded");
  70  |     await page.waitForTimeout(1500);
  71  |     const filtered = errors.filter((e) =>
  72  |       !e.includes("Warning") &&
  73  |       !e.includes("CORS") &&
  74  |       !e.includes("Access-Control") &&
  75  |       !e.includes("ERR_FAILED") &&
  76  |       !e.includes("404")
  77  |     );
  78  |     expect(filtered).toHaveLength(0);
  79  |   });
  80  | });
  81  | 
  82  | test.describe("Skills Engine", () => {
  83  |   test.beforeEach(async ({ page }) => {
  84  |     await page.goto("/dashboard");
  85  |     await page.waitForLoadState("domcontentloaded");
  86  |     await page.waitForTimeout(1500);
  87  |     await page.locator("nav").getByText(/skills engine/i).click();
  88  |     await page.waitForTimeout(1000);
  89  |   });
  90  | 
  91  |   test("loads skills engine section", async ({ page }) => {
  92  |     const heading = page.getByRole("heading", { name: /skills/i }).or(page.getByText("Skills Studio"));
> 93  |     await expect(heading.first()).toBeVisible({ timeout: 15000 });
      |                                   ^ Error: expect(locator).toBeVisible() failed
  94  |   });
  95  | 
  96  |   test("shows skills content", async ({ page }) => {
  97  |     const content = page.getByText("Skills").or(page.getByText("Assignment")).or(page.getByText("Studio"));
  98  |     await expect(content.first()).toBeVisible({ timeout: 10000 });
  99  |   });
  100 | 
  101 |   test("no console errors", async ({ page }) => {
  102 |     const errors: string[] = [];
  103 |     page.on("console", (msg) => {
  104 |       if (msg.type() === "error") errors.push(msg.text());
  105 |     });
  106 |     await page.reload();
  107 |     await page.waitForLoadState("domcontentloaded");
  108 |     await page.waitForTimeout(1500);
  109 |     const filtered = errors.filter((e) =>
  110 |       !e.includes("Warning") &&
  111 |       !e.includes("CORS") &&
  112 |       !e.includes("Access-Control") &&
  113 |       !e.includes("ERR_FAILED") &&
  114 |       !e.includes("404")
  115 |     );
  116 |     expect(filtered).toHaveLength(0);
  117 |   });
  118 | });
  119 | 
  120 | test.describe("Analytics", () => {
  121 |   test.beforeEach(async ({ page }) => {
  122 |     await page.goto("/dashboard");
  123 |     await page.waitForLoadState("domcontentloaded");
  124 |     await page.waitForTimeout(1500);
  125 |     await page.locator("nav").getByText(/analytics/i).click();
  126 |     await page.waitForTimeout(1000);
  127 |   });
  128 | 
  129 |   test("loads analytics section", async ({ page }) => {
  130 |     const heading = page.getByRole("heading", { name: /analytics/i }).or(page.getByText("Analytics"));
  131 |     await expect(heading.first()).toBeVisible({ timeout: 15000 });
  132 |   });
  133 | 
  134 |   test("no console errors", async ({ page }) => {
  135 |     const errors: string[] = [];
  136 |     page.on("console", (msg) => {
  137 |       if (msg.type() === "error") errors.push(msg.text());
  138 |     });
  139 |     await page.reload();
  140 |     await page.waitForLoadState("domcontentloaded");
  141 |     await page.waitForTimeout(1500);
  142 |     const filtered = errors.filter((e) =>
  143 |       !e.includes("Warning") &&
  144 |       !e.includes("CORS") &&
  145 |       !e.includes("Access-Control") &&
  146 |       !e.includes("ERR_FAILED") &&
  147 |       !e.includes("404")
  148 |     );
  149 |     expect(filtered).toHaveLength(0);
  150 |   });
  151 | });
```