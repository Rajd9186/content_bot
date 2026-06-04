import json
from typing import Any

from app.agents.base import BaseAgent


class CritiqueAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a content critique specialist.
Review generated content for quality, accuracy, and completeness.

Return JSON with this structure:
{
  "needs_revision": true,
  "issues": [
    {
      "type": "accuracy|completeness|clarity|citation|structure|tone",
      "severity": "critical|major|minor",
      "excerpt": "Relevant text excerpt",
      "explanation": "What's wrong",
      "suggestion": "How to fix it"
    }
  ],
  "strengths": ["What was done well"],
  "overall_score": 0.0-1.0,
  "summary": "Brief critique summary"
}

Rules:
- Check citation coverage (every claim needs one)
- Check factual consistency with verified claims
- Check structure and flow
- Check tone alignment
- Return ONLY valid JSON"""

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return {"needs_revision": False, "issues": [], "strengths": [], "overall_score": 0.7, "summary": ""}

    def _algorithmic_critique(self, content: dict, claims: list[dict], outline: dict) -> dict:
        issues = []
        strengths = []
        markdown = content.get("markdown", "")
        citations = content.get("citations", [])

        if not markdown:
            issues.append({
                "type": "completeness",
                "severity": "critical",
                "excerpt": "",
                "explanation": "No content generated",
                "suggestion": "Regenerate content",
            })
            return {
                "needs_revision": True,
                "issues": issues,
                "strengths": [],
                "overall_score": 0.0,
                "summary": "Content is empty, needs regeneration",
            }

        words = len(markdown.split())
        if words < 100:
            issues.append({
                "type": "completeness",
                "severity": "critical",
                "excerpt": markdown[:200],
                "explanation": f"Content too short ({words} words)",
                "suggestion": "Expand each section with more detail",
            })

        sections_in_content = [l for l in markdown.split("\n") if l.startswith("## ")]
        outline_sections = outline.get("sections", [])
        if len(sections_in_content) < len(outline_sections) // 2:
            issues.append({
                "type": "structure",
                "severity": "major",
                "excerpt": markdown[:200],
                "explanation": f"Only {len(sections_in_content)} sections found, expected ~{len(outline_sections)}",
                "suggestion": "Include all outline sections",
            })

        has_citations = bool(citations)
        if not has_citations and words > 100:
            issues.append({
                "type": "citation",
                "severity": "major",
                "excerpt": "",
                "explanation": "No citations found in content",
                "suggestion": "Add citations from verified claims",
            })

        if not issues:
            strengths.append("Content length is adequate")
            if has_citations:
                strengths.append(f"Contains {len(citations)} citations")
            if sections_in_content:
                strengths.append(f"Properly structured with {len(sections_in_content)} sections")

        score = 0.9
        for issue in issues:
            if issue["severity"] == "critical":
                score -= 0.3
            elif issue["severity"] == "major":
                score -= 0.15
            else:
                score -= 0.05
        score = max(0.0, min(1.0, score))

        return {
            "needs_revision": len(issues) > 0,
            "issues": issues[:5],
            "strengths": strengths[:3],
            "overall_score": round(score, 2),
            "summary": f"C critique found {len(issues)} issues, score: {score:.0%}",
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        content = kwargs.get("content", {})
        claims = kwargs.get("claims", [])
        outline = kwargs.get("outline", {})

        try:
            result = await super().run(**kwargs)
            if result.get("overall_score") is not None:
                return result
        except Exception as e:
            self.logger.warning("LLM critique failed, using algorithmic", extra={"error": str(e)})

        return self._algorithmic_critique(content, claims, outline)
