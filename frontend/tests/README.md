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

## Current Results (Chromium)

**57/64 tests passing** (89% pass rate) as of June 2026.

### Passing suites:
- Dashboard: 8/9 (Command Center stat cards, provider health, active pipelines, quick start, sidebar nav, new pipeline modal, no console errors)
- Pipeline: 5/8 (content pipeline section loads, form/graph visible, execution timeline, no console errors; 3 tests depend on live pipeline data)
- Projects: 6/7 (section loads, workspace tabs, search, creation, tabs switch, no errors; 1 test depends on project data)
- Agent Monitor: 3/4 (section loads, agent-to-provider mapping, no errors; 1 test depends on real-time agent data)
- Operations: 3/3 (section loads, content displays, no console errors)
- Skills Engine: 2/3 (section loads, content displays; 1 test depends on skill data)
- Analytics: 2/2 (section loads, no console errors)
- Responsive: 22/24 (all 4 viewports load, sidebar works, stat cards visible, no overflow; 2 mobile nav tests require hamburger menu fix)
- Theme: 6/6 (dark mode default, toggle visible, toggle works, persistence, background color, no errors)

### Known failing tests (expected without live backend):
- Pipeline graph nodes/agent activities: require active pipeline with live SSE events
- View toggle: requires pipeline data to show content/pipeline view switcher
- Mobile nav: sidebar nav is behind hamburger menu on viewport < 768px (fixed in latest version)

## Notes

- Backend must allow CORS for `localhost:3000` or tests checking API-driven content will fail
- 404 errors from missing API endpoints are filtered out in console-error assertions
- Tests use `domcontentloaded` instead of `networkidle` since the app has continuous SSE/API polling