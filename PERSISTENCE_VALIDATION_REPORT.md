# Persistence & Event Architecture Validation Report (Phase 2)
**Status:** REJECTED (Unsafe Transaction Boundaries)
**Date:** 2026-05-28
**Auditor:** Senior Distributed Systems Reliability Engineer (goose)

---

## 1. Executive Summary
The Phase 2 persistence and event architecture provides a solid schema and a functional event bus. However, it contains **critical reliability flaws** regarding the atomicity of event persistence and state transitions. The system currently lacks a formal **Outbox Pattern**, leading to potential "Dual Write" failures where a database update succeeds but the event is either lost or duplicated.

## 2. Persistence Health Score: 52/100

| Category | Score | Status |
|---|---|---|
| **Schema & Integrity** | 85% | PASS: Strong FKs, Indexes, and JSONB constraints. |
| **Transaction Safety** | 30% | FAIL: Dual-write risk in EventBus; lack of atomicity. |
| **Event Consistency** | 45% | DEGRADED: No ordering guarantees across restarts. |
| **Scaling & Concurrency** | 50% | DEGRADED: Optimistic locking present but no distributed locking. |

---

## 3. Persistence Audit (Database)

### 3.1 Schema Integrity
*   **Foreign Keys:** `WorkflowStep` and `ExecutionLog` correctly reference `WorkflowJob` with `ondelete="CASCADE"`.
*   **Indexes:** High-quality indexing strategy found in `StoredEvent` (Aggregate ID/Type) and `WorkflowJob` (Status/Created).
*   **Concurrency:** `WorkflowJob` uses a `version` column for optimistic locking in `update_status`.

### 3.2 Reliability Risks
*   **The "Dual Write" Problem:** In `EventBus.publish_and_store`, the event is saved to the DB and then published. If the publisher fails (e.g., Redis down), the database transaction may have already been flushed but the system state is now inconsistent with the message queue.
*   **No Transactional Outbox:** There is no background worker to retry event publication from the `stored_events` table.

---

## 4. Event System Audit

### 4.1 Event Replay & Ordering
*   **Replay:** `EventStore.replay` allows for aggregate reconstruction, which is excellent for event sourcing potential.
*   **Ordering:** The system relies on `created_at` for ordering. In a high-concurrency environment, sub-millisecond collisions could lead to non-deterministic replay order. A monotonic `sequence_number` is missing.

### 4.2 WebSocket & Redis Pub/Sub
*   **In-Memory Weakness:** `ConnectionManager` stores connections in a local `dict`. 
*   **Scalability Risk:** This implementation is incompatible with horizontal scaling (multi-node). If a user connects to Instance A, they will never receive events published by Instance B unless Redis Pub/Sub is used to bridge the managers (currently it only publishes, it doesn't listen).

---

## 5. Workflow Storage Audit
*   **Checkpointing:** `WorkflowStep` provides good granularity for task-level resumability.
*   **Dead Lettering:** `DeadLetterJob` table is well-defined, but there is no automated "re-drive" logic implemented to recover these jobs.

---

## 6. Critical Issues (Blockers for Phase 2)

### 6.1 Unsafe Event Publication (Critical)
The current `publish_and_store` method does not guarantee that an event stored in the database will eventually be published to Redis/WebSockets if the initial call fails.
*   **Requirement:** Implement a Transactional Outbox pattern.

### 6.2 State/Event Atomicity (High)
Business logic updates (e.g., changing a Job status) and event storage (e.g., `JobStartedEvent`) are performed as separate manual steps in the UOW.
*   **Risk:** Status changes without corresponding events, or vice versa.

### 6.3 Local WebSocket Registry (High)
Connections are pinned to the local process memory.
*   **Risk:** Zero visibility of events across a load-balanced cluster.

---

## 7. Auditor Decision: REJECTED
**Reasoning:** The implementation fails to meet distributed system reliability standards. Workflow state and event consistency can be lost during infrastructure partial failures (e.g., Redis blips). 

**Remediation Steps:**
1.  **Transactional Outbox:** Move event publication to a background process that polls the `stored_events` table.
2.  **Monotonic Sequencing:** Add a `sequence_number` (BigInt/Serial) to `StoredEvent` for deterministic replay.
3.  **Redis-Backed WS Manager:** Update `ConnectionManager` to subscribe to a Redis "global" channel to synchronize broadcasts across nodes.
4.  **Atomic State Transitions:** Wrap status updates and event persistence in a single unit-of-work transaction that is enforced at the service layer.
