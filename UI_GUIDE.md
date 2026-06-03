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

### Sidebar Items (11 sections)
| Section | Description |
|---------|-------------|
| Content Pipeline | Default view — create and monitor pipelines |
| Pipeline History | Past pipeline runs |
| Projects | Project management with memory context |
| Analytics | Pipeline success rates, metrics |
| Workspace | Workspace settings |
| Settings | User preferences |
| Agent Monitor | Real-time agent + provider metrics |
| Orchestration | Workflow orchestration |
| System Metrics | Prometheus-style system metrics |
| Skills Engine | Agent skill management |
| Operations | Provider operations dashboard |

---

## Design System

### Theme: Violet
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

### Breakpoints
| Breakpoint | Width | Use |
|-----------|-------|------|
| Mobile | <768px | Single column, hamburger nav, touch-optimized |
| Tablet | 768–1024px | Collapsible sidebar |
| Desktop | ≥1024px | Full sidebar, multi-column layouts |
| Large | ≥1400px | Max container width 1400px |

### Animations
- `bounce-in`: Modal/openings — `cubic-bezier(0.34, 1.56, 0.64, 1)`
- `slide-in-left`: Mobile drawer
- `fade-in`: General fade
- `pulse-soft`: Status indicators
- `btn-press`: Active button feedback (`scale-[0.97]`)

---

## Section: Content Pipeline

The default landing page after login. Has three zones:

### 1. Left Panel (PipelineForm + PipelineList)
- **Create Pipeline form**: Topic input, audience, tone, provider selectors. Violet gradient submit button.
- **Pipeline List**: Small scrollable list of recent pipelines (hidden below lg breakpoint)

### 2. Center — Pipeline DAG
A **NodeStatusCard** showing all 8 pipeline stages as a 2×4 grid (4×2 on sm, 2×2 on mobile):
```
Skill Retrieval | Memory Retrieval
Research | Planner
Writer | SEO
Fact Checker | Compliance | Review | Finalizer
```
Each node card shows a status dot (emerald=completed, blue=running, red=failed, gray=pending) and latency.

### 3. Below DAG — Timeline
Vertical list of completed nodes with status dot and status text.

### Agent Activities Panel
**Below Timeline** — shows detailed agent activity for each pipeline node:

Each node card is **expandable** (click ▶) and shows:
- Agent start — provider/model used, timestamp
- LLM request — when the model was called
- LLM response — received from provider
- Parse output — output parsed successfully
- Retry — if agent retried
- Error — if agent failed

Actions appear **in real-time as the pipeline runs** (from SSE `node_completed` events, not just after completion).

**Empty state**: "Waiting for agents to start..." shown before any data arrives.

### Right Panel (≥xl only)
Static quick-info card.

---

## Section: Agent Monitor

Shows real pipeline agent metrics and live provider stats:

### Agent Metrics Grid
Cards per pipeline stage derived from `usePipelineStore().status.nodes` + SSE events:
- Status dot (emerald/blue/red)
- Provider + model used
- Token count, latency, retry count
- Expandable summary with full node stats

### Provider Stats Grid
Live data from `GET /providers/stats` (auto-refreshes every 10s):
- Calls, RPM, TPM, latency, success rate per provider
- Color-coded success rate (emerald ≥95%, amber ≥80%, red <80%)

### Circuit Breaker + Token Budget Cards
- Circuit breaker: worst state across all providers
- Token budget: aggregate TPM across all providers

### Empty State
"No agent data yet. Run a pipeline to see real-time agent metrics."

---

## Section: Skills Engine

Three tabs: **Skills**, **Assignment**, **Compliance**

### Skills Tab (default)
- CRUD for agent skills (markdown-based)
- Version history per skill
- Test skill with A/B comparison
- Filter by category (writing, research, seo, fact_check, compliance, etc.)

### Assignment Tab
- Assign skills to projects at priority levels (project → workflow → global)
- Enable/disable per project
- Conflict detection

### Compliance Tab
- Usage analytics per skill
- Compliance score distribution

