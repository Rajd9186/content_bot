# AI Content Intelligence Platform — UI Guide

Current version of the frontend — deployed and verified working.

---

## Overview

The frontend is a **Next.js 14 App Router** application with **TypeScript**, **Tailwind CSS**, and **Zustand** for state management. It communicates with the FastAPI backend via REST API and Server-Sent Events (SSE) for real-time pipeline updates.

**Frontend URL**: `http://localhost:3000` (local dev) or via Docker
**API Base**: `/api/v1`

---

## Navigation

### Desktop/Tablet (≥768px)
A fixed **sidebar** (260px expanded, 72px collapsed) on the left with navigation items. Toggle with the hamburger icon in the top bar.

### Mobile (<768px)
A **hamburger drawer** slides in from the left when the menu button is tapped. Closes automatically when a section is selected.

### Sidebar Items (12 sections)
| Section | Description |
|---------|-------------|
| Command Center | AI OS landing page with all metrics |
| Content Pipeline | Create and monitor pipelines |
| Pipeline History | Past pipeline runs |
| Projects | Project management with workspace tabs |
| Analytics | Pipeline success rates, metrics |
| Workspace | Workspace settings |
| Agent Monitor | Real-time agent + provider metrics |
| Orchestration | Workflow orchestration |
| System Metrics | Prometheus-style system metrics |
| Skills Engine | Agent skill management |
| Operations | Provider operations dashboard |
| Settings | User preferences |

---

## Design System

### Theme: Violet (AI OS Dark)
- **Primary color**: Violet (`#7c3aed` / `hsl(262, 83%, 58%)`)
- **Dark mode** (default): Dark slate background
- **Light mode**: Clean white/gray background
- Toggle via the sun/moon icon in the top navigation bar
- Theme preference is **persisted** in `localStorage`

### Color Tokens (CSS Variables)
```
Primary:          hsl(262 83% 58%)    — Violet
Success/Emerald: hsl(160 84% 39%)   — Emerald
Warning/Amber:   hsl(38 92% 50%)     — Amber
Destructive/Red: hsl(0 63% 50%)      — Red
Info/Blue:        hsl(211 100% 61%)  — Blue
Background (dark): hsl(222 47% 11%)
Foreground (dark):  hsl(210 40% 98%)
Card (dark):        hsl(222 47% 14%)
```

### Typography
- **Sans**: Inter (with system-ui fallback)
- **Mono**: JetBrains Mono
- Scale: 11px captions → 14px body → 18px headings

### Animations
- `bounce-in`: Modal/openings — `cubic-bezier(0.34, 1.56, 0.64, 1)`
- `slide-in-left`: Mobile drawer
- `fade-in`: General fade
- `node-pulse`: Running pipeline nodes
- `btn-press`: Active button feedback (`scale-[0.97]`)

---

## Section: Command Center (NEW — Default Landing)

AI OS-style landing page with real-time metrics. Shows when app loads.

### Metrics Row (7 stat cards)
- Projects count
- Running pipelines
- Completed pipelines
- Memories count
- Skills count
- Outputs count
- Token usage (aggregate)

### Provider Health Panel
Live provider stats from `GET /providers/stats`:
- Status dot per provider (emerald/amber/red)
- Success rate, latency, RPM usage

### Activity Timeline
Streaming SSE events: research completed, memory retrieved, skill applied, etc.

### Latest Outputs
Recent completed pipelines with topic and token count.

### Quick Start
New Pipeline and Browse Projects buttons.

---

## Section: Content Pipeline

Has two view modes: **Pipeline View** (default) and **Content View**.

### Pipeline View
Three main panels:
1. **Pipeline Graph** — SVG-based DAG visualization (React Flow-style)
2. **Stream Timeline** — Real-time SSE streaming events
3. **Agent Activities** — Expandable per-node activity cards

Plus the **Output Workspace** (3-column content view) via the "Content View" toggle button.

### Pipeline Graph
SVG-rendered pipeline DAG with:
- All 11 stages: Prompt → Skill Retrieval → Memory Retrieval → Research → Planner → Writer → SEO → Fact Check → Compliance → Review → Final Output
- Color-coded edges (completed = emerald, running = blue, pending = dashed violet)
- Clickable nodes → open Agent Transparency Panel
- Live status dots and latency display

### Stream Timeline
Real-time updating vertical timeline driven by SSE events:
- Events stream in as pipeline runs: `node_started`, `node_completed`, `pipeline_failed`, etc.
- Shows timestamps, latency, tokens per event
- Auto-scrolls to latest
- Color-coded: emerald = completed, blue = running, red = failed, amber = cancelled

### Content View (3-column Output Workspace)
Toggle via "Content View" button:
- **Left**: Auto-generated outline from content headings
- **Center**: Full generated content (final vs draft indicator, word count)
- **Right**: Content Intelligence panel
  - Aggregate stats (tokens, latency, success rate)
  - Agents Used (provider/model per agent)
  - Skills Applied
  - Memories Retrieved
  - Fact Checks
  - Compliance
  - Provider Details

### Agent Transparency Panel
Slide-in drawer from right when clicking any pipeline node:
Shows full agent details:
- Status + provider/model
- Latency, tokens, estimated cost, retries
- Timestamps (started/completed)
- Prompt Sent, LLM Request, LLM Response (expandable)
- Generated Output (JSON view)
- Execution Timeline with all steps

---

## Section: Agent Monitor

Real-time agent metrics derived from `status.nodes` + live `GET /providers/stats`:
- Agent metrics cards: status dot, provider/model, tokens, latency, retries
- Expandable summary
- 10s auto-refresh from providers stats
- Color-coded success rate per provider

