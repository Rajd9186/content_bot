from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Optional

from app.agents.contracts import (
    AgentInput, AgentOutput, AgentStatus, TokenUsage,
)
from app.agents.base import BaseAgent
from app.agents.provider.base import ProviderRequest, ProviderResponse
from app.agents.prompt.engine import PromptContext, prompt_engine
from app.agents.provider.factory import provider_factory
from app.agents.retry.policy import RetryPolicyExecutor
from app.agents.telemetry.collector import telemetry_collector
from app.agents.validation.parser import ResponseParser
from app.agents.validation.recovery import fallback_generator

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    INPUT_VALIDATION = "input_validation"
    PROMPT_CONSTRUCTION = "prompt_construction"
    PROVIDER_SELECTION = "provider_selection"
    LLM_EXECUTION = "llm_execution"
    OUTPUT_PARSING = "output_parsing"
    SCHEMA_VALIDATION = "schema_validation"
    RETRY_HANDLING = "retry_handling"
    FALLBACK_HANDLING = "fallback_handling"
    TELEMETRY_CAPTURE = "telemetry_capture"
    EVENT_EMISSION = "event_emission"


StageHook = Callable[
    [PipelineStage, AgentInput, Optional[dict[str, Any]]],
    Coroutine[Any, Any, None],
]


