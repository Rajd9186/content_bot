from __future__ import annotations

from typing import Any

import pytest

from app.agents.contracts import (
    AgentContract, AgentInput, RetryPolicy, TimeoutPolicy,
)


@pytest.fixture
def sample_contract() -> AgentContract:
    return AgentContract(
        name="test_agent",
        description="Test agent for unit tests",
        version="1.0.0",
        retry_policy=RetryPolicy(max_retries=2, base_delay_ms=100.0),
        timeout_policy=TimeoutPolicy(execution_ms=30000),
    )


@pytest.fixture
def sample_agent_input() -> AgentInput:
    return AgentInput(
        correlation_id="test-correlation-123",
        workflow_id="test-workflow-456",
        metadata={
            "template_kwargs": {
                "topic": "Artificial Intelligence",
                "goals": "Explain AI concepts",
                "audience": "Beginners",
                "outline": "1. Introduction\n2. Key Concepts\n3. Applications",
                "title": "AI for Beginners",
                "content": "# Test\n\nThis is test content for validation.",
            }
        },
    )