---

## Section: Projects

Enhanced workspace with tab navigation:

### Tabs: Overview | Memories | Skills | Sources | Pipelines | Outputs | Analytics | Settings

### Overview Tab
- Project header with counts (memories, outputs, sources, tokens)
- 6-stat grid (outputs, memories, sources, tokens, cost, last activity)
- Recent pipelines list
- New Pipeline button

### Pipelines Tab
- List of project pipelines
- Status indicator per pipeline

### Outputs Tab
- List of generated outputs with title, content type, date

### Settings Tab
- Edit project name, description
- Archive toggle
- Save changes

### All Projects View
- Searchable project list
- Inline "New project" creation
- Project cards with: initial avatar, name, description, memory/output counts, last activity

---

## Section: Skills Engine

Three tabs: **Skills**, **Assignment**, **Compliance**

### Skills Tab (default)
- CRUD for agent skills (markdown-based)
- Category filter (writing, research, seo, fact_check, compliance, etc.)
- Version history viewer
- Search by name/description
- Skill detail view with version badge, active/inactive status, agent targets
- Create/Edit modal with markdown editor

### Assignment Tab
- Assign skills to projects at priority levels

### Compliance Tab
- Usage analytics per skill, compliance score distribution

---

## Section: Operations

**ProviderDashboard** — real-time provider metrics:
- Per-provider cards: RPM/TPM usage bars, active requests, latency, success rate, circuit state badge
- Aggregate request distribution bar
- Auto-refresh every 10 seconds

---

## Other Sections

| Section | What it shows |
|---------|--------------|
| Pipeline History | Past pipeline runs with status |
| Analytics | Charts: bar, line, pie, metrics cards |
| Workspace | Workspace management |
| Settings | API base URL, refresh interval, default tone/audience |
| Orchestration | Workflow orchestration (placeholder) |
| System Metrics | Prometheus metrics (placeholder) |

---

## Component Library

### Layout
`SideNav` (collapsible desktop, drawer mobile), `TopNav` (hamburger + new pipeline + theme toggle)

### Pipeline
`PipelineGraph` (SVG DAG, live status, clickable nodes), `StreamTimeline` (SSE streaming), `OutputWorkspace` (3-column content view), `AgentTransparencyPanel` (slide-in agent details), `AgentActivityPanel` (expandable per-node activity cards), `PipelineForm`, `PipelineViewer`, `PipelineList`

### Providers
`ProviderDashboard` (live RPM/TPM/latency/success per provider)

### Command Center
`CommandCenter` (AI OS landing: stat cards, provider health, activity timeline, outputs, quick start)

### Common
`Badge`, `LoadingSpinner` (violet glow), `Modal` (bounce-in, rounded-2xl), `StatusIndicator`, `ThemeToggle`, `ErrorBoundary`

---

## State Management (Zustand)

| Store | Manages |
|-------|---------|
| `pipeline-store.ts` | Pipelines list, current pipeline, status, content, timeline, SSE events |
| `ui-store.ts` | Current section, sidebar open/closed, theme, mobile menu, modals, settings |
| `auth-store.ts` | Auth tokens, user profile |
| `project-store.ts` | Projects, current project |
| `skills-store.ts` | Skills, project skills, filtering |
| `notification-store.ts` | Notifications |

---

## Key Hooks

| Hook | Purpose |
|------|---------|
| `useAgentNodes()` | Merges `status.nodes` + SSE `events[]` for real-time agent data |
| `useProvidersStats()` | Polls `GET /providers/stats` every 10s |
| `useSSE()` | Manages SSE connection for pipeline events |
| `usePipeline()` | Pipeline operations wrapper |

---

## Real-Time Updates

Pipelines use **SSE** (`GET /pipeline/{id}/events`) to stream:
- `connected` — connection established
- `node_started` / `node_running` — a node began
- `node_completed` — a node finished (includes actions, tokens, latency, provider/model)
- `pipeline_completed` / `pipeline_failed` — done

Events flow into:
- `events[]` in pipeline store → drives `StreamTimeline` in real-time
- `status.nodes` via `refresh()` → drives `AgentActivityPanel`, `OutputWorkspace.MetadataPanel`
- `AgentTransparencyPanel` opens from `PipelineGraph` node click

---

## Running Locally

```bash
cd frontend
npm install
npm run dev   # → http://localhost:3000

# Backend must be running on :8000 for API to work
```

## Playwright E2E Tests

```bash
npm install -D @playwright/test
npx playwright install --with-deps
npm run test:e2e          # Run all suites
npm run test:e2e:ui      # Interactive UI mode
npm run test:e2e:headed   # See browser
```

Test files: `tests/e2e/dashboard.spec.ts`, `projects.spec.ts`, `pipeline.spec.ts`, `sections.spec.ts`, `responsive.spec.ts`, `theme.spec.ts`

Target: ≥ 80% UI coverage across all major sections.

---

## Backend Health Check

Pipeline execution uses **intelligent provider scheduling** (`provider_scheduler.py`):
- Scores providers by: circuit state, RPM remaining, TPM remaining, active requests, latency, success rate
- NVIDIA uses `meta/llama-3.1-70b-instruct` for fast tasks, `meta/llama-3.3-70b-instruct` for heavy tasks
- Groq is RPM-protected (preflight check before sending)
- Fallback chain: preferred → fallback → ollama → "no provider"

Working providers: **Groq** (391ms), **NVIDIA llama-3.1/3.3** (1.2–1.7s), **Ollama gpt-oss:120b** (2.3s)