import json
from typing import Any

from app.agents.base import BaseAgent
from app.config import settings


class ResearchAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a research analyst for a verified content system.
Analyze the provided search results and extract high-quality evidence.

Return JSON with this structure:
{
  "sources": [
    {
      "url": "https://...",
      "domain": "example.com",
      "title": "Article Title",
      "snippet": "Relevant excerpt",
      "author": null,
      "relevance_score": 0.95,
      "key_findings": ["finding 1"],
      "evidence_snippets": ["evidence 1"]
    }
  ],
  "summary": "Brief research summary",
  "key_insights": ["insight 1"]
}

Rules:
- Preserve ALL source URLs and titles from the input
- Assign relevance scores 0.0-1.0
- Return ONLY valid JSON"""

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            result = json.loads(response)
            if result.get("sources"):
                return result
            return {"sources": [], "summary": "", "key_insights": []}
        except (json.JSONDecodeError, TypeError):
            return {"sources": [], "summary": "", "key_insights": []}

    def compute_trust_score(self, domain: str) -> float:
        return settings.domain_trust_scores.get(
            domain.lower(), settings.default_trust_score
        )

    def _algorithmic_analysis(self, sources: list[dict]) -> dict:
        insights = []
        findings_by_source = []

        for s in sources:
            snippet = s.get("snippet", "") or s.get("content", "") or ""
            domain = s.get("domain", "")
            title = s.get("title", "Untitled")

            sentences = [x.strip() for x in snippet.replace("? ", ". ").split(". ") if len(x.strip()) > 30]
            top_sentences = sentences[:3]

            findings_by_source.append({
                "url": s.get("url", ""),
                "domain": domain,
                "title": title,
                "snippet": snippet[:500],
                "trust_score": self.compute_trust_score(domain),
                "relevance_score": s.get("score", s.get("relevance_score", 0.7)),
                "key_findings": [s.strip() for s in top_sentences[:2]],
                "evidence_snippets": [s.strip() for s in top_sentences],
            })

            if top_sentences:
                insights.append(f"According to {domain}: {top_sentences[0][:120]}...")

        summary = f"Collected {len(findings_by_source)} sources from trusted domains. "
        if findings_by_source:
            top = findings_by_source[0]
            summary += f"Key evidence from {top['domain']} indicates that {top.get('evidence_snippets', ['relevant findings'])[0][:200]}."

        return {
            "sources": findings_by_source,
            "summary": summary,
            "key_insights": insights[:5],
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        raw_sources = kwargs.get("sources", kwargs.get("evidence_sources", []))
        if not raw_sources:
            return {"sources": [], "summary": "", "key_insights": []}

        try:
            result = await super().run(**kwargs)
            if result.get("sources"):
                self.logger.info(
                    "Research analysis completed via LLM",
                    extra={"sources": len(result.get("sources", []))},
                )
                return result
        except Exception as e:
            self.logger.warning("LLM research analysis failed, using algorithmic fallback", extra={"error": str(e)})

        self.logger.info("Using algorithmic research analysis", extra={"raw_sources": len(raw_sources)})
        return self._algorithmic_analysis(raw_sources)
