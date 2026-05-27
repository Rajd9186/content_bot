from __future__ import annotations

import json
import re

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.validator import ValidatorInput
from app.schemas.agent_outputs.validator import ValidatorOutput


VALIDATOR_SYSTEM_PROMPT = """You are a content quality validator.

Analyze markdown content for quality, completeness, structure, and citation health.

Return ONLY valid JSON with this exact structure:
{
  "is_valid": false,
  "errors": ["Error description"],
  "warnings": ["Warning description"],
  "word_count": 1500,
  "citation_count": 5,
  "missing_sections": ["Conclusion"],
  "quality_score": 0.75,
  "hallucination_risk": 0.1,
  "completeness_score": 0.8
}

Rules:
- is_valid: true only if no errors and quality_score >= 0.6
- quality_score: 0.0 to 1.0 (content quality based on structure, depth, citations)
- hallucination_risk: 0.0 to 1.0 (likelihood of unsubstantiated claims)
- completeness_score: 0.0 to 1.0 (how well all required sections are covered)
- Return ONLY valid JSON"""


class ValidatorAgent(BaseAgent[ValidatorInput, ValidatorOutput]):
    def system_prompt(self) -> str:
        return VALIDATOR_SYSTEM_PROMPT

    def parse_response(self, response: str, input_data: ValidatorInput) -> ValidatorOutput:
        try:
            data = json.loads(response)
            return ValidatorOutput(
                is_valid=bool(data.get("is_valid", False)),
                errors=data.get("errors", []),
                warnings=data.get("warnings", []),
                word_count=int(data.get("word_count", 0)),
                citation_count=int(data.get("citation_count", 0)),
                missing_sections=data.get("missing_sections", []),
                quality_score=min(1.0, max(0.0, float(data.get("quality_score", 0.0)))),
                hallucination_risk=min(1.0, max(0.0, float(data.get("hallucination_risk", 0.0)))),
                completeness_score=min(1.0, max(0.0, float(data.get("completeness_score", 0.0)))),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._fallback(input_data)

    def _fallback(self, input_data: ValidatorInput) -> ValidatorOutput:
        word_count = len(input_data.markdown.split())
        citation_count = len(input_data.citations)
        errors = []
        warnings = []

        if word_count < input_data.min_word_count:
            errors.append(f"Word count ({word_count}) below minimum ({input_data.min_word_count})")

        if not input_data.markdown.strip():
            errors.append("Content is empty")

        missing = [s for s in input_data.required_sections if s.lower() not in input_data.markdown.lower()]
        quality = min(1.0, max(0.0, (word_count / max(input_data.min_word_count, 1)) * 0.4 + (min(citation_count, 10) / 10) * 0.3 + 0.3))

        return ValidatorOutput(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            word_count=word_count,
            citation_count=citation_count,
            missing_sections=missing,
            quality_score=quality,
            hallucination_risk=0.1,
            completeness_score=quality,
        )

    async def run(self, input_data: ValidatorInput) -> ValidatorOutput:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.user_prompt(input_data)},
        ]
        try:
            response = await self.call_llm(messages, temperature=0.2)
            return self.parse_response(response.content, input_data)
        except Exception as e:
            self.logger.warning("ValidatorAgent failed, using fallback: %s", e)
            return self._fallback(input_data)