---

## Section: Operations

**ProviderDashboard** component — real-time provider metrics:
- Per-provider cards: RPM/TPM usage bars, active requests, latency, success rate, circuit state badge
- Aggregate request distribution bar
- Target ranges: Groq 25-35%, NVIDIA 25-35%, Ollama 30-50%
- Auto-refresh every 10 seconds

---

## Other Sections

| Section | What it shows |
|---------|--------------|
| Pipeline History | Past pipeline runs with status |
| Projects | Project CRUD, memory context, timeline |
| Analytics | Charts: bar, line, pie, metrics cards |
| Workspace | Workspace management |
| Settings | API base URL, refresh interval, default tone/audience |
| Orchestration | Workflow orchestration (placeholder) |
| System Metrics | Prometheus metrics (placeholder) |

---

## Component Library

### Common
`Badge` (variants: violet/emerald/blue/amber/red/slate), `LoadingSpinner` (violet glow), `Modal` (bounce-in, rounded-2xl), `StatusIndicator`, `ThemeToggle`, `ErrorBoundary`

### Layout
`SideNav` (collapsible on desktop, drawer on mobile), `TopNav` (hamburger + new pipeline + theme toggle), `Footer`, `Breadcrumb`

### Pipeline
`AgentActivityPanel` (real-time agent steps), `NodeStatusCard` (8-node grid), `PipelineForm`, `PipelineViewer`, `PipelineTimeline`, `PipelineList`, `HumanReviewModal`

### Providers
`ProviderDashboard` (live RPM/TPM/latency/success per provider)

---

## Real-Time Updates

Pipelines use **SSE** (`GET /pipeline/{id}/events`) to stream:
- `connected` — connection established
- `node_completed` — a pipeline node finished (includes actions, tokens, latency)
- `pipeline_completed` / `pipeline_failed` — pipeline done

SSE events flow into:
- `events[]` array in pipeline store → drives AgentActivityPanel in real-time
- `handleEvent` calls `refresh()` → populates `status.nodes` → drives AgentMonitor and NodeStatusCard

---

## State Management (Zustand)

| Store | Manages |
|-------|---------|
| `pipeline-store.ts` | Pipelines list, current pipeline, status, content, timeline, SSE events |
| `ui-store.ts` | Current section, sidebar open/closed, theme, mobile menu, modals |
| `auth-store.ts` | Auth tokens, user profile |
| `project-store.ts` | Projects |
| `skills-store.ts` | Skills |
| `notification-store.ts` | Notifications |

---

## API Integration

- All API calls go through `lib/api.ts` → `/api/v1`
- Key endpoints:
  - `POST /content-pipeline/pipeline/start` — create pipeline
  - `POST /content-pipeline/pipeline/{id}/run` — run pipeline
  - `GET /content-pipeline/pipeline/{id}` — pipeline status + nodes (includes actions)
  - `GET /content-pipeline/pipeline/{id}/timeline` — timeline + actions
  - `GET /content-pipeline/pipeline/{id}/events` — SSE stream
  - `GET /providers/stats` — provider capacity/latency/success rate
  - `GET/POST/PUT/DELETE /skills` — skills CRUD
  - `GET /projects` — projects list

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base (default: `http://localhost:8000`) |

---

## Backend Health Check

Pipeline execution uses **intelligent provider scheduling** (`provider_scheduler.py`):
- Scores providers by: circuit state, RPM remaining, TPM remaining, active requests, latency, success rate
- NVIDIA uses `meta/llama-3.1-70b-instruct` for fast tasks, `meta/llama-3.3-70b-instruct` for heavy tasks
- Groq is RPM-protected (preflight check before sending)
- Fallback chain: preferred → fallback → ollama → "no provider"

Working providers: **Groq** (391ms), **NVIDIA llama-3.1/3.3** (1.2–1.7s), **Ollama gpt-oss:120b** (2.3s)

---

## Running Locally

```bash
cd frontend
npm install
npm run dev   # → http://localhost:3000

# Backend must be running on :8000 for API to work
```