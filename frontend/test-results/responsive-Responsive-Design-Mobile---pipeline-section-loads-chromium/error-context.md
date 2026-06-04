# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: responsive.spec.ts >> Responsive Design >> Mobile - pipeline section loads
- Location: tests\e2e\responsive.spec.ts:68:9

# Error details

```
Test timeout of 60000ms exceeded.
```

```
Error: locator.click: Test timeout of 60000ms exceeded.
Call log:
  - waiting for locator('nav').getByText(/content pipeline/i)
    - locator resolved to <span class="whitespace-nowrap font-medium">Content Pipeline</span>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
      - waiting 100ms
    110 × waiting for element to be visible, enabled and stable
        - element is not visible
      - retrying click action
        - waiting 500ms

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - banner [ref=e4]:
      - button "Toggle menu" [ref=e5] [cursor=pointer]:
        - img [ref=e6]
      - button "+ New" [ref=e8] [cursor=pointer]
      - button "Toggle theme" [ref=e10] [cursor=pointer]:
        - img [ref=e11]
    - main [ref=e13]:
      - generic [ref=e15]:
        - generic [ref=e16]:
          - generic [ref=e17]:
            - heading "Command Center" [level=1] [ref=e18]
            - paragraph [ref=e19]: AI Content Intelligence Platform overview
          - button "New Pipeline" [ref=e20] [cursor=pointer]:
            - img [ref=e21]
            - text: New Pipeline
        - generic [ref=e22]:
          - generic [ref=e25] [cursor=pointer]:
            - img [ref=e28]
            - generic [ref=e30]: "0"
            - generic [ref=e31]: Projects
          - generic [ref=e34] [cursor=pointer]:
            - img [ref=e37]
            - generic [ref=e39]: "0"
            - generic [ref=e40]: Running
          - generic [ref=e43] [cursor=pointer]:
            - img [ref=e46]
            - generic [ref=e50]: "0"
            - generic [ref=e51]: Completed
          - generic [ref=e54] [cursor=pointer]:
            - img [ref=e57]
            - generic [ref=e67]: —
            - generic [ref=e68]: Memories
          - generic [ref=e71] [cursor=pointer]:
            - img [ref=e74]
            - generic [ref=e76]: —
            - generic [ref=e77]: Skills
          - generic [ref=e80] [cursor=pointer]:
            - img [ref=e83]
            - generic [ref=e85]: "0"
            - generic [ref=e86]: Outputs
          - generic [ref=e89] [cursor=pointer]:
            - img [ref=e92]
            - generic [ref=e95]: —
            - generic [ref=e96]: Token Usage
        - generic [ref=e97]:
          - generic [ref=e98]:
            - generic [ref=e99]:
              - heading "Recent Activity" [level=3] [ref=e101]:
                - img [ref=e102]
                - text: Recent Activity
              - generic [ref=e104]:
                - img [ref=e105]
                - paragraph [ref=e107]: No recent activity
            - generic [ref=e108]:
              - heading "Latest Outputs" [level=3] [ref=e110]:
                - img [ref=e111]
                - text: Latest Outputs
              - generic [ref=e117]:
                - img [ref=e118]
                - paragraph [ref=e124]: No outputs yet
                - button "Create your first pipeline →" [ref=e125] [cursor=pointer]
          - generic [ref=e126]:
            - generic [ref=e127]:
              - heading "Provider Health" [level=3] [ref=e129]
              - paragraph [ref=e131]: No providers configured
              - button "View all operations →" [ref=e132] [cursor=pointer]
            - generic [ref=e133]:
              - generic [ref=e134]:
                - heading "Active Pipelines" [level=3] [ref=e135]:
                  - img [ref=e136]
                  - text: Active Pipelines
                - generic [ref=e138]: 0 running
              - generic [ref=e139]:
                - img [ref=e140]
                - paragraph [ref=e142]: No active pipelines
            - generic [ref=e143]:
              - generic [ref=e144]:
                - img [ref=e145]
                - heading "Quick Start" [level=3] [ref=e147]
              - generic [ref=e148]:
                - button "New Pipeline Generate AI content" [ref=e149] [cursor=pointer]:
                  - img [ref=e151]
                  - generic [ref=e152]:
                    - generic [ref=e153]: New Pipeline
                    - generic [ref=e154]: Generate AI content
                  - img [ref=e155]
                - button "Browse Projects Manage workspaces" [ref=e157] [cursor=pointer]:
                  - img [ref=e159]
                  - generic [ref=e161]:
                    - generic [ref=e162]: Browse Projects
                    - generic [ref=e163]: Manage workspaces
                  - img [ref=e164]
  - alert [ref=e166]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("Responsive Design", () => {
  4  |   const viewports = [
  5  |     { name: "Mobile", width: 390, height: 844 },
  6  |     { name: "Tablet", width: 768, height: 1024 },
  7  |     { name: "Desktop", width: 1280, height: 800 },
  8  |     { name: "Large", width: 1920, height: 1080 },
  9  |   ];
  10 | 
  11 |   for (const vp of viewports) {
  12 |     test(`${vp.name} (${vp.width}x${vp.height}) - dashboard loads`, async ({ page }) => {
  13 |       await page.setViewportSize({ width: vp.width, height: vp.height });
  14 |       await page.goto("/dashboard");
  15 |       await page.waitForLoadState("domcontentloaded");
  16 |       await page.waitForTimeout(1500);
  17 |       await expect(page.getByRole("heading", { name: /command center/i })).toBeVisible({ timeout: 15000 });
  18 |     });
  19 | 
  20 |     test(`${vp.name} - sidebar behavior`, async ({ page }) => {
  21 |       await page.setViewportSize({ width: vp.width, height: vp.height });
  22 |       await page.goto("/dashboard");
  23 |       await page.waitForLoadState("domcontentloaded");
  24 |       await page.waitForTimeout(1500);
  25 | 
  26 |       if (vp.width < 768) {
  27 |         const hamburgerBtn = page.locator("button").filter({ hasText: /menu/i }).first();
  28 |         if (await hamburgerBtn.isVisible()) {
  29 |           await hamburgerBtn.click();
  30 |           await page.waitForTimeout(300);
  31 |         }
  32 |       }
  33 |     });
  34 | 
  35 |     test(`${vp.name} - Command Center stat cards`, async ({ page }) => {
  36 |       await page.setViewportSize({ width: vp.width, height: vp.height });
  37 |       await page.goto("/dashboard");
  38 |       await page.waitForLoadState("domcontentloaded");
  39 |       await page.waitForTimeout(1500);
  40 | 
  41 |       const stats = page.locator(".grid > div").filter({ hasText: /projects|running|completed/i });
  42 |       const count = await stats.count();
  43 |       expect(count).toBeGreaterThan(0);
  44 |     });
  45 | 
  46 |     test(`${vp.name} - no horizontal overflow`, async ({ page }) => {
  47 |       await page.setViewportSize({ width: vp.width, height: vp.height });
  48 |       await page.goto("/dashboard");
  49 |       await page.waitForLoadState("domcontentloaded");
  50 |       await page.waitForTimeout(1500);
  51 | 
  52 |       const body = page.locator("body");
  53 |       const overflow = await body.evaluate((el) => el.scrollWidth > el.clientWidth);
  54 |       expect(overflow).toBe(false);
  55 |     });
  56 | 
  57 |     test(`${vp.name} - projects section loads`, async ({ page }) => {
  58 |       await page.setViewportSize({ width: vp.width, height: vp.height });
  59 |       await page.goto("/dashboard");
  60 |       await page.waitForLoadState("domcontentloaded");
  61 |       await page.waitForTimeout(1500);
  62 |       await page.locator("nav").getByText(/projects/i).click();
  63 |       await page.waitForTimeout(1000);
  64 |       const content = page.getByRole("heading", { name: /projects/i }).or(page.getByText("Browse Projects"));
  65 |       await expect(content.first()).toBeVisible({ timeout: 10000 });
  66 |     });
  67 | 
  68 |     test(`${vp.name} - pipeline section loads`, async ({ page }) => {
  69 |       await page.setViewportSize({ width: vp.width, height: vp.height });
  70 |       await page.goto("/dashboard");
  71 |       await page.waitForLoadState("domcontentloaded");
  72 |       await page.waitForTimeout(1500);
> 73 |       await page.locator("nav").getByText(/content pipeline/i).click();
     |                                                                ^ Error: locator.click: Test timeout of 60000ms exceeded.
  74 |       await page.waitForTimeout(1000);
  75 |       const content = page.getByText("Pipeline Graph").or(page.getByText("Topic"));
  76 |       await expect(content.first()).toBeVisible({ timeout: 10000 });
  77 |     });
  78 |   }
  79 | });
```