# E2E Test Suite

Playwright-based end-to-end tests for the AI Content Intelligence Platform frontend.

## Setup

```bash
# 1. Install Playwright (requires bypass of execution policy)
npm install -D @playwright/test
npx playwright install --with-deps

# 2. Run tests
npm run test:e2e

# 3. Run with UI mode
npm run test:e2e:ui

# 4. Run headed (see browser)
npm run test:e2e:headed
```

## Test Suites

| File | What it tests |
|------|--------------|
| `dashboard.spec.ts` | Command Center: stat cards, provider health, quick start |
| `projects.spec.ts` | Projects workspace: tabs, search, creation |
| `pipeline.spec.ts` | Content Pipeline: graph, timeline, output workspace |
| `sections.spec.ts` | Agent Monitor, Operations, Skills Engine, Analytics |
| `responsive.spec.ts` | Mobile/Tablet/Desktop/Large viewport checks |
| `theme.spec.ts` | Dark/light mode toggle, persistence |

## Coverage Target

- ≥ 80% UI coverage across all major sections
- Navigation: all sidebar sections
- Data loading: pipelines, projects, providers
- SSE updates: pipeline execution flow
- Theme switching: persistence across reload
- Responsive: 4 viewport sizes × key sections

## Running Specific Tests

```bash
# Single suite
npx playwright test dashboard.spec.ts

# Single test
npx playwright test --grep "loads command center"

# Specific viewport
npx playwright test --project="Mobile Chrome"

# Debug mode
npm run test:e2e:debug
```

## Reports

```bash
npm run test:e2e:report
# Opens HTML report at playwright-report/index.html
```

## CI Mode

```bash
CI=true npm run test:e2e
# Runs in chromium only, with retries, no web server start
```