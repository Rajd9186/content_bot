from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.outline import OutlineInput
from app.schemas.agent_outputs.outline import OutlineOutput
from app.orchestration.retry_engine.retry_middleware import RetryConfig, async_retry


OUTLINE_SYSTEM_PROMPT = """You are a content outlining specialist.

Your role is to transform research findings and a planner outline into a
detailed section-by-section content outline with target keywords.

Return ONLY valid JSON with this exact structure:
{
  "sections": [
    {
      "heading": "Section Title",
      "key_points": ["Point 1", "Point 2"],
      "target_word_count": 300,
      "keywords": ["keyword1", "keyword2"]
    }
  ],
  "target_keywords": ["keyword1", "keyword2"],
  "suggested_structure": "problem-solution"
}

Rules:
- Create 4-8 detailed sections
- Each section must have 2-5 key points
- Return ONLY valid JSON"""


class OutlineAgent(BaseAgent[OutlineInput, OutlineOutput]):
    def __init__(self):
        super().__init__()
        self._retry_config = RetryConfig(max_retries=2)

    def system_prompt(self) -> str:
        return OUTLINE_SYSTEM_PROMPT

    def parse_response(self, response: str, input_data: OutlineInput) -> OutlineOutput:
        try:
            data = json.loads(response)
            sections = data.get("sections", [])
            if not sections:
                return self._fallback(input_data)
            return OutlineOutput(
                sections=sections,
                target_keywords=data.get("target_keywords", []),
                suggested_structure=data.get("suggested_structure", ""),
            )
        except (json.JSONDecodeError, ValueError):
            return self._fallback(input_data)

    def _fallback(self, input_data: OutlineInput) -> OutlineOutput:
        sections = input_data.planner_outline.get("sections", [])
        if sections:
            return OutlineOutput(
                sections=sections,
                target_keywords=[],
                suggested_structure=input_data.planner_outline.get("intended_structure", ""),
            )
        return OutlineOutput(
            sections=[{"heading": "Introduction", "key_points": [f"Overview of {input_data.topic}"], "target_word_count": 300}],
            target_keywords=[input_data.topic],
            suggested_structure="standard",
        )

    async def run(self, input_data: OutlineInput) -> OutlineOutput:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.user_prompt(input_data)},
        ]
        try:
            response = await self.call_llm(messages, temperature=0.3)
            return self.parse_response(response.content, input_data)
        except Exception as e:
            self.logger.warning("OutlineAgent failed, using fallback: %s", e)
            return self._fallback(input_data)
