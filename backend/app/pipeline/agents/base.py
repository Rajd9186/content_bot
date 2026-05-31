from __future__ import annotations

import json
import logging
import time
from abc import ABC
from datetime import UTC, datetime
from typing import Any

from app.agents.provider.base import ProviderRequest
from app.agents.provider.factory import ProviderFactory
from app.infrastructure.metrics.collector import metrics_collector
from app.pipeline.context_compressor import context_compressor
from app.pipeline.output_validator import agent_output_validator
from app.pipeline.prompts import build_system_prompt, build_user_prompt
from app.pipeline.router import provider_router
from app.pipeline.state import NodeResult, NodeStatus, PipelineState

logger = logging.getLogger(__name__)


class PipelineAgent(ABC):
    def __init__(
        self,
        agent_type: str,
        provider_name: str = "groq",
        model: str = "llama-3.3-70b-versatile",
    ) -> None:
        self.agent_type = agent_type
        self.provider_name = provider_name
        self.model = model
        self._provider_factory = ProviderFactory()

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        start_time = time.monotonic()
        node_result = NodeResult(
            node=self.agent_type,
            status=NodeStatus.RUNNING,
            started_at=datetime.now(UTC).isoformat(),
        )

        try:
            system_prompt = build_system_prompt(self.agent_type)
            state_dict = state.model_dump()
            provider_name_hint = self.provider_name
            compressed_state = context_compressor.compress_for_agent(
                self.agent_type, state_dict, provider=provider_name_hint,
                system_prompt=system_prompt,
            )
            user_prompt = build_user_prompt(self.agent_type, compressed_state)

            decision = await provider_router.route(
                self.agent_type, system_prompt, user_prompt, state_dict,
            )

            provider_name = provider_override or decision.provider
            model = model_override or decision.model

            provider = self._provider_factory.get_or_create(provider_name, model)

            # Record the action of starting the agent execution
            node_result.actions.append({
                "action": "agent_start",
                "timestamp": datetime.now(UTC).isoformat(),
                "details": f"Starting {self.agent_type} using {provider_name}/{model}"
            })

            request = ProviderRequest(
                model=model,
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.1,
                max_tokens=4000,
            )

            response = await provider.execute_with_retry(request, max_retries=2)

            # Record the LLM response action
            node_result.actions.append({
                "action": "llm_response",
                "timestamp": datetime.now(UTC).isoformat(),
                "details": "Received response from LLM provider",
                "success": response.success
            })

            if not response.success:
                fallback = await provider_router.get_fallback(
                    self.agent_type, provider_name, model,
                    response.error or "",
                )
                logger.info(
                    "Agent %s: %s failed, fallback to %s/%s: %s",
                    self.agent_type, model, fallback.provider,
                    fallback.model, fallback.routing_reason,
                )
                provider_name = fallback.provider
                model = fallback.model
                request.model = model
                provider = self._provider_factory.get_or_create(provider_name, model)
                response = await provider.execute_with_retry(request, max_retries=1)

            if not response.success:
                node_result.status = NodeStatus.FAILED
                node_result.error = response.error or "All routing attempts failed"
                node_result.completed_at = datetime.now(UTC).isoformat()
                node_result.latency_ms = (time.monotonic() - start_time) * 1000
                provider_router.release_premium()
                return node_result

            output = self._parse_response(response.content)
            node_result.output = output

            # Record action for successful parsing and validation
            node_result.actions.append({
                "action": "parse_output",
                "timestamp": datetime.now(UTC).isoformat(),
                "details": f"Successfully parsed {self.agent_type} output"
            })

            validation = agent_output_validator.validate(self.agent_type, output)
            if validation.warnings:
                logger.warning(
                    "Agent %s output warnings: %s",
                    self.agent_type, validation.warnings,
                )
            if not validation:
                logger.error(
                    "Agent %s output validation failed: %s",
                    self.agent_type, validation.errors,
                )
                metrics_collector.record_validation_failure(self.agent_type)
                node_result.status = NodeStatus.FAILED
                node_result.error = "; ".join(validation.errors)
                node_result.completed_at = datetime.now(UTC).isoformat()
                node_result.latency_ms = (time.monotonic() - start_time) * 1000
                provider_router.release_premium()
                return node_result

            node_result.status = NodeStatus.SUCCESS

            latency = (time.monotonic() - start_time) * 1000
            metrics_collector.record_agent_latency(
                self.agent_type, provider_name, latency,
            )

            if response.token_usage:
                tokens = response.token_usage.total_tokens
                node_result.tokens_used = tokens
                provider_router.record_usage(provider_name, tokens)
                metrics_collector.record_agent_tokens(
                    self.agent_type, provider_name, tokens,
                )

        except Exception as e:
            logger.exception(
                "Agent %s failed: %s", self.agent_type, str(e)
            )
            node_result.status = NodeStatus.FAILED
            node_result.error = str(e)

        node_result.completed_at = datetime.now(UTC).isoformat()
        node_result.latency_ms = (time.monotonic() - start_time) * 1000
        provider_router.release_premium()
        return node_result

    def _parse_response(self, content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_content": content, "parse_error": "Could not parse as JSON"}
