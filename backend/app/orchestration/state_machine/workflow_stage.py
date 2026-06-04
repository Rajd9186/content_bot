import enum
from typing import Optional


class WorkflowStage(str, enum.Enum):
    INIT = "INIT"
    PLANNING = "PLANNING"
    RESEARCH = "RESEARCH"
    SYNTHESIS = "SYNTHESIS"
    OUTLINING = "OUTLINING"
    WRITING = "WRITING"
    VALIDATION = "VALIDATION"
    SEO = "SEO"
    FACT_CHECK = "FACT_CHECK"
    FINALIZATION = "FINALIZATION"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


STAGE_ORDER = [
    WorkflowStage.INIT,
    WorkflowStage.PLANNING,
    WorkflowStage.RESEARCH,
    WorkflowStage.SYNTHESIS,
    WorkflowStage.OUTLINING,
    WorkflowStage.WRITING,
    WorkflowStage.VALIDATION,
    WorkflowStage.SEO,
    WorkflowStage.FACT_CHECK,
    WorkflowStage.FINALIZATION,
    WorkflowStage.PUBLISHED,
]

TERMINAL_STAGES = {WorkflowStage.PUBLISHED, WorkflowStage.FAILED}


class StageStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


VALID_TRANSITIONS: dict[WorkflowStage, set[WorkflowStage]] = {
    WorkflowStage.INIT: {WorkflowStage.PLANNING, WorkflowStage.FAILED},
    WorkflowStage.PLANNING: {WorkflowStage.RESEARCH, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.RESEARCH: {WorkflowStage.SYNTHESIS, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.SYNTHESIS: {WorkflowStage.OUTLINING, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.OUTLINING: {WorkflowStage.WRITING, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.WRITING: {WorkflowStage.VALIDATION, WorkflowStage.FAILED, WorkflowStage.BLOCKED, WorkflowStage.RESEARCH},
    WorkflowStage.VALIDATION: {WorkflowStage.SEO, WorkflowStage.WRITING, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.SEO: {WorkflowStage.FACT_CHECK, WorkflowStage.WRITING, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.FACT_CHECK: {WorkflowStage.FINALIZATION, WorkflowStage.WRITING, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.FINALIZATION: {WorkflowStage.PUBLISHED, WorkflowStage.FAILED, WorkflowStage.BLOCKED},
    WorkflowStage.PUBLISHED: set(),
    WorkflowStage.FAILED: {WorkflowStage.INIT},
    WorkflowStage.BLOCKED: {WorkflowStage.INIT, WorkflowStage.FAILED},
}


class IllegalTransitionError(ValueError):
    def __init__(self, current: WorkflowStage, attempted: WorkflowStage):
        self.current = current
        self.attempted = attempted
        super().__init__(f"Illegal transition: {current.value} -> {attempted.value}")


def validate_transition(current: WorkflowStage, next_stage: WorkflowStage) -> None:
    allowed = VALID_TRANSITIONS.get(current, set())
    if next_stage not in allowed:
        raise IllegalTransitionError(current, next_stage)


def can_transition(current: WorkflowStage, next_stage: WorkflowStage) -> bool:
    return next_stage in VALID_TRANSITIONS.get(current, set())


def is_terminal(stage: WorkflowStage) -> bool:
    return stage in TERMINAL_STAGES


def stage_display_name(stage: WorkflowStage) -> str:
    return stage.value.replace("_", " ").title()
