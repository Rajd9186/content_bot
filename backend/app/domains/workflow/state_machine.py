from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    RETRYING = "RETRYING"

    @property
    def is_terminal(self) -> bool:
        return self in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELED)

    @property
    def is_active(self) -> bool:
        return self in (
            WorkflowStatus.QUEUED, WorkflowStatus.VALIDATING,
            WorkflowStatus.PROCESSING, WorkflowStatus.RETRYING,
        )


class ProcessingStage(str, Enum):
    PRE_PROCESS = "PRE_PROCESS"
    AGENT_DISPATCH = "AGENT_DISPATCH"
    AGENT_WORK = "AGENT_WORK"
    SYNTHESIS = "SYNTHESIS"
    POST_PROCESS = "POST_PROCESS"


class Trigger(str, Enum):
    SUBMIT = "submit"
    CANCEL = "cancel"
    DEQUEUE = "dequeue"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    DATA_READY = "data_ready"
    PRE_PROCESS_ERROR = "pre_process_error"
    AGENTS_CONFIGURED = "agents_configured"
    DISPATCH_ERROR = "dispatch_error"
    ALL_AGENTS_COMPLETE = "all_agents_complete"
    AGENT_TIMEOUT = "agent_timeout"
    ALL_AGENTS_FAILED = "all_agents_failed"
    SYNTHESIS_COMPLETE = "synthesis_complete"
    SYNTHESIS_ERROR = "synthesis_error"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"
    FINALIZE = "finalize"
    POST_PROCESS_ERROR = "post_process_error"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"


@dataclass
class TransitionDef:
    """Codified transition definition matching the architecture constitution."""

    trigger: str
    from_status: WorkflowStatus
    to_status: WorkflowStatus
    guard_description: str = ""
    side_effect_description: str = ""


TRANSITION_TABLE: List[TransitionDef] = [
    TransitionDef("submit", WorkflowStatus.DRAFT, WorkflowStatus.QUEUED,
                  "Owner match, quota check", "Emit workflow.job.started.v1"),
    TransitionDef("dequeue", WorkflowStatus.QUEUED, WorkflowStatus.VALIDATING,
                  "Capacity available", "Log queue wait time"),
    TransitionDef("cancel", WorkflowStatus.QUEUED, WorkflowStatus.CANCELED,
                  "Owner match", "Emit workflow.job.canceled.v1"),
    TransitionDef("validation_passed", WorkflowStatus.VALIDATING, WorkflowStatus.PROCESSING,
                  "All validators ok", "Initialize ProcessingStage to PRE_PROCESS"),
    TransitionDef("validation_failed", WorkflowStatus.VALIDATING, WorkflowStatus.FAILED,
                  "", "Record error details"),
    TransitionDef("data_ready", WorkflowStatus.PROCESSING, WorkflowStatus.PROCESSING,
                  "Chunks indexed", "Advance ProcessingStage to AGENT_DISPATCH"),
    TransitionDef("pre_process_error", WorkflowStatus.PROCESSING, WorkflowStatus.FAILED,
                  "", "Record error details"),
    TransitionDef("agents_configured", WorkflowStatus.PROCESSING, WorkflowStatus.PROCESSING,
                  "All agents resolved", "Dispatch agent tasks"),
    TransitionDef("dispatch_error", WorkflowStatus.PROCESSING, WorkflowStatus.FAILED,
                  "", "Record error details"),
    TransitionDef("all_agents_complete", WorkflowStatus.PROCESSING, WorkflowStatus.PROCESSING,
                  "All agents succeeded", "Collect agent outputs, advance to SYNTHESIS"),
    TransitionDef("agent_timeout", WorkflowStatus.PROCESSING, WorkflowStatus.FAILED,
                  "Duration > timeoutMs", "Record timeout, emit system.agent.failed.v2"),
    TransitionDef("all_agents_failed", WorkflowStatus.PROCESSING, WorkflowStatus.FAILED,
                  "Zero agents succeeded", "Record error details"),
    TransitionDef("synthesis_complete", WorkflowStatus.PROCESSING, WorkflowStatus.PROCESSING,
                  "Output validated", "Advance ProcessingStage to POST_PROCESS"),
    TransitionDef("synthesis_error", WorkflowStatus.PROCESSING, WorkflowStatus.FAILED,
                  "", "Record error details"),
    TransitionDef("insufficient_confidence", WorkflowStatus.PROCESSING, WorkflowStatus.PROCESSING,
                  "Confidence < threshold", "Re-dispatch to AGENT_WORK with refined prompt"),
    TransitionDef("finalize", WorkflowStatus.PROCESSING, WorkflowStatus.COMPLETED,
                  "All post-checks passed", "Emit workflow.job.completed.v1"),
    TransitionDef("retry_needed", WorkflowStatus.PROCESSING, WorkflowStatus.RETRYING,
                  "Retryable error in processing", "Increment retryCount, schedule retry"),
    TransitionDef("post_process_error", WorkflowStatus.PROCESSING, WorkflowStatus.FAILED,
                  "", "Record error details"),
    TransitionDef("retry", WorkflowStatus.FAILED, WorkflowStatus.QUEUED,
                  "retryCount < maxRetries", "Increment retryCount, emit retry event"),
    TransitionDef("dead_letter", WorkflowStatus.FAILED, WorkflowStatus.FAILED,
                  "retryCount >= maxRetries", "Emit dead-letter alert (no actual transition)"),
    TransitionDef("cancel", WorkflowStatus.DRAFT, WorkflowStatus.CANCELED,
                  "Owner match", "Emit workflow.job.canceled.v1"),
    TransitionDef("cancel", WorkflowStatus.VALIDATING, WorkflowStatus.CANCELED,
                  "Owner match", "Emit workflow.job.canceled.v1"),
    TransitionDef("cancel", WorkflowStatus.RETRYING, WorkflowStatus.CANCELED,
                  "Owner match", "Emit workflow.job.canceled.v1"),
    TransitionDef("retry_ready", WorkflowStatus.RETRYING, WorkflowStatus.PROCESSING,
                  "Backoff elapsed, capacity available", "Resume processing"),
    TransitionDef("retry_failed", WorkflowStatus.RETRYING, WorkflowStatus.FAILED,
                  "Retry count exhausted", "Record final error details"),
]

