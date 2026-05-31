from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

CHAR_TO_TOKEN_RATIO = 0.25

PROVIDER_TOKEN_LIMITS: dict[str, int] = {
    "groq": 8192,
    "openai": 128000,
    "anthropic": 200000,
    "nvidia": 4096,
    "ollama": 32768,
    "local": 4096,
}

AGENT_CONTEXT_BUDGETS: dict[str, float] = {
    "research": 0.6,
    "planner": 0.7,
    "writer": 0.75,
    "seo": 0.5,
    "fact_checker": 0.5,
    "compliance": 0.5,
    "finalizer": 0.6,
}

RESERVED_OUTPUT_TOKENS = 1500
MIN_SYSTEM_PROMPT_TOKENS = 300
MIN_USER_PROMPT_TOKENS = 100


class TokenBudgetManager:
    def __init__(self) -> None:
        self._compression_stats: dict[str, dict[str, int]] = {}

    def calculate_budget(
        self,
        agent_type: str,
        provider: str,
        system_prompt: str,
    ) -> int:
        provider_limit = PROVIDER_TOKEN_LIMITS.get(provider, 8192)
        budget_ratio = AGENT_CONTEXT_BUDGETS.get(agent_type, 0.6)
        system_tokens = max(1, int(len(system_prompt) * CHAR_TO_TOKEN_RATIO))
        available = int(provider_limit * budget_ratio)
        available = max(0, available - system_tokens - RESERVED_OUTPUT_TOKENS)
        return max(MIN_USER_PROMPT_TOKENS, available)

    def record_compression(
        self,
        agent_type: str,
        original_tokens: int,
        compressed_tokens: int,
    ) -> None:
        self._compression_stats[agent_type] = {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": (
                round(compressed_tokens / original_tokens, 2)
                if original_tokens > 0
                else 0
            ),
        }

    @property
    def compression_stats(self) -> dict[str, dict[str, int]]:
        return dict(self._compression_stats)


