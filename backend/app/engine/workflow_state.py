"""Explicit workflow state machine with validated transitions.

States:
  CREATED → PLANNING → RESEARCHING → WRITING → DRAFT_READY
  DRAFT_READY → REVIEW_PENDING | COMPLETED
  REVIEW_PENDING → REVISING | VERIFYING | COMPLETED
  REVISING → DRAFT_READY
  VERIFYING → DRAFT_READY | COMPLETED
  Any → FAILED | CANCELLED
"""

from __future__ import annotations

import enum
from typing import Optional


class WorkflowStage(str, enum.Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    RESEARCHING = "RESEARCHING"
    WRITING = "WRITING"
    DRAFT_READY = "DRAFT_READY"
    REVIEW_PENDING = "REVIEW_PENDING"
    REVISING = "REVISING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WAITING_FOR_USER = "WAITING_FOR_USER"

    @classmethod
    def terminal(cls) -> set[WorkflowStage]:
        return {cls.COMPLETED, cls.FAILED, cls.CANCELLED}

    @classmethod
    def active(cls) -> set[WorkflowStage]:
        return {
            cls.PLANNING, cls.RESEARCHING, cls.WRITING,
            cls.DRAFT_READY, cls.REVIEW_PENDING, cls.REVISING,
            cls.VERIFYING, cls.WAITING_FOR_USER,
        }


# Valid transitions: current -> set(valid next)
TRANSITIONS: dict[WorkflowStage, set[WorkflowStage]] = {
    WorkflowStage.CREATED: {WorkflowStage.PLANNING, WorkflowStage.FAILED, WorkflowStage.CANCELLED},
    WorkflowStage.PLANNING: {WorkflowStage.RESEARCHING, WorkflowStage.FAILED, WorkflowStage.CANCELLED},
    WorkflowStage.RESEARCHING: {WorkflowStage.WRITING, WorkflowStage.FAILED, WorkflowStage.CANCELLED},
    WorkflowStage.WRITING: {WorkflowStage.DRAFT_READY, WorkflowStage.FAILED, WorkflowStage.CANCELLED},
    WorkflowStage.DRAFT_READY: {
        WorkflowStage.WAITING_FOR_USER, WorkflowStage.REVIEW_PENDING,
        WorkflowStage.COMPLETED, WorkflowStage.FAILED, WorkflowStage.CANCELLED,
    },
    WorkflowStage.REVIEW_PENDING: {
        WorkflowStage.REVISING, WorkflowStage.VERIFYING,
        WorkflowStage.COMPLETED, WorkflowStage.FAILED, WorkflowStage.CANCELLED,
    },
    WorkflowStage.REVISING: {WorkflowStage.DRAFT_READY, WorkflowStage.FAILED, WorkflowStage.CANCELLED},
    WorkflowStage.VERIFYING: {WorkflowStage.DRAFT_READY, WorkflowStage.COMPLETED, WorkflowStage.FAILED, WorkflowStage.CANCELLED},
    WorkflowStage.WAITING_FOR_USER: {
        WorkflowStage.REVIEW_PENDING, WorkflowStage.REVISING,
        WorkflowStage.WRITING, WorkflowStage.COMPLETED,
        WorkflowStage.FAILED, WorkflowStage.CANCELLED,
    },
    # Terminal states have no valid transitions
    WorkflowStage.COMPLETED: set(),
    WorkflowStage.FAILED: set(),
    WorkflowStage.CANCELLED: set(),
}


class IllegalTransitionError(ValueError):
    """Raised when an invalid workflow stage transition is attempted."""

    def __init__(self, current: WorkflowStage, attempted: WorkflowStage):
        self.current = current
        self.attempted = attempted
        super().__init__(f"Illegal transition: {current.value} -> {attempted.value}")


def validate_transition(current: WorkflowStage, next_stage: WorkflowStage) -> None:
    """Validate that a stage transition is legal. Raises IllegalTransitionError if not."""
    allowed = TRANSITIONS.get(current, set())
    if next_stage not in allowed:
        raise IllegalTransitionError(current, next_stage)


def can_transition_to(current: WorkflowStage, next_stage: WorkflowStage) -> bool:
    """Check if a stage transition is legal without raising."""
    return next_stage in TRANSITIONS.get(current, set())


def is_terminal(stage: WorkflowStage) -> bool:
    return stage in WorkflowStage.terminal()


def is_active(stage: WorkflowStage) -> bool:
    return stage in WorkflowStage.active()


def stage_display_name(stage: WorkflowStage) -> str:
    """Human-readable stage name."""
    names = {
        WorkflowStage.CREATED: "Created",
        WorkflowStage.PLANNING: "Planning",
        WorkflowStage.RESEARCHING: "Researching",
        WorkflowStage.WRITING: "Writing",
        WorkflowStage.DRAFT_READY: "Draft Ready",
        WorkflowStage.REVIEW_PENDING: "Awaiting Review",
        WorkflowStage.REVISING: "Revising",
        WorkflowStage.VERIFYING: "Verifying",
        WorkflowStage.COMPLETED: "Completed",
        WorkflowStage.FAILED: "Failed",
        WorkflowStage.CANCELLED: "Cancelled",
        WorkflowStage.WAITING_FOR_USER: "Waiting for User",
    }
    return names.get(stage, stage.value)
