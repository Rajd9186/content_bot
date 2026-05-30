from __future__ import annotations

from typing import Any


class PromptBuilder:
    def __init__(self, agent_type: str) -> None:
        self._agent_type = agent_type
        self._kwargs: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> PromptBuilder:
        if value is not None:
            self._kwargs[key] = value
        return self

    def build(self) -> dict[str, Any]:
        return dict(self._kwargs)


class ResearchPromptBuilder(PromptBuilder):
    def __init__(self) -> None:
        super().__init__("researcher")

    def with_plan(self, plan: dict[str, Any]) -> ResearchPromptBuilder:
        plan_summary = self._format_plan(plan)
        self.set("plan_summary", plan_summary)
        research_qs = plan.get("research_questions", [])
        if isinstance(research_qs, list):
            q_text = "\n".join(f"- {q}" for q in research_qs if q)
            self.set("research_questions", q_text)
        elif isinstance(research_qs, str):
            self.set("research_questions", research_qs)
        return self

    def with_existing_knowledge(
        self, knowledge: str | None = None,
    ) -> ResearchPromptBuilder:
        self.set("existing_knowledge", knowledge or "No prior knowledge provided.")
        return self

    def _format_plan(self, plan: dict[str, Any]) -> str:
        title = plan.get("title", plan.get("topic", "Unknown Topic"))
        goals = plan.get("goals", plan.get("objectives", ""))
        audience = plan.get("audience", plan.get("target_audience", ""))
        themes = plan.get("themes", plan.get("key_themes", []))
        parts = [f"Title: {title}"]
        if goals:
            parts.append(f"Goals: {goals}")
        if audience:
            parts.append(f"Target Audience: {audience}")
        if themes:
            theme_list = ", ".join(themes) if isinstance(themes, list) else str(themes)
            parts.append(f"Key Themes: {theme_list}")
        return "\n".join(parts)


class WritingPromptBuilder(PromptBuilder):
    def __init__(self) -> None:
        super().__init__("writer")

    def with_title(self, title: str) -> WritingPromptBuilder:
        self.set("title", title or "Untitled Document")
        return self

    def with_outline(self, outline: Any) -> WritingPromptBuilder:
        if isinstance(outline, str):
            self.set("outline", outline)
        elif isinstance(outline, dict):
            self.set("outline", self._format_outline(outline))
        elif isinstance(outline, list):
            self.set("outline", self._format_outline_list(outline))
        else:
            self.set("outline", str(outline))
        return self

    def with_research_synthesis(self, synthesis: Any) -> WritingPromptBuilder:
        if isinstance(synthesis, str):
            self.set("research_synthesis", synthesis)
        elif isinstance(synthesis, dict):
            self.set("research_synthesis", self._format_synthesis(synthesis))
        else:
            self.set("research_synthesis", str(synthesis))
        return self

    def _format_outline(self, outline: dict[str, Any]) -> str:
        parts = []
        sections = outline.get("sections", [])
        for i, sec in enumerate(sections, 1):
            title = sec.get("title", f"Section {i}")
            parts.append(f"{i}. {title}")
            points = sec.get("key_points", sec.get("points", []))
            for pt in points:
                parts.append(f"   - {pt}")
            subs = sec.get("subsections", [])
            for j, sub in enumerate(subs, 1):
                sub_title = sub if isinstance(sub, str) else sub.get("title", f"Sub {j}")
                parts.append(f"   {i}.{j}. {sub_title}")
        return "\n".join(parts)

    def _format_outline_list(self, outline_list: list) -> str:
        parts = []
        for i, item in enumerate(outline_list, 1):
            if isinstance(item, dict):
                parts.append(f"{i}. {item.get('title', item.get('heading', 'Section'))}")
            else:
                parts.append(f"{i}. {item}")
        return "\n".join(parts)

    def _format_synthesis(self, synthesis: dict[str, Any]) -> str:
        parts = ["Research Synthesis:"]
        for key, value in synthesis.items():
            parts.append(f"\n{key.replace('_', ' ').title()}:")
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        parts.append(f"- {item.get('finding', item.get('insight', str(item)))}")
                    else:
                        parts.append(f"- {item}")
            elif isinstance(value, str):
                parts.append(f"  {value}")
        return "\n".join(parts)


class ValidationPromptBuilder(PromptBuilder):
    def __init__(self) -> None:
        super().__init__("validator")

    def with_brief(
        self, brief: dict[str, Any],
    ) -> ValidationPromptBuilder:
        parts = []
        for key, value in brief.items():
            if isinstance(value, str) and value:
                parts.append(f"{key.replace('_', ' ').title()}: {value}")
            elif isinstance(value, list) and value:
                parts.append(f"{key.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}")
        self.set("brief", "\n".join(parts) if parts else str(brief))
        return self

    def with_content(self, content: str) -> ValidationPromptBuilder:
        self.set("content", content)
        return self
