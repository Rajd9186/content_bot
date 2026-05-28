from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATING_INPUT = "VALIDATING_INPUT"
    CONSTRUCTING_PROMPT = "CONSTRUCTING_PROMPT"
    EXECUTING = "EXECUTING"
    PARSING_OUTPUT = "PARSING_OUTPUT"
    VALIDATING_OUTPUT = "VALIDATING_OUTPUT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    FALLBACK = "FALLBACK"
    CANCELLED = "CANCELLED"


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    provider: str = ""
    model: str = ""


class AgentTelemetry(BaseModel):
    agent_name: str = ""
    status: AgentStatus = AgentStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    latency_ms: float = 0.0
    token_usage: TokenUsage = TokenUsage()
    retry_count: int = 0
    fallback_used: bool = False
    error: Optional[str] = None
    correlation_id: Optional[str] = None
    workflow_id: Optional[str] = None


class ValidationResult(BaseModel):
    valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RetryPolicy(BaseModel):
    max_retries: int = 3
    base_delay_ms: float = 1000.0
    max_delay_ms: float = 30000.0
    jitter_factor: float = 0.1
    retryable_errors: list[str] = Field(default_factory=lambda: [
        "timeout", "rate_limit", "provider_error",
        "server_error", "malformed_response",
    ])
    provider_failover: bool = True


class TimeoutPolicy(BaseModel):
    execution_ms: int = 120000
    prompt_construction_ms: int = 5000
    parsing_ms: int = 10000


class AgentInput(BaseModel):
    correlation_id: str
    workflow_id: Optional[str] = None
    workspace_id: Optional[str] = None
    content_item_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    success: bool = False
    data: dict[str, Any] = Field(default_factory=dict)
    telemetry: AgentTelemetry = Field(default_factory=AgentTelemetry)
    error: Optional[str] = None


class AgentContract(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    input_schema: type = AgentInput
    output_schema: type = AgentOutput
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_policy: TimeoutPolicy = Field(default_factory=TimeoutPolicy)
    required_capabilities: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class ProviderConfig(BaseModel):
    name: str
    model: str
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout_ms: int = 60000
    max_retries: int = 3


T = TypeVar("T")
AsyncHandler = Callable[..., Coroutine[Any, Any, None]]
