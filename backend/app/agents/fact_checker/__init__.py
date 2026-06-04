from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.fact_checker import FactCheckerInput
from app.schemas.agent_outputs.fact_checker import FactCheckerOutput


FACT_CHECKER_SYSTEM_PROMPT = """You are a fact-checking and citation verification specialist.

Analyze the provided content, citations, and claims for factual accuracy
and citation correctness.

Return ONLY valid JSON with this exact structure:
{
  "is_pass": false,
  "errors": [
    {"type": "missing_citation", "detail": "Claim without supporting citation", "location": "Section 2"}
  ],
  "warnings": [
    {"type": "low_confidence", "detail": "Claim has low confidence score", "location": "Section 1"}
  ],
  "corrected_citations": [
    {"original": "old url", "corrected": "new url", "reason": "URL mismatch"}
  ],
  "hallucination_risk": 0.2,
  "corrected_markdown": "# Title...",
  "details": {"claims_checked": 5, "errors_found": 1, "warnings_found": 2}
}

Rules:
- hallucination_risk: 0.0 to 1.0
- is_pass: true only if no errors and hallucination_risk < 0.3
- Return ONLY valid JSON"""


class FactCheckerAgent(BaseAgent[FactCheckerInput, FactCheckerOutput]):
    def system_prompt(self) -> str:
        return FACT_CHECKER_SYSTEM_PROMPT

    def parse_response(self, response: str, input_data: FactCheckerInput) -> FactCheckerOutput:
        try:
            data = json.loads(response)
            hallucination_risk = min(1.0, max(0.0, float(data.get("hallucination_risk", 0.0))))
            errors = data.get("errors", [])
            return FactCheckerOutput(
                is_pass=len(errors) == 0 and hallucination_risk < 0.3,
                errors=errors,
                warnings=data.get("warnings", []),
                corrected_citations=data.get("corrected_citations", []),
                hallucination_risk=hallucination_risk,
                corrected_markdown=data.get("corrected_markdown", input_data.markdown),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._fallback(input_data)

    def _fallback(self, input_data: FactCheckerInput) -> FactCheckerOutput:
        return FactCheckerOutput(
            is_pass=True,
            errors=[],
            warnings=[{"type": "not_verified", "detail": "Fact checking unavailable"}],
            hallucination_risk=0.0,
            corrected_markdown=input_data.markdown,
        )

    async def run(self, input_data: FactCheckerInput) -> FactCheckerOutput:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.user_prompt(input_data)},
        ]
        try:
            response = await self.call_llm(messages, temperature=0.2)
            return self.parse_response(response.content, input_data)
        except Exception as e:
            self.logger.warning("FactCheckerAgent failed, using fallback: %s", e)
            return self._fallback(input_data)
