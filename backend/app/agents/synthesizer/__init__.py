from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.synthesizer import SynthesizerInput
from app.schemas.agent_outputs.synthesizer import SynthesizerOutput


SYNTHESIZER_SYSTEM_PROMPT = """You are a research synthesis specialist.

Your role is to analyze research findings, identify key themes, detect gaps,
and produce a synthesized research summary that guides content creation.

Return ONLY valid JSON with this exact structure:
{
  "executive_summary": "Concise overview of all research findings",
  "key_findings": ["Finding 1", "Finding 2"],
  "research_gaps": ["Gap 1", "Gap 2"],
  "synthesized_outline": {
    "narrative_arc": "Recommended story structure",
    "section_priorities": [{"heading": "Section", "priority": "high"}]
  },
  "confidence_score": 0.85
}

Rules:
- key_findings: 5-15 distinct findings from the research
- research_gaps: areas where more information is needed
- confidence_score: 0.0 to 1.0 (overall research confidence)
- Return ONLY valid JSON"""


class SynthesizerAgent(BaseAgent[SynthesizerInput, SynthesizerOutput]):
    def system_prompt(self) -> str:
        return SYNTHESIZER_SYSTEM_PROMPT

    def parse_response(self, response: str, input_data: SynthesizerInput) -> SynthesizerOutput:
        try:
            data = json.loads(response)
            return SynthesizerOutput(
                executive_summary=data.get("executive_summary", ""),
                key_findings=data.get("key_findings", []),
                research_gaps=data.get("research_gaps", []),
                synthesized_outline=data.get("synthesized_outline", {}),
                confidence_score=min(1.0, max(0.0, float(data.get("confidence_score", 0.0)))),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._fallback(input_data)

    def _fallback(self, input_data: SynthesizerInput) -> SynthesizerOutput:
        rp = input_data.research_packet
        return SynthesizerOutput(
            executive_summary=rp.executive_summary or f"Research synthesis for {input_data.topic}.",
            key_findings=rp.key_findings[:10] if rp.key_findings else [f"Key findings about {input_data.topic}"],
            research_gaps=[],
            synthesized_outline=input_data.planner_outline,
            confidence_score=0.5,
        )

    async def run(self, input_data: SynthesizerInput) -> SynthesizerOutput:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.user_prompt(input_data)},
        ]
        try:
            response = await self.call_llm(messages, temperature=0.3)
            return self.parse_response(response.content, input_data)
        except Exception as e:
            self.logger.warning("SynthesizerAgent failed, using fallback: %s", e)
            return self._fallback(input_data)
