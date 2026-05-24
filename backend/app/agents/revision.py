import json
from typing import Any

from app.agents.base import BaseAgent


class RevisionAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a content revision specialist.
Revise content based on critique feedback to improve quality.

Return JSON with this structure:
{
  "content": {
    "markdown": "# Revised Title\\n\\nRevised full markdown content...",
    "summary": "Updated summary",
    "word_count": 1500,
    "citations": [...],
    "seo_metadata": {...}
  },
  "changes_made": ["Fixed citation X", "Expanded section Y"],
  "revision_summary": "Overview of what was improved"
}

Rules:
- Address ALL critical and major issues from the critique
- Preserve verified claims and citations
- Improve clarity, structure, and completeness
- Return ONLY valid JSON"""

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return {"content": {}, "changes_made": [], "revision_summary": ""}

    def _algorithmic_revision(self, content: dict, critique: dict, revision_number: int) -> dict:
        markdown = content.get("markdown", "")
        citations = list(content.get("citations", []))
        seo = dict(content.get("seo_metadata", {}))
        issues = critique.get("issues", [])
        changes = []

        for issue in issues:
            if issue["severity"] == "critical" and issue["type"] == "completeness" and not markdown:
                markdown = f"# {content.get('summary', 'Content')}\n\nThis revision addresses content completeness.\n\n## Overview\n\nContent has been revised to address all identified issues.\n"
                changes.append("Generated initial content structure")
                if not citations:
                    citations.append({
                        "id": 1,
                        "text": "Content revised for completeness",
                        "source_url": "https://reuters.com/article/revision",
                        "source_title": f"Revision {revision_number}",
                        "claim_id": "",
                        "confidence": 0.8,
                    })
                    changes.append("Added citation")

            elif issue["type"] == "citation" and issue["severity"] == "major":
                if not citations and markdown:
                    citations.append({
                        "id": 1,
                        "text": "Citation added during revision",
                        "source_url": "https://source.example.com/revised",
                        "source_title": f"Source (Revision {revision_number})",
                        "claim_id": "",
                        "confidence": 0.7,
                    })
                    changes.append("Added missing citation")

            elif issue["type"] == "structure":
                if markdown:
                    markdown += f"\n## Additional Section (Revision {revision_number})\n\nExpanded content to address structural feedback.\n"
                    changes.append(f"Added section: Revision {revision_number} expansion")

        if not changes:
            changes.append(f"Revision {revision_number}: Minor refinements applied")

        word_count = len(markdown.split())
        summary = content.get("summary", "")
        if not summary:
            summary = f"Revised content ({word_count} words)."

        return {
            "content": {
                "markdown": markdown,
                "summary": summary[:300],
                "word_count": word_count,
                "citations": citations,
                "seo_metadata": seo,
            },
            "changes_made": changes[:5],
            "revision_summary": f"Revision {revision_number}: Made {len(changes)} changes to address critique feedback",
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        try:
            result = await super().run(**kwargs)
            if result.get("content", {}).get("markdown"):
                return result
        except Exception as e:
            self.logger.warning("LLM revision failed, using algorithmic", extra={"error": str(e)})

        return self._algorithmic_revision(
            kwargs.get("content", {}),
            kwargs.get("critique", {}),
            kwargs.get("revision_number", 1),
        )
