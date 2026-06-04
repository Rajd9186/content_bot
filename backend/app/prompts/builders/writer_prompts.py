from __future__ import annotations

import json
from typing import Any

from app.schemas.agent_inputs.writer import WriterInput
from app.schemas.research_packet import ResearchPacket


def build_writer_system_prompt() -> str:
    return """You are a senior content writer specializing in evidence-based verified content.

You will receive a writing task with a title, outline, verified claims, and research packet.

Your job is to write a complete, comprehensive article following the outline structure.

RESPONSE FORMAT — Return ONLY valid JSON with this exact structure:
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
  "headings_used": ["Heading 1", "Heading 2"]
}

RULES:
- Use the title as the H1 heading
- Follow the outline structure — each outline section becomes an H2
- Use verified claims as source material with inline citations
- Write substantive, specific content — NO filler or placeholder text
- Each section must have at least 2 meaningful paragraphs
- Use proper markdown: H1 for title, H2 for sections, H3 for subsections
- Minimum 300 words for a complete article
- Return ONLY valid JSON — no other text before or after"""


def build_writer_user_prompt(input_data: WriterInput) -> str:
    parts = [f"# Writing Task: {input_data.title}", ""]

    instructions = []
    instructions.append(f"Write a comprehensive article titled '{input_data.title}'.")
    instructions.append(f"Target audience: {input_data.target_audience}.")
    instructions.append(f"Tone: {input_data.tone}.")
    instructions.append(f"Content type: {input_data.content_type}.")

    if input_data.seo_keywords:
        instructions.append(f"Naturally incorporate these SEO keywords: {', '.join(input_data.seo_keywords)}.")

    if input_data.outline:
        sections = input_data.outline.get("sections", [])
        instructions.append(f"Structure the article with {len(sections)} sections based on the outline provided.")
        instructions.append("Every section must contain substantive, specific content — not generic statements.")

    rp = input_data.research_packet
    if rp and rp.executive_summary:
        instructions.append(f"Research context: {rp.executive_summary}")
        if rp.key_findings:
            instructions.append(f"Key findings to incorporate: {len(rp.key_findings)} data points available.")
        if rp.statistics:
            stats = rp.statistics
            if isinstance(stats, dict) and stats.get("total_sources", 0) > 0:
                instructions.append(f"Based on {stats['total_sources']} sources from {stats.get('unique_domains', 0)} domains.")

    if input_data.verified_claims:
        instructions.append(f"Use the {len(input_data.verified_claims)} verified claims as source material.")
        instructions.append("Every factual assertion in the article MUST have a corresponding citation from these claims.")
    else:
        instructions.append("Write based on research summary and topic knowledge. No verified claims available.")

    instructions.append("Do NOT use placeholder text, generic headings, or filler content.")
    instructions.append("Return ONLY valid JSON matching the structure in the system prompt.")

    parts.append("## Instructions")
    for inst in instructions:
        parts.append(f"- {inst}")
    parts.append("")

    if rp and rp.executive_summary:
        parts.append("## Research Summary")
        parts.append(rp.executive_summary)
        parts.append("")

    if input_data.outline:
        parts.append("## Outline")
        parts.append(json.dumps(input_data.outline, indent=2))
        parts.append("")

    if input_data.verified_claims:
        parts.append("## Verified Claims")
        parts.append(json.dumps(input_data.verified_claims, indent=2))
        parts.append("")

    return "\n".join(parts)
