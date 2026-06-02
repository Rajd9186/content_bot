# Phase 8: Project Intelligence Layer - Implementation Plan

## 1. Audit Result: PHASE 8 FAILED (Current Status: 0%)
As of June 1, 2026, a comprehensive audit of the codebase confirms that Phase 8 (Project Intelligence Layer) has not yet been implemented. The system currently functions as a single-turn content pipeline without long-term project memory, cross-workflow context, or semantic retrieval capabilities.

---

## 2. Gap Analysis

### Missing Backend Components
- **Project Domain:** No REST APIs for `/api/projects`.
- **Database Schema:** Missing tables for `projects`, `project_memories`, and `project_conversations`.
- **Vector Search:** `pgvector` extension is not enabled; no embedding storage or similarity search logic exists.
- **Agentic Logic:** The LangGraph workflow in `graph.py` lacks a `MemoryRetrievalAgent`.
- **Background Jobs:** No scheduled tasks for memory deduplication or consolidation.

### Missing Frontend Components
- **Project Dashboard:** UI for managing multiple projects.
- **Memory Explorer:** View for inspecting, pinning, and deleting project knowledge.
- **Context Preview:** Pre-generation component showing what memories will be injected into the LLM prompt.
- **Project Timeline:** Chronological view of all prompts, research, and outputs within a project.

---

## 3. Implementation Roadmap (What to Build)

### Step 1: Database & Infrastructure (Foundation)
- Create an Alembic migration to:
    - Enable `pgvector` extension.
    - Create `projects` table.
    - Create `project_memories` table with a `vector(1536)` column (for OpenAI/Nvidia embeddings).
    - Create `project_outputs` and `pinned_project_memories` tables.

### Step 2: Project Management API
- Implement the `Project` domain:
    - `POST /api/projects`: Create a new project container.
    - `GET /api/projects`: List projects.
    - `GET /api/projects/{id}/dashboard`: Aggregate metrics (total tokens, outputs, memories).

### Step 3: Semantic Memory Engine
- Implement a `MemoryService`:
    - Integration with an embedding provider (Nvidia/OpenAI).
    - Logic to save memories automatically after each pipeline stage (Research, Writer, Fact-Check).
    - `POST /api/projects/{id}/memory/search`: Semantic search endpoint.

### Step 4: Agentic Integration (LangGraph)
- Create `MemoryRetrievalAgent`:
    - This agent will run **before** the Research Agent.
    - It will query the `project_memories` table based on the user's current topic.
    - It will inject found context into the `PipelineState`.
- Update `prompts.py` to handle the "Assembled Context" block.

### Step 5: Frontend Intelligence UI
- **Dashboard:** Project selection and summary stats.
- **Timeline:** Chronological activity feed.
- **Intelligence View:** The "Context Preview" that shows the user what the AI "remembers" before they hit generate.

---

## 4. Success Criteria
Phase 8 will be considered **COMPLETE** when:
1. A user can create a project "Solar Energy".
2. They generate an article; the findings are automatically stored.
3. They start a second article in the same project, and the system **automatically retrieves and cites** the facts from the first article without the user re-pasting them.
4. Project A cannot see Project B's memories (Isolation).
