import json
from typing import Any

from app.agents.base import BaseAgent


class TopicPlannerAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are an expert topic planner for a verified content generation system.

Return a JSON object with exactly this structure:
{
  "title": "The refined content title",
  "sections": [
    {
      "heading": "Section heading",
      "purpose": "What this section aims to achieve",
      "key_points": ["point 1", "point 2"],
      "research_queries": ["search query 1", "search query 2"]
    }
  ],
  "estimated_word_count": 1500,
  "target_keywords": ["keyword1", "keyword2"],
  "intended_structure": "analytical"
}

Rules:
- Create 4-7 sections
- Each section must have 2-4 key points and 1-3 research queries
- Research queries must be specific web search queries that return high-authority results
- Return ONLY valid JSON, no other text"""

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            result = json.loads(response)
            if result.get("sections"):
                return result
            return self._default_outline(result.get("title", "Untitled"))
        except (json.JSONDecodeError, TypeError):
            return self._default_outline("Untitled")

    def _default_outline(self, title: str) -> dict[str, Any]:
        return {
            "title": title,
            "sections": [
                {
                    "heading": "Overview and Context",
                    "purpose": "Provide background and scope of the topic",
                    "key_points": [
                        "Current state of the field",
                        "Why this topic matters now",
                        "Key stakeholders and affected parties",
                    ],
                    "research_queries": [
                        f"{title} current state overview 2026",
                        f"{title} importance and impact analysis",
                    ],
                },
                {
                    "heading": "Key Developments and Trends",
                    "purpose": "Examine major developments and emerging patterns",
                    "key_points": [
                        "Recent breakthroughs and milestones",
                        "Adoption and growth metrics",
                        "Leading organizations and contributors",
                    ],
                    "research_queries": [
                        f"{title} recent developments 2025 2026",
                        f"{title} adoption rates industry statistics",
                    ],
                },
                {
                    "heading": "Evidence and Data Analysis",
                    "purpose": "Present verified data and research findings",
                    "key_points": [
                        "Key statistics and metrics",
                        "Research findings from trusted sources",
                        "Comparative analysis of approaches",
                    ],
                    "research_queries": [
                        f"{title} research findings data analysis",
                        f"{title} statistics evidence based outcomes",
                    ],
                },
                {
                    "heading": "Applications and Impact",
                    "purpose": "Explore practical applications and real-world impact",
                    "key_points": [
                        "Real-world use cases and implementations",
                        "Measurable outcomes and benefits",
                        "Challenges and limitations",
                    ],
                    "research_queries": [
                        f"{title} real world applications case studies",
                        f"{title} impact outcomes results",
                    ],
                },
                {
                    "heading": "Future Outlook",
                    "purpose": "Discuss future directions and predictions",
                    "key_points": [
                        "Emerging trends and predictions",
                        "Growth projections and market forecasts",
                        "Preparation and strategic recommendations",
                    ],
                    "research_queries": [
                        f"{title} future trends predictions 2026 2030",
                        f"{title} market forecast growth projections",
                    ],
                },
            ],
            "estimated_word_count": 1500,
            "target_keywords": [title],
            "intended_structure": "analytical",
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        try:
            result = await super().run(**kwargs)
        except Exception as e:
            self.logger.error("Topic planner LLM failed, using fallback", extra={"error": str(e)})
            result = self._default_outline(kwargs.get("title", kwargs.get("topic", "Untitled")))

        sections = result.get("sections", [])
        if not sections:
            result = self._default_outline(result.get("title", kwargs.get("title", "Untitled")))
            sections = result.get("sections", [])

        self.logger.info(
            "Topic plan ready",
            extra={"sections_count": len(sections), "title": result.get("title")},
        )
        return result
