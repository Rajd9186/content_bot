import json
from typing import Any

from app.agents.base import BaseAgent


class ContentWriterAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a senior content writer specializing in evidence-based verified content.

Return JSON with exactly this structure:
{
  "markdown": "# Title\\n\\nFull markdown content...",
  "summary": "2-3 sentence summary",
  "word_count": 1500,
  "citations": [
    {
      "id": 1,
      "text": "Claim text needing citation",
      "source_url": "https://...",
      "source_title": "Source title",
      "claim_id": "",
      "confidence": 0.95
    }
  ],
  "seo_metadata": {
    "meta_title": "SEO title",
    "meta_description": "SEO description",
    "focus_keywords": ["keyword1"]
  },
  "headings_used": ["Heading 1", "Heading 2"]
}

Rules - CRITICAL:
- ONLY use verified claims where confidence > 0.70
- EVERY factual assertion MUST have a corresponding citation
- Do NOT fabricate statistics, dates, or quotes
- Use proper markdown with H1, H2, H3
- Return ONLY valid JSON, no other text"""

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            result = json.loads(response)
            if result.get("markdown"):
                return result
            return self._default_content(
                result.get("title", "Untitled"),
                result.get("verified_claims", []),
                result.get("outline", {}),
                result.get("research_summary", ""),
            )
        except (json.JSONDecodeError, TypeError):
            return self._default_content("Untitled", [], {}, "")

    def _default_content(
        self,
        title: str,
        verified_claims: list[dict],
        outline: dict,
        research_summary: str,
    ) -> dict:
        sections_data = outline.get("sections", []) if outline else []

        lines = [f"# {title}", ""]

        if research_summary:
            lines.append(f"{research_summary}")
            lines.append("")

        citations = []
        citation_id = 0

        for i, section in enumerate(sections_data):
            heading = section.get("heading", f"Section {i + 1}")
            key_points = section.get("key_points", [])
            lines.append(f"## {heading}")
            lines.append("")

            section_claims = [
                c for c in verified_claims
                if any(kp.lower() in c.get("claim_text", "").lower() for kp in key_points)
            ] if verified_claims else []

            if section_claims:
                for claim in section_claims[:3]:
                    text = claim.get("claim_text", "")
                    conf = claim.get("confidence", 0)
                    source = claim.get("supporting_evidence", [""])[0] if claim.get("supporting_evidence") else ""
                    status = claim.get("status", "unverified")

                    if status == "verified" and conf >= 0.7:
                        citation_id += 1
                        citation_text = text.rstrip(".")
                        url = claim.get("source_url", "https://source.example.com")
                        lines.append(f"{citation_text} [^{citation_id}]")
                        lines.append("")
                        citations.append({
                            "id": citation_id,
                            "text": citation_text,
                            "source_url": url,
                            "source_title": f"Source {citation_id}",
                            "claim_id": claim.get("id", ""),
                            "confidence": conf,
                        })
                    elif conf >= 0.5:
                        lines.append(f"{text}")
                        lines.append("")
            else:
                for kp in key_points:
                    claim_for_point = next(
                        (c for c in verified_claims if c.get("confidence", 0) >= 0.7),
                        None,
                    )
                    if claim_for_point:
                        citation_id += 1
                        lines.append(f"{kp}. {claim_for_point['claim_text']} [^{citation_id}]")
                        lines.append("")
                        citations.append({
                            "id": citation_id,
                            "text": claim_for_point["claim_text"],
                            "source_url": claim_for_point.get("source_url", "https://source.example.com"),
                            "source_title": f"Source {citation_id}",
                            "claim_id": claim_for_point.get("id", ""),
                            "confidence": claim_for_point["confidence"],
                        })
                    else:
                        lines.append(f"{kp}.")
                        lines.append("")

        if citations:
            lines.append("## References")
            lines.append("")
            for cit in citations:
                lines.append(f"[^{cit['id']}]: {cit['source_title']} — {cit['source_url']}")
            lines.append("")

        markdown = "\n".join(lines)
        word_count = len(markdown.split())

        summary_sentences = []
        if research_summary:
            summary_sentences.append(research_summary[:150])
        if citations:
            summary_sentences.append(f"Supported by {len(citations)} citations from verified sources.")

        return {
            "markdown": markdown,
            "summary": " ".join(summary_sentences) if summary_sentences else f"Generated content about {title}.",
            "word_count": word_count,
            "citations": citations,
            "seo_metadata": {
                "meta_title": title[:60],
                "meta_description": (research_summary or title)[:160],
                "focus_keywords": outline.get("target_keywords", [title]),
            },
            "headings_used": [s.get("heading", f"Section {i+1}") for i, s in enumerate(sections_data)],
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        prompt_title = kwargs.get("title", "Untitled")
        claims = kwargs.get("verified_claims", [])
        outline = kwargs.get("outline", {})
        research_summary = kwargs.get("research_summary", "")

        try:
            result = await super().run(**kwargs)
            if result.get("markdown"):
                self.logger.info(
                    "Content written via LLM",
                    extra={"word_count": result.get("word_count"), "citations": len(result.get("citations", []))},
                )
                return result
        except Exception as e:
            self.logger.warning("LLM content writing failed, using template fallback", extra={"error": str(e)})

        self.logger.info(
            "Using template-based content generation",
            extra={"verified_claims": len(claims), "sections": len(outline.get("sections", []))},
        )
        return self._default_content(prompt_title, claims, outline, research_summary)
