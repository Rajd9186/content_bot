from app.agents.base import BaseAgent
from app.agents.topic_planner import TopicPlannerAgent


class TaskPlannerAgent(TopicPlannerAgent):
    def system_prompt(self) -> str:
        return """You are a task planning specialist for a multi-agent research system.
Analyze the user's topic and decompose it into research tasks.

Return JSON with this structure:
{
  "title": "The content title",
  "sections": [
    {
      "heading": "Section Title",
      "purpose": "Why this section matters",
      "key_points": ["point 1", "point 2", "point 3"],
      "research_queries": ["search query 1", "search query 2"]
    }
  ],
  "research_tasks": [
    {
      "agent_type": "news|academic|financial|government",
      "query": "specific search query",
      "rationale": "Why this task exists"
    }
  ],
  "estimated_word_count": 1500,
  "target_keywords": ["keyword1"],
  "intended_structure": "narrative|analytical|comparative|problem-solution"
}

Rules:
- Decompose the topic into 3-6 research tasks
- Assign each task to the most appropriate agent type
- News: current events, announcements, trends
- Academic: studies, papers, research findings
- Financial: markets, investments, economic data
- Government: policies, regulations, official data
- Return ONLY valid JSON"""

    def _default_plan(self, title: str) -> dict:
        default = self._default_outline(title)
        default["research_tasks"] = [
            {"agent_type": "news", "query": f"{title} latest developments 2026", "rationale": "Current state"},
            {"agent_type": "academic", "query": f"{title} research studies", "rationale": "Evidence base"},
            {"agent_type": "financial", "query": f"{title} market impact", "rationale": "Economic context"},
            {"agent_type": "government", "query": f"{title} policy regulation", "rationale": "Regulatory landscape"},
        ]
        return default

    async def run(self, **kwargs) -> dict:
        try:
            result = await super().run(**kwargs)
            if result.get("sections"):
                return result
        except Exception as e:
            self.logger.warning("Task planner LLM failed, using default", extra={"error": str(e)})
        return self._default_plan(kwargs.get("title", "Untitled"))