TRANSITION_BY_TRIGGER: Dict[str, List[TransitionDef]] = {}
for td in TRANSITION_TABLE:
    key = td.trigger
    if key not in TRANSITION_BY_TRIGGER:
        TRANSITION_BY_TRIGGER[key] = []
    TRANSITION_BY_TRIGGER[key].append(td)

TRANSITION_RULES: Dict[WorkflowStatus, set[WorkflowStatus]] = {}
for td in TRANSITION_TABLE:
    if td.from_status not in TRANSITION_RULES:
        TRANSITION_RULES[td.from_status] = set()
    TRANSITION_RULES[td.from_status].add(td.to_status)

for status in WorkflowStatus:
    if status not in TRANSITION_RULES:
        TRANSITION_RULES[status] = set()

Guard = Callable[[str, str, str, dict[str, Any]], Coroutine[Any, Any, bool]]
SideEffect = Callable[[str, str, str, dict[str, Any]], Coroutine[Any, Any, None]]


class StateMachine:
    def __init__(self) -> None:
        self._guards: Dict[str, List[Guard]] = {}
        self._side_effects: Dict[str, List[SideEffect]] = {}

    def add_guard(self, from_status: str, to_status: str, guard: Guard) -> None:
        key = f"{from_status}->{to_status}"
        if key not in self._guards:
            self._guards[key] = []
        self._guards[key].append(guard)

    def add_side_effect(self, from_status: str, to_status: str, effect: SideEffect) -> None:
        key = f"{from_status}->{to_status}"
        if key not in self._side_effects:
            self._side_effects[key] = []
        self._side_effects[key].append(effect)

    def validate_trigger(
        self, from_status: str, trigger: str,
    ) -> List[TransitionDef]:
        """Get valid target transitions for a given trigger from a status."""
        results: List[TransitionDef] = []
        for td in TRANSITION_BY_TRIGGER.get(trigger, []):
            if td.from_status.value == from_status or td.from_status == from_status:
                results.append(td)
        return results

    async def can_transition(
        self, from_status: str, to_status: str,
        job_id: str, workspace_id: str, context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        ctx = context or {}
        try:
            current = WorkflowStatus(from_status)
            target = WorkflowStatus(to_status)
        except ValueError:
            return False, f"Invalid status: {from_status} or {to_status}"

        allowed = TRANSITION_RULES.get(current, set())
        if target not in allowed:
            return False, (
                f"Transition '{from_status}' -> '{to_status}' is not allowed. "
                f"Allowed from '{from_status}': {[s.value for s in allowed]}"
            )

        key = f"{from_status}->{to_status}"
        for guard in self._guards.get(key, []):
            if not await guard(job_id, workspace_id, to_status, ctx):
                return False, f"Guard blocked transition '{from_status}' -> '{to_status}'"

        return True, ""

    async def transition(
        self, from_status: str, to_status: str,
        job_id: str, workspace_id: str, context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        allowed, reason = await self.can_transition(
            from_status, to_status, job_id, workspace_id, ctx,
        )
        if not allowed:
            raise ValueError(f"Transition rejected: {reason}")

        key = f"{from_status}->{to_status}"
        for effect in self._side_effects.get(key, []):
            await effect(job_id, workspace_id, to_status, ctx)

    def find_transition_by_trigger(
        self, from_status: str, trigger: str,
    ) -> Optional[TransitionDef]:
        """Find the transition definition matching a trigger from a given status."""
        for td in TRANSITION_TABLE:
            if td.from_status.value == from_status and td.trigger == trigger:
                return td
        return None

    def get_allowed_triggers(self, from_status: str) -> List[str]:
        """Get all valid triggers from a given status."""
        triggers: List[str] = []
        for td in TRANSITION_TABLE:
            if td.from_status.value == from_status and td.trigger not in triggers:
                triggers.append(td.trigger)
        return triggers


workflow_state_machine = StateMachine()
