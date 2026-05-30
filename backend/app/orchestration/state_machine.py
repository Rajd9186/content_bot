from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from app.orchestration.stages import (
    STAGE_MAX_RETRIES,
    STAGE_TIMEOUT_SECONDS,
    STAGE_TRANSITIONS,
    WorkflowRun,
    WorkflowStage,
    validate_transition,
)

logger = logging.getLogger(__name__)

OrchestrationGuard = Callable[[WorkflowRun, WorkflowStage, dict[str, Any]], Coroutine[Any, Any, bool]]
OrchestrationSideEffect = Callable[
    [WorkflowRun, WorkflowStage, WorkflowStage, dict[str, Any]],
    Coroutine[Any, Any, None],
]


@dataclass
class StageTransitionDef:
    """Codified stage transition definition."""
    from_stage: WorkflowStage
    to_stage: WorkflowStage
    trigger: str
    guard_description: str = ""
    side_effect_description: str = ""
    timeout_seconds: int = 120
    max_retries: int = 3


STAGE_TRANSITION_TABLE: list[StageTransitionDef] = [
    StageTransitionDef(WorkflowStage.INIT, WorkflowStage.PLANNING, "begin",
                       "Content brief present", "Emit workflow started event",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.INIT],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.INIT]),
    StageTransitionDef(WorkflowStage.PLANNING, WorkflowStage.RESEARCH, "plan_complete",
                       "Research plan validated", "Initialize research queries",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.PLANNING],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.PLANNING]),
    StageTransitionDef(WorkflowStage.RESEARCH, WorkflowStage.SYNTHESIS, "research_complete",
                       "All sources collected", "Compile research findings",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.RESEARCH],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.RESEARCH]),
    StageTransitionDef(WorkflowStage.SYNTHESIS, WorkflowStage.OUTLINING, "synthesize_complete",
                       "Synthesis output validated", "Generate outline",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.SYNTHESIS],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.SYNTHESIS]),
    StageTransitionDef(WorkflowStage.OUTLINING, WorkflowStage.WRITING, "outline_complete",
                       "Outline structure approved", "Begin content writing",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.OUTLINING],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.OUTLINING]),
    StageTransitionDef(WorkflowStage.WRITING, WorkflowStage.VALIDATION, "writing_complete",
                       "Content draft complete", "Validate content quality",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.WRITING],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.WRITING]),
    StageTransitionDef(WorkflowStage.VALIDATION, WorkflowStage.SEO, "validation_passed",
                       "Quality checks passed", "Optimize for SEO",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.VALIDATION],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.VALIDATION]),
    StageTransitionDef(WorkflowStage.VALIDATION, WorkflowStage.FACT_CHECK, "validation_passed",
                       "Quality checks passed", "Verify facts",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.VALIDATION],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.VALIDATION]),
    StageTransitionDef(WorkflowStage.SEO, WorkflowStage.FACT_CHECK, "seo_complete",
                       "SEO metadata generated", "Verify facts",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.SEO],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.SEO]),
    StageTransitionDef(WorkflowStage.SEO, WorkflowStage.FINALIZATION, "seo_complete",
                       "SEO metadata generated", "Prepare final output",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.SEO],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.SEO]),
    StageTransitionDef(WorkflowStage.FACT_CHECK, WorkflowStage.FINALIZATION, "fact_check_complete",
                       "All facts verified", "Prepare final output",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.FACT_CHECK],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.FACT_CHECK]),
    StageTransitionDef(WorkflowStage.FINALIZATION, WorkflowStage.PUBLISHED, "finalize",
                       "All pre-publish checks passed", "Publish content, emit completed event",
                       timeout_seconds=STAGE_TIMEOUT_SECONDS[WorkflowStage.FINALIZATION],
                       max_retries=STAGE_MAX_RETRIES[WorkflowStage.FINALIZATION]),
]


class OrchestrationStateMachine:
    """State machine for orchestration stage transitions.

    Wraps WorkflowStage transitions with guards, side effects,
    and the full transition table codified from the architecture.
    """

    def __init__(self) -> None:
        self._guards: dict[str, list[OrchestrationGuard]] = {}
        self._side_effects: dict[str, list[OrchestrationSideEffect]] = {}

    def add_guard(self, from_stage: str, to_stage: str, guard: OrchestrationGuard) -> None:
        key = f"{from_stage}->{to_stage}"
        if key not in self._guards:
            self._guards[key] = []
        self._guards[key].append(guard)

    def add_side_effect(self, from_stage: str, to_stage: str, effect: OrchestrationSideEffect) -> None:
        key = f"{from_stage}->{to_stage}"
        if key not in self._side_effects:
            self._side_effects[key] = []
        self._side_effects[key].append(effect)

    async def can_transition(
        self, run: WorkflowRun, from_stage: WorkflowStage, to_stage: WorkflowStage,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if a stage transition is allowed."""
        try:
            validate_transition(from_stage, to_stage)
        except ValueError as e:
            logger.warning("Stage transition blocked: %s", e)
            return False

        ctx = context or {}
        key = f"{from_stage.value}->{to_stage.value}"
        for guard in self._guards.get(key, []):
            if not await guard(run, to_stage, ctx):
                return False
        return True

    async def transition(
        self, run: WorkflowRun, from_stage: WorkflowStage, to_stage: WorkflowStage,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Execute a stage transition with guard checks and side effects."""
        if not await self.can_transition(run, from_stage, to_stage, context):
            raise ValueError(
                f"Stage transition rejected: {from_stage.value} -> {to_stage.value}"
            )

        ctx = context or {}
        key = f"{from_stage.value}->{to_stage.value}"
        for effect in self._side_effects.get(key, []):
            await effect(run, from_stage, to_stage, ctx)

    def find_transition(self, from_stage: WorkflowStage, to_stage: WorkflowStage) -> StageTransitionDef | None:
        """Find the transition definition for a given from/to pair."""
        for td in STAGE_TRANSITION_TABLE:
            if td.from_stage == from_stage and td.to_stage == to_stage:
                return td
        return None

    def find_transitions_by_trigger(self, trigger: str) -> list[StageTransitionDef]:
        """Find all transitions matching a trigger name."""
        return [td for td in STAGE_TRANSITION_TABLE if td.trigger == trigger]

    def get_allowed_transitions(self, from_stage: WorkflowStage) -> list[StageTransitionDef]:
        """Get all valid transitions from a given stage."""
        allowed = STAGE_TRANSITIONS.get(from_stage, set())
        return [td for td in STAGE_TRANSITION_TABLE if td.from_stage == from_stage and td.to_stage in allowed]


orchestration_state_machine = OrchestrationStateMachine()