class ExecutionPipeline:
    def __init__(self, agent: BaseAgent) -> None:
        self._agent = agent
        self._hooks: list[StageHook] = []
        self._stage_timings: dict[str, float] = {}

    def add_hook(self, hook: StageHook) -> None:
        self._hooks.append(hook)

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        telemetry = telemetry_collector.create_telemetry(
            agent_name=self._agent.name,
            correlation_id=agent_input.correlation_id,
            workflow_id=agent_input.workflow_id,
        )
        telemetry.started_at = datetime.now(timezone.utc).isoformat()

        stage_data: dict[str, Any] = {}
        fallback_used = False
        final_error: Optional[str] = None

        try:
            stage_data["input"] = agent_input

            await self._run_stage(
                PipelineStage.INPUT_VALIDATION, agent_input, stage_data,
                self._stage_input_validation,
            )
            telemetry.status = AgentStatus.VALIDATING_INPUT

            await self._run_stage(
                PipelineStage.PROMPT_CONSTRUCTION, agent_input, stage_data,
                self._stage_prompt_construction,
            )
            telemetry.status = AgentStatus.CONSTRUCTING_PROMPT

            await self._run_stage(
                PipelineStage.PROVIDER_SELECTION, agent_input, stage_data,
                self._stage_provider_selection,
            )

            telemetry.status = AgentStatus.EXECUTING
            execution_success = False
            retry_count = 0
            provider_responses: list[ProviderResponse] = []

            retry_executor = RetryPolicyExecutor(
                self._agent.contract.retry_policy
            )

            async def execute_attempt() -> tuple[bool, Any, Optional[str]]:
                nonlocal retry_count
                retry_count += 1
                return await self._execute_llm_attempt(stage_data, provider_responses)

            execution_success, execution_result, execution_error = (
                await retry_executor.execute_with_retry(
                    execute_attempt,  # type: ignore
                    on_retry=self._on_pipeline_retry,
                )
            )

            telemetry.retry_count = retry_count - 1
            stage_data["provider_responses"] = provider_responses
            stage_data["token_usage"] = self._aggregate_tokens(provider_responses)

            if not execution_success:
                telemetry.status = AgentStatus.FALLBACK
                fallback_used = True
                final_error = execution_error
                stage_data["output"] = await self._run_stage(
                    PipelineStage.FALLBACK_HANDLING, agent_input, stage_data,
                    self._stage_fallback_handling,
                )
            else:
                telemetry.status = AgentStatus.PARSING_OUTPUT
                stage_data["output"] = execution_result

            telemetry.status = AgentStatus.VALIDATING_OUTPUT
            await self._run_stage(
                PipelineStage.SCHEMA_VALIDATION, agent_input, stage_data,
                self._stage_schema_validation,
            )

            await self._run_stage(
                PipelineStage.TELEMETRY_CAPTURE, agent_input, stage_data,
                self._stage_telemetry_capture,
            )

            await self._run_stage(
                PipelineStage.EVENT_EMISSION, agent_input, stage_data,
                self._stage_event_emission,
            )

            telemetry.status = AgentStatus.COMPLETED
            telemetry.completed_at = datetime.now(timezone.utc).isoformat()
            telemetry.latency_ms = self._compute_total_latency(telemetry)
            telemetry.fallback_used = fallback_used
            telemetry.error = final_error

            telemetry_collector.record(telemetry)

            return AgentOutput(
                success=True,
                data=stage_data.get("output", {}),
                telemetry=telemetry,
            )

        except asyncio.CancelledError:
            telemetry.status = AgentStatus.CANCELLED
            telemetry.completed_at = datetime.now(timezone.utc).isoformat()
            telemetry.error = "Pipeline execution cancelled"
            telemetry_collector.record(telemetry)
            return AgentOutput(
                success=False, error="Cancelled", telemetry=telemetry,
            )

        except Exception as e:
            telemetry.status = AgentStatus.FAILED
            telemetry.completed_at = datetime.now(timezone.utc).isoformat()
            telemetry.error = str(e)
            telemetry_collector.record(telemetry)
            return AgentOutput(
                success=False, error=str(e), telemetry=telemetry,
            )

    async def _run_stage(
        self,
        stage: PipelineStage,
        agent_input: AgentInput,
        stage_data: dict[str, Any],
        stage_fn: Callable[
            [AgentInput, dict[str, Any]],
            Coroutine[Any, Any, Any],
        ],
    ) -> Any:
        start = time.monotonic()
        try:
            result = await stage_fn(agent_input, stage_data)
            elapsed = (time.monotonic() - start) * 1000
            self._stage_timings[stage.value] = elapsed

            for hook in self._hooks:
                try:
                    await hook(stage, agent_input, stage_data)
                except Exception as hook_err:
                    logger.warning(
                        "Pipeline hook failed at stage %s: %s",
                        stage.value, hook_err,
                    )

            return result
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self._stage_timings[stage.value] = elapsed
            logger.error(
                "Pipeline stage %s failed: %s", stage.value, e,
            )
            raise

    async def _stage_input_validation(
        self, agent_input: AgentInput, stage_data: dict[str, Any],
    ) -> None:
        validation = await self._agent._validate_input(agent_input)
        if not validation.valid:
            raise ValueError(
                f"Input validation failed: {'; '.join(validation.errors)}"
            )
        stage_data["validation_result"] = validation

    async def _stage_prompt_construction(
        self, agent_input: AgentInput, stage_data: dict[str, Any],
    ) -> PromptContext:
        ctx = await self._agent._build_prompt(agent_input)
        stage_data["prompt_context"] = ctx
        return ctx

    async def _stage_provider_selection(
        self, agent_input: AgentInput, stage_data: dict[str, Any],
    ) -> None:
        provider = await self._agent._get_provider()
        prompt_context = stage_data.get("prompt_context")
        if prompt_context:
            request = self._agent._build_provider_request(prompt_context)
            stage_data["provider_request"] = request
            stage_data["provider"] = provider

    async def _execute_llm_attempt(
        self,
        stage_data: dict[str, Any],
        provider_responses: list[ProviderResponse],
    ) -> tuple[bool, Optional[dict[str, Any]], Optional[str]]:
        provider = stage_data.get("provider")
        request = stage_data.get("provider_request")

        if not provider or not request:
            return False, None, "Provider or request not initialized"

        response = await provider.execute(request)
        provider_responses.append(response)

        if not response.success:
            return False, None, response.error or "LLM execution failed"

        parser = ResponseParser()
        parsed, parse_error = parser.parse_json(response.content)
        if parse_error:
            return False, None, f"Output parsing failed: {parse_error}"

        stage_data["raw_response"] = response.content
        stage_data["parsed_response"] = parsed

        return True, parsed, None

    async def _stage_fallback_handling(
        self, agent_input: AgentInput, stage_data: dict[str, Any],
    ) -> dict[str, Any]:
        error = stage_data.get("execution_error", "Unknown error")
        original_kwargs = agent_input.metadata.get("template_kwargs", {})
        return fallback_generator.generate_fallback_output(
            agent_type=self._agent.name,
            original_kwargs=original_kwargs,
            error=error,
        )

    async def _stage_schema_validation(
        self, agent_input: AgentInput, stage_data: dict[str, Any],
    ) -> None:
        output = stage_data.get("output")
        if output:
            validation = await self._agent._validate_output(output, agent_input)
            if not validation.valid:
                raise ValueError(
                    f"Output schema validation failed: "
                    f"{'; '.join(validation.errors)}"
                )
            stage_data["schema_validation"] = validation

    async def _stage_telemetry_capture(
        self, agent_input: AgentInput, stage_data: dict[str, Any],
    ) -> None:
        token_usage = stage_data.get("token_usage", TokenUsage())
        telemetry_collector.update_token_usage(
            telemetry_collector.create_telemetry(
                agent_name=self._agent.name,
                correlation_id=agent_input.correlation_id,
                workflow_id=agent_input.workflow_id,
            ),
            token_usage,
        )

    async def _stage_event_emission(
        self, agent_input: AgentInput, stage_data: dict[str, Any],
    ) -> None:
        pass

    async def _on_pipeline_retry(self, attempt: int, error: str) -> None:
        logger.info(
            "Pipeline retry %d for %s: %s",
            attempt, self._agent.name, error,
        )

    def _aggregate_tokens(
        self, responses: list[ProviderResponse],
    ) -> TokenUsage:
        total = TokenUsage()
        for resp in responses:
            total.prompt_tokens += resp.token_usage.prompt_tokens
            total.completion_tokens += resp.token_usage.completion_tokens
            total.total_tokens += resp.token_usage.total_tokens
            if resp.provider and not total.provider:
                total.provider = resp.provider
            if resp.model and not total.model:
                total.model = resp.model
        return total

    def _compute_total_latency(self, telemetry: Any) -> float:
        if telemetry.started_at and telemetry.completed_at:
            start = datetime.fromisoformat(telemetry.started_at)
            end = datetime.fromisoformat(telemetry.completed_at)
            return (end - start).total_seconds() * 1000
        return sum(self._stage_timings.values())
