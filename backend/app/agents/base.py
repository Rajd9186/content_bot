from __future__ import annotations

import asyncio
import logging
from abc import ABC
from datetime import UTC, datetime
from typing import Any, Optional

from app.agents.contracts import (
    AgentContract,
    AgentInput,
    AgentOutput,
    AgentStatus,
    AgentTelemetry,
    ValidationResult,
)
from app.agents.prompt.engine import PromptContext, prompt_engine
from app.agents.provider.base import BaseProvider, ProviderRequest
from app.agents.provider.factory import provider_factory
from app.agents.retry.policy import RetryPolicyExecutor
from app.agents.pipeline import ExecutionPipeline, PipelineStage
from app.agents.telemetry.collector import telemetry_collector
from app.agents.validation.parser import ResponseParser
from app.agents.validation.recovery import fallback_generator
from app.agents.validation.schema import SchemaValidator
from app.services.context_assembly_engine import ContextAssemblyEngine
from app.services.embedding_service import EmbeddingService
from app.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(
        self,
        contract: AgentContract,
        provider_name: str = "openai",
        model: str | None = None,
        uow: Optional[UnitOfWork] = None,
    ) -> None:
        self._contract = contract
        self._provider_name = provider_name
        self._model = model
        self._uow = uow
        self._response_parser = ResponseParser()
        self._schema_validator = SchemaValidator()
        self._fallback_generator = fallback_generator
        self._telemetry_collector = telemetry_collector
        self._prompt_engine = prompt_engine
        self._provider: BaseProvider | None = None
        self._retry_executor = RetryPolicyExecutor(contract.retry_policy)
        self._cancelled = False
        
        # Intelligence Layer components
        self._embedding_service = EmbeddingService()
        self._context_engine = ContextAssemblyEngine(
            uow=self._uow, 
            embedding_service=self._embedding_service
        ) if self._uow else None
        
        # Execution pipeline
        self._pipeline = ExecutionPipeline(self)

    @property
    def name(self) -> str:
        return self._contract.name

    @property
    def contract(self) -> AgentContract:
        return self._contract

    async def _get_provider(self) -> BaseProvider:
        if self._provider is None:
            self._provider = provider_factory.get_or_create(
                self._provider_name, self._model
            )
        return self._provider

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        telemetry = self._telemetry_collector.create_telemetry(
            agent_name=self.name,
            correlation_id=agent_input.correlation_id,
            workflow_id=agent_input.workflow_id,
        )
        telemetry.status = AgentStatus.VALIDATING_INPUT
        telemetry.started_at = datetime.now(UTC).isoformat()

        try:
            validation = await self._validate_input(agent_input)
            if not validation.valid:
                telemetry.status = AgentStatus.FAILED
                telemetry.error = "; ".join(validation.errors)
                self._telemetry_collector.record(telemetry)
                return AgentOutput(
                    success=False,
                    error=telemetry.error,
                    telemetry=telemetry,
                )

            telemetry.status = AgentStatus.CONSTRUCTING_PROMPT
            prompt_context = await self._build_prompt(agent_input)

            telemetry.status = AgentStatus.EXECUTING
            success, result_data, error = await self._execute_with_retry(
                prompt_context, agent_input,
            )

            if not success:
                telemetry.status = AgentStatus.FALLBACK
                telemetry.fallback_used = True
                result_data = self._generate_fallback(agent_input, error or "Unknown error")
                telemetry.error = error

            telemetry.status = AgentStatus.COMPLETED
            telemetry.completed_at = datetime.now(UTC).isoformat()
            telemetry.latency_ms = self._compute_latency(telemetry)
            self._telemetry_collector.record(telemetry)

            return AgentOutput(
                success=True,
                data=result_data or {},
                telemetry=telemetry,
            )

        except asyncio.CancelledError:
            telemetry.status = AgentStatus.CANCELLED
            telemetry.completed_at = datetime.now(UTC).isoformat()
            telemetry.error = "Agent execution cancelled"
            self._telemetry_collector.record(telemetry)
            return AgentOutput(
                success=False, error="Cancelled", telemetry=telemetry,
            )

        except Exception as e:
            telemetry.status = AgentStatus.FAILED
            telemetry.completed_at = datetime.now(UTC).isoformat()
            telemetry.error = str(e)
            self._telemetry_collector.record(telemetry)
            return AgentOutput(
                success=False, error=str(e), telemetry=telemetry,
            )

    async def _validate_input(self, agent_input: AgentInput) -> ValidationResult:
        return ValidationResult(valid=True)

    async def _build_prompt(self, agent_input: AgentInput) -> PromptContext:
        # 1. Assemble Project Intelligence Context if project_id is present
        project_id = agent_input.metadata.get("project_id")
        if project_id and self._context_engine:
            try:
                context_package = await self._context_engine.assemble_context(project_id, agent_input.prompt)
                system_augmentation = self._context_engine.format_as_system_prompt(context_package)
                
                # Inject augmented knowledge into the prompt context
                # We append it to the system prompt to ensure the LLM prioritizes this knowledge
                prompt_ctx = await self._prompt_engine.build(
                    agent_type=self._contract.name,
                    correlation_id=agent_input.correlation_id,
                    template_kwargs=agent_input.metadata.get("template_kwargs", {}),
                )
                
                if prompt_ctx.system_prompt:
                    prompt_ctx.system_prompt += f"\n\n{system_augmentation}"
                else:
                    prompt_ctx.system_prompt = system_augmentation
                
                return prompt_ctx
            except Exception as e:
                logger.error(f"Project intelligence augmentation failed: {e}")

        # Fallback to standard prompt building
        return await self._prompt_engine.build(
            agent_type=self._contract.name,
            correlation_id=agent_input.correlation_id,
            template_kwargs=agent_input.metadata.get("template_kwargs", {}),
        )

    async def _execute_with_retry(
        self, prompt_context: PromptContext, agent_input: AgentInput,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        return await self._retry_executor.execute_with_retry(
            self._execute_single, prompt_context, agent_input,
            on_retry=self._on_retry,
        )

    async def _execute_single(
        self, prompt_context: PromptContext, agent_input: AgentInput,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        self._check_cancelled()

        provider = await self._get_provider()
        request = self._build_provider_request(prompt_context)

        timeout_policy = self._contract.timeout_policy
        try:
            response = await asyncio.wait_for(
                provider.execute(request),
                timeout=timeout_policy.execution_ms / 1000,
            )
        except TimeoutError:
            return False, None, "Provider execution timed out"

        if not response.success:
            return False, None, response.error or "Provider execution failed"

        self._check_cancelled()

        parsed = await self._parse_output(response.content, agent_input)
        if parsed is None:
            return False, None, "Failed to parse LLM output"

        validation = await self._validate_output(parsed, agent_input)
        if not validation.valid:
            errors = "; ".join(validation.errors)
            return False, None, f"Output validation failed: {errors}"

        return True, parsed, None

    def _build_provider_request(self, prompt_context: PromptContext) -> ProviderRequest:
        messages = prompt_context.messages
        system_prompt = prompt_context.system_prompt
        return ProviderRequest(
            model=self._model or "",
            system_prompt=system_prompt,
            messages=[m for m in messages if m["role"] != "system"],
            temperature=0.1,
            max_tokens=4096,
            timeout_ms=self._contract.timeout_policy.execution_ms,
        )

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> dict[str, Any] | None:
        return self._parse_json_output(content)

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        return ValidationResult(valid=True)

    def _parse_json_output(self, content: str) -> dict[str, Any] | None:
        parsed, error = self._response_parser.parse_json(content)
        if error:
            logger.warning("JSON parsing failed for %s: %s", self.name, error)
        return parsed

    def _generate_fallback(
        self, agent_input: AgentInput, error: str,
    ) -> dict[str, Any]:
        original_kwargs = agent_input.metadata.get("template_kwargs", {})
        return self._fallback_generator.generate_fallback_output(
            agent_type=self._contract.name,
            original_kwargs=original_kwargs,
            error=error,
        )

    async def _on_retry(self, attempt: int, error: str) -> None:
        logger.info(
            "Agent %s retry %d: %s", self.name, attempt, error,
        )

    def cancel(self) -> None:
        self._cancelled = True

    def _check_cancelled(self) -> None:
        if self._cancelled:
            raise asyncio.CancelledError(f"Agent {self.name} was cancelled")

    def _compute_latency(self, telemetry: AgentTelemetry) -> float:
        if telemetry.started_at and telemetry.completed_at:
            start = datetime.fromisoformat(telemetry.started_at)
            end = datetime.fromisoformat(telemetry.completed_at)
            return (end - start).total_seconds() * 1000
        return 0.0
