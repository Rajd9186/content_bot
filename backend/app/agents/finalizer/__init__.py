from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.finalizer import FinalizerInput
from app.schemas.agent_outputs.finalizer import FinalizerOutput


FINALIZER_SYSTEM_PROMPT = """You are a content finalization specialist.

Your role is to perform the final review pass: polish the markdown, ensure
metadata is complete, verify citations are properly formatted, and prepare
the content for publication.

Return ONLY valid JSON with this exact structure:
{
  "final_markdown": "The complete polished markdown content",
  "final_title": "Polished Title",
  "meta_title": "SEO Title | Brand",
  "meta_description": "150-160 character description",
  "focus_keywords": ["primary", "secondary"],
  "word_count": 1500,
  "citations": [{"id": 1, "text": "Citation text", "source_url": "https://..."}],
  "overall_quality": 0.88,
  "ready_for_publish": true
}

Rules:
- final_markdown: must be complete, no placeholders, no filler
- meta_title: max 60 characters
- meta_description: 150-160 characters
- overall_quality: 0.0 to 1.0
- ready_for_publish: true only if overall_quality >= 0.6
- Return ONLY valid JSON"""


class FinalizerAgent(BaseAgent[FinalizerInput, FinalizerOutput]):
    def system_prompt(self) -> str:
        return FINALIZER_SYSTEM_PROMPT

    def parse_response(self, response: str, input_data: FinalizerInput) -> FinalizerOutput:
        try:
            data = json.loads(response)
            return FinalizerOutput(
                final_markdown=data.get("final_markdown", input_data.markdown),
                final_title=data.get("final_title", input_data.title),
                meta_title=data.get("meta_title", input_data.meta_title or input_data.title),
                meta_description=data.get("meta_description", input_data.meta_description),
                focus_keywords=data.get("focus_keywords", input_data.focus_keywords),
                word_count=int(data.get("word_count", 0)) or len(data.get("final_markdown", input_data.markdown).split()),
                citations=data.get("citations", input_data.citations),
                overall_quality=min(1.0, max(0.0, float(data.get("overall_quality", 0.0)))),
                ready_for_publish=bool(data.get("ready_for_publish", False)),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._fallback(input_data)

    def _fallback(self, input_data: FinalizerInput) -> FinalizerOutput:
        word_count = len(input_data.markdown.split())
        overall = (input_data.quality_score + input_data.seo_score) / 2.0 if input_data.seo_score > 0 else input_data.quality_score
        return FinalizerOutput(
            final_markdown=input_data.markdown,
            final_title=input_data.title,
            meta_title=input_data.meta_title or input_data.title,
            meta_description=input_data.meta_description or f"Article about {input_data.title}",
            focus_keywords=input_data.focus_keywords,
            word_count=word_count,
            citations=input_data.citations,
            overall_quality=overall,
            ready_for_publish=overall >= 0.6 and input_data.fact_check_passed,
        )

    async def run(self, input_data: FinalizerInput) -> FinalizerOutput:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.user_prompt(input_data)},
        ]
        try:
            response = await self.call_llm(messages, temperature=0.2)
            return self.parse_response(response.content, input_data)
        except Exception as e:
            self.logger.warning("FinalizerAgent failed, using fallback: %s", e)
            return self._fallback(input_data)
