from __future__ import annotations

import json
from typing import Any

from app.schemas.agent_inputs.planner import PlannerInput


def build_planner_system_prompt() -> str:
    return """You are a research and content planning specialist.

Your role is to analyze a writing topic and produce:
1. A structured outline with sections
2. Research queries that will gather evidence for each section
3. Target keywords for SEO

Return ONLY valid JSON with this exact structure:
{
  "outline": {
    "sections": [
      {
        "heading": "Section Title",
        "key_points": ["Point 1", "Point 2"],
        "research_queries": ["search query 1", "search query 2"],
        "word_count_target": 300
      }
    ],
    "intended_structure": "problem-solution",
    "estimated_total_words": 1500
  },
  "target_keywords": ["keyword1", "keyword2", "keyword3"],
  "suggested_sources": ["source type 1", "source type 2"]
}

Rules:
- Each section must have 2-5 key points and 1-3 research queries
- Research queries should be specific, searchable phrases
- Cover all aspects of the topic comprehensively
- Return ONLY valid JSON"""


def build_planner_user_prompt(input_data: PlannerInput) -> str:
    parts = [f"# Planning Task: {input_data.topic}", ""]
    parts.append("## Project Details")
    parts.append(f"Content Type: {input_data.content_type}")
    parts.append(f"Tone: {input_data.tone}")
    parts.append(f"Target Audience: {input_data.target_audience}")

    if input_data.title:
        parts.append(f"Title: {input_data.title}")
    if input_data.points_to_cover:
        parts.append(f"\nPoints to Cover:")
        for p in input_data.points_to_cover:
            parts.append(f"- {p}")
    if input_data.seo_keywords:
        parts.append(f"\nSEO Keywords: {', '.join(input_data.seo_keywords)}")

    return "\n".join(parts)
