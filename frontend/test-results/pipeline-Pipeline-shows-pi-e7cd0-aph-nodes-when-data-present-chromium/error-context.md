# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: pipeline.spec.ts >> Pipeline >> shows pipeline graph nodes when data present
- Location: tests\e2e\pipeline.spec.ts:22:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Prompt').or(getByText('No pipelines')).first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('Prompt').or(getByText('No pipelines')).first()

```

```yaml
- complementary:
  - text: A ACIP Content Intelligence
  - navigation "Main navigation":
    - button "◈ Command Center"
    - button "⊞ Content Pipeline"
    - button "≡ Pipeline History"
    - button "📁 Projects"
    - button "⬡ Analytics"
    - button "◰ Workspace"
    - button "⚙ Settings"
    - button "◈ Agent Monitor"
    - button "⇄ Orchestration"
    - button "◆ System Metrics"
    - button "◇ Skills Engine"
    - button "◉ Operations"
  - text: System Online All services operational
- banner:
  - button "Toggle sidebar":
    - img
  - button "+ New Pipeline"
  - text: / Content Pipeline
  - button "Toggle theme":
    - img
- main:
  - heading "Create Pipeline" [level=3]
  - text: Topic
  - textbox "Enter content topic..."
  - text: Audience
  - combobox:
    - option "Developers"
    - option "Managers"
    - option "Marketing"
    - option "Technical Writers"
    - option "Executives"
    - option "Researchers"
    - option "General Audience" [selected]
  - text: Tone
  - combobox:
    - option "Professional" [selected]
    - option "Casual"
    - option "Academic"
    - option "Journalistic"
    - option "Persuasive"
    - option "Technical"
  - text: Provider
  - combobox:
    - option "OpenAI" [selected]
    - option "Groq"
    - option "NVIDIA"
    - option "Anthropic"
    - option "Ollama"
  - button "Start Pipeline" [disabled]
  - heading "Recent Pipelines" [level=3]
  - paragraph: Select a pipeline to view details
  - heading "Quick Info" [level=3]
  - paragraph: Select or create a pipeline to generate AI content. Each pipeline runs through 8 stages of automated content creation with real-time streaming.
- contentinfo: © 2026 ACIP — AI Content Intelligence Platform All systems operational | v1.0.0
- alert
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
> 24 |     await expect(promptNode.first()).toBeVisible({ timeout: 5000 });
     |                                      ^ Error: expect(locator).toBeVisible() failed
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
  41 |     expect(hasToggle).toBe(true);
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