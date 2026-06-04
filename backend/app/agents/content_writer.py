import json
import asyncio
from typing import Any

from app.agents.base import BaseAgent


PLACEHOLDER_PATTERNS = [
    "untitled", "lorem ipsum", "coming soon", "to be written",
    "[placeholder", "your content here", "write here",
]


def _is_placeholder(text: str) -> bool:
    lower = text.lower().strip()
    for pat in PLACEHOLDER_PATTERNS:
        if pat in lower:
            return True
    return False


def _validate_draft(content: dict, kwargs: dict) -> dict:
    """Validate a generated draft. Returns dict with is_valid, errors, warnings."""
    markdown = content.get("markdown", "")
    title = content.get("title", kwargs.get("title", ""))
    citations = content.get("citations", [])
    word_count = content.get("word_count", 0) or len(markdown.split())
    headings = content.get("headings_used", [])

    errors = []
    warnings = []

    if not markdown or len(markdown.strip()) < 50:
        errors.append("markdown too short")
    if not title or _is_placeholder(title):
        errors.append(f"invalid title: '{title}'")
    if word_count < 50:
        errors.append(f"word count too low: {word_count}")
    if not citations:
        warnings.append("no citations provided")
    if _is_placeholder(markdown):
        errors.append("placeholder content detected")
    if headings and all(_is_placeholder(h) for h in headings):
        errors.append("all headings are placeholders")

    outline_sections = kwargs.get("outline", {}).get("sections", [])
    expected_headings = {s.get("heading", "").lower().strip() for s in outline_sections if s.get("heading")}
    if expected_headings:
        actual_headings = {h.lower().strip() for h in headings}
        missing = expected_headings - actual_headings
        if missing:
            warnings.append(f"missing expected sections: {', '.join(list(missing)[:3])}")

    is_valid = len(errors) == 0
    quality_score = 1.0 - (len(errors) * 0.25 + len(warnings) * 0.05)
    quality_score = max(0.0, min(1.0, quality_score))

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "quality_score": quality_score,
    }


class ContentWriterAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a senior content writer specializing in evidence-based verified content.

You will receive a writing task with a title, outline, verified claims, and research summary.

Your job is to write a complete, comprehensive article.

Return JSON with exactly this structure:
{
  "markdown": "# Title\\n\\nFull markdown content with multiple sections...",
  "summary": "2-3 sentence summary of the entire article",
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
    "focus_keywords": ["keyword1", "keyword2"]
  },
  "headings_used": ["Heading 1", "Heading 2", "Heading 3"]
}

Rules:
- Use the title as the H1 heading
- Follow the outline structure for sections and subsections
- Use verified claims as source material with citations
- Write substantive, specific content — no filler or placeholders
- Each section must have meaningful paragraphs
- Use proper markdown: H1 for title, H2 for sections, H3 for subsections
- Return ONLY valid JSON, no other text
- Minimum 300 words for a complete article"""

    def parse_response(self, response: str, **kwargs) -> dict[str, Any]:
        """Parse LLM response, falling back to trusted kwargs data."""
        kwargs_title = kwargs.get("title", "Untitled")
        kwargs_claims = kwargs.get("verified_claims", [])
        kwargs_outline = kwargs.get("outline", {})
        kwargs_summary = kwargs.get("research_summary", "")

        try:
            result = json.loads(response)
            if result.get("markdown"):
                result["title"] = result.get("title") or kwargs_title
                return result
            return self._default_content(kwargs_title, kwargs_claims, kwargs_outline, kwargs_summary)
        except (json.JSONDecodeError, TypeError):
            return self._default_content(kwargs_title, kwargs_claims, kwargs_outline, kwargs_summary)

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

        max_retries = 3
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                result = await super().run(**kwargs)
                result["title"] = result.get("title") or prompt_title

                validation = _validate_draft(result, kwargs)
                if validation["is_valid"]:
                    self.logger.info(
                        "Content written via LLM",
                        extra={
                            "word_count": result.get("word_count"),
                            "citations": len(result.get("citations", [])),
                            "quality_score": validation["quality_score"],
                            "attempt": attempt + 1,
                        },
                    )
                    return result

                last_error = "; ".join(validation["errors"])
                self.logger.warning(
                    "Draft validation failed, retrying",
                    extra={
                        "errors": validation["errors"],
                        "warnings": validation["warnings"],
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                    },
                )

                if attempt < max_retries:
                    enhanced_kwargs = dict(kwargs)
                    enhanced_kwargs["_retry_instructions"] = (
                        f"Previous attempt failed: {last_error}. "
                        "Write a complete article with substantive content, proper markdown formatting, "
                        "and meaningful sections. Avoid placeholders and generic text."
                    )
                    kwargs["_retry_instructions"] = enhanced_kwargs.get("_retry_instructions", "")
                    await asyncio.sleep(1.0 * (attempt + 1))

            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    "LLM content writing failed on attempt %d/%d",
                    attempt + 1, max_retries + 1,
                    extra={"error": str(e)},
                )
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                else:
                    break

        self.logger.info(
            "Using template-based content generation after %d attempts",
            attempt + 1,
            extra={"verified_claims": len(claims), "sections": len(outline.get("sections", [])), "last_error": last_error},
        )
        return self._default_content(prompt_title, claims, outline, research_summary)
