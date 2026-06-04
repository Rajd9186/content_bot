# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: pipeline.spec.ts >> Pipeline >> has view toggle between pipeline and content
- Location: tests\e2e\pipeline.spec.ts:37:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]: A
        - generic [ref=e6]:
          - generic [ref=e7]: ACIP
          - generic [ref=e8]: Content Intelligence
      - navigation "Main navigation" [ref=e9]:
        - button "◈ Command Center" [ref=e10] [cursor=pointer]:
          - generic [ref=e11]: ◈
          - generic [ref=e12]: Command Center
        - button "⊞ Content Pipeline" [active] [ref=e13] [cursor=pointer]:
          - generic [ref=e14]: ⊞
          - generic [ref=e15]: Content Pipeline
        - button "≡ Pipeline History" [ref=e16] [cursor=pointer]:
          - generic [ref=e17]: ≡
          - generic [ref=e18]: Pipeline History
        - button "📁 Projects" [ref=e19] [cursor=pointer]:
          - generic [ref=e20]: 📁
          - generic [ref=e21]: Projects
        - button "⬡ Analytics" [ref=e22] [cursor=pointer]:
          - generic [ref=e23]: ⬡
          - generic [ref=e24]: Analytics
        - button "◰ Workspace" [ref=e25] [cursor=pointer]:
          - generic [ref=e26]: ◰
          - generic [ref=e27]: Workspace
        - button "⚙ Settings" [ref=e28] [cursor=pointer]:
          - generic [ref=e29]: ⚙
          - generic [ref=e30]: Settings
        - button "◈ Agent Monitor" [ref=e31] [cursor=pointer]:
          - generic [ref=e32]: ◈
          - generic [ref=e33]: Agent Monitor
        - button "⇄ Orchestration" [ref=e34] [cursor=pointer]:
          - generic [ref=e35]: ⇄
          - generic [ref=e36]: Orchestration
        - button "◆ System Metrics" [ref=e37] [cursor=pointer]:
          - generic [ref=e38]: ◆
          - generic [ref=e39]: System Metrics
        - button "◇ Skills Engine" [ref=e40] [cursor=pointer]:
          - generic [ref=e41]: ◇
          - generic [ref=e42]: Skills Engine
        - button "◉ Operations" [ref=e43] [cursor=pointer]:
          - generic [ref=e44]: ◉
          - generic [ref=e45]: Operations
      - generic [ref=e49]:
        - generic [ref=e50]: System Online
        - generic [ref=e51]: All services operational
    - generic [ref=e52]:
      - banner [ref=e53]:
        - button "Toggle sidebar" [ref=e54] [cursor=pointer]:
          - img [ref=e55]
        - button "+ New Pipeline" [ref=e57] [cursor=pointer]
        - generic [ref=e59]:
          - generic [ref=e60]: /
          - generic [ref=e61]: Content Pipeline
        - button "Toggle theme" [ref=e63] [cursor=pointer]:
          - img [ref=e64]
      - main [ref=e66]:
        - generic [ref=e68]:
          - generic [ref=e69]:
            - generic [ref=e70]:
              - heading "Create Pipeline" [level=3] [ref=e71]: Create Pipeline
              - generic [ref=e73]:
                - generic [ref=e74]:
                  - generic [ref=e75]: Topic
                  - textbox "Enter content topic..." [ref=e76]
                - generic [ref=e77]:
                  - generic [ref=e78]:
                    - generic [ref=e79]: Audience
                    - combobox [ref=e80] [cursor=pointer]:
                      - option "Developers"
                      - option "Managers"
                      - option "Marketing"
                      - option "Technical Writers"
                      - option "Executives"
                      - option "Researchers"
                      - option "General Audience" [selected]
                  - generic [ref=e81]:
                    - generic [ref=e82]: Tone
                    - combobox [ref=e83] [cursor=pointer]:
                      - option "Professional" [selected]
                      - option "Casual"
                      - option "Academic"
                      - option "Journalistic"
                      - option "Persuasive"
                      - option "Technical"
                  - generic [ref=e84]:
                    - generic [ref=e85]: Provider
                    - combobox [ref=e86] [cursor=pointer]:
                      - option "OpenAI" [selected]
                      - option "Groq"
                      - option "NVIDIA"
                      - option "Anthropic"
                      - option "Ollama"
                - button "Start Pipeline" [disabled] [ref=e87]
            - heading "Recent Pipelines" [level=3] [ref=e90]
          - paragraph [ref=e93]: Select a pipeline to view details
          - generic [ref=e95]:
            - heading "Quick Info" [level=3] [ref=e96]
            - paragraph [ref=e97]: Select or create a pipeline to generate AI content. Each pipeline runs through 8 stages of automated content creation with real-time streaming.
      - contentinfo [ref=e99]:
        - generic [ref=e100]: © 2026 ACIP — AI Content Intelligence Platform
        - generic [ref=e101]:
          - generic [ref=e102]: All systems operational
          - generic [ref=e104]: "|"
          - generic [ref=e105]: v1.0.0
  - alert [ref=e106]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("Pipeline", () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto("/dashboard");
  6  |     await page.waitForLoadState("domcontentloaded");
  7  |     await page.waitForTimeout(1500);
  8  |     await page.locator("nav").getByText(/content pipeline/i).click();
  9  |     await page.waitForTimeout(1000);
  10 |   });
  11 | 
  12 |   test("loads content pipeline section", async ({ page }) => {
  13 |     const pipelineEl = page.getByText("Pipeline Graph").or(page.getByText("Topic"));
  14 |     await expect(pipelineEl.first()).toBeVisible({ timeout: 15000 });
  15 |   });
  16 | 
  17 |   test("shows pipeline form or pipeline graph", async ({ page }) => {
  18 |     const formOrGraph = page.getByPlaceholder(/topic/i).or(page.getByText("Pipeline Graph"));
  19 |     await expect(formOrGraph.first()).toBeVisible({ timeout: 10000 });
  20 |   });
  21 | 
  22 |   test("shows pipeline graph nodes when data present", async ({ page }) => {
  23 |     const promptNode = page.getByText("Prompt").or(page.getByText("No pipelines"));
  24 |     await expect(promptNode.first()).toBeVisible({ timeout: 5000 });
  25 |   });
  26 | 
  27 |   test("shows execution timeline when pipeline is active", async ({ page }) => {
  28 |     const timeline = page.getByText("Execution Timeline").or(page.getByText("Start Pipeline"));
  29 |     await expect(timeline.first()).toBeVisible({ timeout: 5000 });
  30 |   });
  31 | 
  32 |   test("shows agent activities when pipeline is active", async ({ page }) => {
  33 |     const activities = page.getByText("Agent Activities").or(page.locator("[class*='agent']").first());
  34 |     await expect(activities.first()).toBeVisible({ timeout: 5000 });
  35 |   });
  36 | 
  37 |   test("has view toggle between pipeline and content", async ({ page }) => {
  38 |     const contentBtn = page.getByText("Content View").first();
  39 |     const pipelineBtn = page.getByText("Pipeline View").first();
  40 |     const hasToggle = await contentBtn.isVisible() || await pipelineBtn.isVisible();
> 41 |     expect(hasToggle).toBe(true);
     |                       ^ Error: expect(received).toBe(expected) // Object.is equality
  42 |   });
  43 | 
  44 |   test("no console errors", async ({ page }) => {
  45 |     const errors: string[] = [];
  46 |     page.on("console", (msg) => {
  47 |       if (msg.type() === "error") errors.push(msg.text());
  48 |     });
  49 |     await page.reload();
  50 |     await page.waitForLoadState("domcontentloaded");
  51 |     await page.waitForTimeout(1500);
  52 |     const filtered = errors.filter((e) =>
  53 |       !e.includes("Warning") &&
  54 |       !e.includes("CORS") &&
  55 |       !e.includes("Access-Control") &&
  56 |       !e.includes("ERR_FAILED") &&
  57 |       !e.includes("404")
  58 |     );
  59 |     expect(filtered).toHaveLength(0);
  60 |   });
  61 | });
```