from __future__ import annotations

import json
import re

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.seo import SEOInput
from app.schemas.agent_outputs.seo import SEOOutput


SEO_SYSTEM_PROMPT = """You are an SEO optimization specialist.

Analyze the provided markdown content and improve its SEO metadata.

Return ONLY valid JSON with this exact structure:
{
  "meta_title": "Optimized Title | Brand",
  "meta_description": "Compelling 150-160 char description",
  "focus_keywords": ["primary", "secondary", "tertiary"],
  "seo_score": 0.85,
  "suggestions": ["Add H2 tags for subheadings", "Include keyword in first paragraph"],
  "optimized_markdown": "# Title\\n\\nFull optimized content..."
}

Rules:
- meta_title: max 60 characters
- meta_description: 150-160 characters
- seo_score: 0.0 to 1.0
- optimized_markdown: the content with SEO improvements applied
- Return ONLY valid JSON"""


class SEOAgent(BaseAgent[SEOInput, SEOOutput]):
    def system_prompt(self) -> str:
        return SEO_SYSTEM_PROMPT

    def parse_response(self, response: str, input_data: SEOInput) -> SEOOutput:
        try:
            data = json.loads(response)
            return SEOOutput(
                meta_title=data.get("meta_title", input_data.title),
                meta_description=data.get("meta_description", ""),
                focus_keywords=data.get("focus_keywords", input_data.seo_keywords),
                seo_score=min(1.0, max(0.0, float(data.get("seo_score", 0.0)))),
                suggestions=data.get("suggestions", []),
                optimized_markdown=data.get("optimized_markdown", input_data.markdown),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._fallback(input_data)

    def _fallback(self, input_data: SEOInput) -> SEOOutput:
        return SEOOutput(
            meta_title=input_data.title,
            meta_description=f"Article about {input_data.title}",
            focus_keywords=input_data.seo_keywords,
            seo_score=0.5,
            suggestions=["Consider adding more keywords"],
            optimized_markdown=input_data.markdown,
        )

    async def run(self, input_data: SEOInput) -> SEOOutput:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.user_prompt(input_data)},
        ]
        try:
            response = await self.call_llm(messages, temperature=0.2)
            return self.parse_response(response.content, input_data)
        except Exception as e:
            self.logger.warning("SEOAgent failed, using fallback: %s", e)
            return self._fallback(input_data)