class ContextCompressor:
    def __init__(self, budget_manager: TokenBudgetManager) -> None:
        self._budget_manager = budget_manager

    def compress_for_agent(
        self,
        agent_type: str,
        state: dict[str, Any],
        provider: str = "groq",
        system_prompt: str = "",
    ) -> dict[str, Any]:
        budget = self._budget_manager.calculate_budget(
            agent_type, provider, system_prompt,
        )
        compressed = self._select_context(agent_type, state)
        compressed_str = self._dict_to_text(compressed)
        current_tokens = max(1, int(len(compressed_str) * CHAR_TO_TOKEN_RATIO))

        if current_tokens <= budget:
            self._budget_manager.record_compression(
                agent_type, current_tokens, current_tokens,
            )
            return compressed

        compressed = self._truncate_context(compressed, budget, agent_type)
        final_str = self._dict_to_text(compressed)
        final_tokens = max(1, int(len(final_str) * CHAR_TO_TOKEN_RATIO))
        self._budget_manager.record_compression(
            agent_type, current_tokens, final_tokens,
        )
        logger.info(
            "Context compressed for %s: %d -> %d tokens (budget: %d, provider: %s)",
            agent_type, current_tokens, final_tokens, budget, provider,
        )
        return compressed

    def _select_context(
        self, agent_type: str, state: dict[str, Any],
    ) -> dict[str, Any]:
        core = {
            "topic": state.get("topic", ""),
            "audience": state.get("audience", "general"),
            "tone": state.get("tone", "professional"),
            "goals": state.get("goals", ""),
        }
        research = state.get("research_data", {})
        plan = state.get("plan", {})
        outline = state.get("outline", {})
        draft = state.get("draft_content", "")
        seo = state.get("seo_metadata", {})
        fact_check = state.get("fact_check_results", {})
        compliance = state.get("compliance_results", {})

        if agent_type == "research":
            return core

        if agent_type == "planner":
            return {
                **core,
                "research_summary": research.get("summary", ""),
                "key_points": research.get("key_points", [])[:10],
                "statistics": research.get("statistics", [])[:5],
            }

        if agent_type == "writer":
            # More aggressive truncation for writer context
            truncated_key_points = [
                self._summarize_or_truncate_text(str(kp), 100)
                for kp in research.get("key_points", [])[:8]
            ]
            truncated_plan_sections = [
                self._summarize_or_truncate_text(str(sec), 150)
                for sec in plan.get("sections", [])[:8]
            ]
            truncated_outline_sections = [
                self._summarize_or_truncate_text(str(sec), 150)
                for sec in outline.get("sections", [])[:8]
            ]
            return {
                **core,
                "research_summary": self._summarize_or_truncate_text(
                    research.get("summary", ""), 1000,
                ),
                "key_points": truncated_key_points,
                "statistics": research.get("statistics", [])[:3],
                "plan_sections": truncated_plan_sections,
                "outline_sections": truncated_outline_sections,
            }

        if agent_type == "seo":
            return {
                "topic": core["topic"],
                "draft_content": draft[:3000],
            }

        if agent_type == "fact_checker":
            return {
                "topic": core["topic"],
                "draft_content": draft[:4000],
                "research_summary": research.get("summary", "")[:1000],
                "citations": research.get("citations", [])[:15],
            }

        if agent_type == "compliance":
            return {
                "topic": core["topic"],
                "draft_content": draft[:4000],
            }

        if agent_type == "finalizer":
            return {
                **core,
                "draft_content": draft[:6000],
                "seo_metadata": seo,
                "fact_check_results": fact_check,
                "compliance_results": compliance,
            }

        return core

    def _summarize_or_truncate_text(self, text: str, char_budget: int) -> str:
        if len(text) <= char_budget:
            return text
        return text[:char_budget] + "..."

    def _truncate_context(
        self,
        context: dict[str, Any],
        token_budget: int,
        agent_type: str,
    ) -> dict[str, Any]:
        char_budget = int(token_budget / CHAR_TO_TOKEN_RATIO)
        total_chars = len(self._dict_to_text(context))
        if total_chars <= char_budget:
            return context

        if agent_type == "writer":
            return self._truncate_writer_context(context, char_budget)

        ratio = char_budget / total_chars
        truncated: dict[str, Any] = {}
        for key, value in context.items():
            if isinstance(value, str):
                max_len = max(50, int(len(value) * ratio))
                truncated[key] = value[:max_len] + ("..." if len(value) > max_len else "")
            elif isinstance(value, list):
                max_items = max(1, int(len(value) * ratio))
                truncated[key] = value[:max_items]
            elif isinstance(value, dict):
                dict_str = str(value)
                max_len = max(50, int(len(dict_str) * ratio))
                truncated[key] = dict_str[:max_len] + "..."
            else:
                truncated[key] = value
        return truncated

    def _truncate_writer_context(
        self, context: dict[str, Any], char_budget: int,
    ) -> dict[str, Any]:
        truncated: dict[str, Any] = {}
        remaining_budget = char_budget

        for key in ["topic", "audience", "tone", "goals"]:
            if key in context and isinstance(context[key], str):
                val = context[key]
                truncated[key] = val
                remaining_budget -= len(val) + len(key) + 2

        plan_sections = context.get("plan_sections", [])
        outline_sections = context.get("outline_sections", [])
        combined_sections = plan_sections + outline_sections
        section_char_budget = int(remaining_budget * 0.4)
        truncated_sections = []
        if combined_sections:
            budget_per_section = section_char_budget // len(combined_sections)
            for section in combined_sections:
                section_str = str(section)
                if len(section_str) <= budget_per_section:
                    truncated_sections.append(section)
                    remaining_budget -= len(section_str)
                else:
                    truncated_val = self._summarize_or_truncate_text(section_str, budget_per_section)
                    truncated_sections.append(truncated_val)
                    remaining_budget -= len(truncated_val)
        truncated["plan_outline_sections"] = truncated_sections

        research_summary = context.get("research_summary", "")
        summary_char_budget = int(remaining_budget * 0.3)
        truncated["research_summary"] = self._summarize_or_truncate_text(
            research_summary, max(100, summary_char_budget),
        )
        remaining_budget -= len(truncated["research_summary"])

        key_points = context.get("key_points", [])
        key_point_char_budget = int(remaining_budget * 0.3)
        truncated_key_points = []
        if key_points:
            budget_per_kp = key_point_char_budget // len(key_points)
            for kp in key_points:
                kp_str = str(kp)
                truncated_val = self._summarize_or_truncate_text(kp_str, max(50, budget_per_kp))
                truncated_key_points.append(truncated_val)
                remaining_budget -= len(truncated_val)
        truncated["key_points"] = truncated_key_points

        for key, value in context.items():
            if key not in truncated:
                val_str = str(value)
                if remaining_budget > 100:
                    max_len = max(50, int(len(val_str) * (remaining_budget / (len(val_str) + 1))))
                    truncated_val = self._summarize_or_truncate_text(val_str, max_len)
                    truncated[key] = truncated_val
                    remaining_budget -= len(truncated_val)
                else:
                    truncated[key] = "... (truncated)"

        return truncated

    def _dict_to_text(self, d: dict[str, Any]) -> str:
        parts: list[str] = []
        for k, v in d.items():
            if isinstance(v, str):
                parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                for item in v:
                    parts.append(f"{k}: {item}")
            else:
                parts.append(f"{k}: {v}")
        return "\n".join(parts)


class PromptSizer:
    def estimate_tokens(self, text: str) -> int:
        return max(1, int(len(text) * CHAR_TO_TOKEN_RATIO))

    def estimate_state_tokens(self, state: dict[str, Any]) -> int:
        return self.estimate_tokens(str(state))

    def fits_budget(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: str,
        reserve_output: int = RESERVED_OUTPUT_TOKENS,
    ) -> bool:
        provider_limit = PROVIDER_TOKEN_LIMITS.get(provider, 8192)
        total = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_prompt)
        return total + reserve_output <= provider_limit


token_budget_manager = TokenBudgetManager()
context_compressor = ContextCompressor(token_budget_manager)
prompt_sizer = PromptSizer()
