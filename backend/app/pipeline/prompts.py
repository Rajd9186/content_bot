from __future__ import annotations

from typing import Any

SYSTEM_PROMPTS: dict[str, str] = {
    "research": (
        "You are a senior research analyst. Your role is to conduct thorough research "
        "on the given topic and produce a structured, actionable research synthesis.\n\n"
        "OBJECTIVES:\n"
        "- Extract key insights, statistics, and expert perspectives\n"
        "- Identify trends, patterns, and contradictions\n"
        "- Assess source credibility and note conflicting viewpoints\n"
        "- Provide specific data points with context\n\n"
        "CONSTRAINTS:\n"
        "- Every finding must be substantive (2+ sentences)\n"
        "- Include specific numbers, dates, and named entities\n"
        "- Flag low-confidence or contradictory information\n"
        "- Never use placeholder text or generic statements\n\n"
        "OUTPUT FORMAT: Valid JSON with keys: summary, key_points, statistics, "
        "citations, entities, risks, outline_suggestions, gaps, contradictions, vlog_links"
    ),
    "planner": (
        "You are an expert content strategist. Your role is to create a detailed, "
        "actionable content plan based on research findings.\n\n"
        "OBJECTIVES:\n"
        "- Define content goals and target audience fit\n"
        "- Create structured outline with sections and subsections\n"
        "- Identify key themes and research integration points\n"
        "- Specify success criteria and quality benchmarks\n\n"
        "CONSTRAINTS:\n"
        "- Every section must have a clear purpose and key points (3-5)\n"
        "- Include research questions for each section\n"
        "- Define measurable success criteria\n"
        "- Never produce vague or generic plans\n\n"
        "OUTPUT FORMAT: Valid JSON with keys: title, sections, goals, "
        "target_audience, key_themes, research_questions, success_criteria, "
        "estimated_word_count"
    ),
    "writer": (
        "You are an expert content writer specializing in authoritative, "
        "engaging long-form content.\n\n"
        "OBJECTIVES:\n"
        "- Produce publication-ready content (800+ words)\n"
        "- Integrate research findings naturally into the narrative\n"
        "- Use proper markdown formatting with heading hierarchy\n"
        "- Maintain consistent tone and voice throughout\n\n"
        "CONSTRAINTS:\n"
        "- Every factual claim must be supported by research\n"
        "- Never use placeholder text or template variables\n"
        "- Produce complete sentences and paragraphs, not outlines\n"
        "- Minimum 800 words for standard articles\n"
        "- Include inline citations where research supports claims\n\n"
        "OUTPUT FORMAT: Valid JSON with keys: content (markdown string), "
        "title, word_count, sections_written, citations_used"
    ),
    "seo": (
        "You are an SEO optimization specialist. Your role is to optimize content "
        "for search engines while maintaining readability.\n\n"
        "OBJECTIVES:\n"
        "- Identify primary and secondary keywords\n"
        "- Optimize headings, meta description, and URL slug\n"
        "- Suggest internal and external linking opportunities\n"
        "- Ensure keyword density without keyword stuffing\n\n"
        "CONSTRAINTS:\n"
        "- Never sacrifice readability for keyword placement\n"
        "- All suggestions must be specific and actionable\n"
        "- Include search intent analysis\n"
        "- Never recommend black-hat SEO techniques\n\n"
        "OUTPUT FORMAT: Valid JSON with keys: title, meta_description, "
        "url_slug, primary_keywords, secondary_keywords, heading_suggestions, "
        "internal_links, external_links, readability_score, word_count_target, "
        "content (updated markdown)"
    ),
    "fact_checker": (
        "You are a rigorous fact-checking specialist. Your role is to verify all "
        "claims, statistics, and factual statements in the content.\n\n"
        "OBJECTIVES:\n"
        "- Verify every factual claim against provided research\n"
        "- Flag unsupported or exaggerated statements\n"
        "- Check statistical claims for accuracy and context\n"
        "- Verify proper citation of sources\n\n"
        "CONSTRAINTS:\n"
        "- Be specific about which claims are verified or unverified\n"
        "- Never guess or fabricate verification evidence\n"
        "- Flag ambiguous or misleading phrasing\n"
        "- Distinguish between verified, unverified, and disputed claims\n\n"
        "OUTPUT FORMAT: Valid JSON with keys: verified_claims, "
        "unverified_claims, disputed_claims, corrections, overall_assessment, "
        "confidence_score, content (updated markdown with corrections)"
    ),
    "compliance": (
        "You are a content compliance and risk officer. Your role is to review "
        "content for regulatory, legal, and brand safety issues.\n\n"
        "OBJECTIVES:\n"
        "- Check for regulatory compliance (GDPR, FTC, industry-specific)\n"
        "- Identify brand safety risks\n"
        "- Flag defamatory or misleading statements\n"
        "- Verify disclaimer and disclosure requirements\n\n"
        "CONSTRAINTS:\n"
        "- Be specific about which regulations apply\n"
        "- Provide clear remediation steps for each issue\n"
        "- Distinguish between critical and minor issues\n"
        "- Never approve content with unresolved critical issues\n\n"
        "OUTPUT FORMAT: Valid JSON with keys: compliance_status, "
        "issues (list of {severity, category, description, remediation}), "
        "disclaimers_needed, brand_safety_score, regulatory_checks, "
        "overall_verdict, content (updated markdown)"
    ),
    "finalizer": (
        "You are a content publishing specialist. Your role is to prepare "
        "the final content for publication.\n\n"
        "OBJECTIVES:\n"
        "- Apply all corrections from fact-checking and compliance\n"
        "- Format content for publication platform\n"
        "- Generate final metadata and summary\n"
        "- Ensure all sections are complete and polished\n\n"
        "CONSTRAINTS:\n"
        "- No placeholder content or incomplete sections\n"
        "- All citations must be properly formatted\n"
        "- SEO metadata must be included\n"
        "- Content must be publication-ready\n\n"
        "OUTPUT FORMAT: Valid JSON with keys: final_content, title, "
        "excerpt, word_count, reading_time_minutes, metadata, "
        "citations_list, change_log"
    ),
}


def build_system_prompt(agent_type: str) -> str:
    return SYSTEM_PROMPTS.get(
        agent_type,
        "You are a helpful AI assistant. Produce valid JSON output.",
    )


def build_research_prompt(state: dict[str, Any]) -> str:
    topic = state.get("topic", "Unknown topic")
    audience = state.get("audience", "general")
    goals = state.get("goals", "")
    memory_context = state.get("memory_context", "")
    pinned = state.get("pinned_memories", 0)
    relevant = state.get("relevant_memories", 0)
    memory_section = ""
    if memory_context:
        memory_section = f"\n### Project Knowledge Context\n{memory_context}\n\n"
    return (
        f"## Research Request\n\n"
        f"### Topic\n{topic}\n\n"
        f"### Target Audience\n{audience}\n\n"
        f"### Content Goals\n{goals}\n\n"
        f"{memory_section}"
        f"### Instructions\n"
        f"Conduct thorough research on this topic. For each finding:\n"
        f"- Write a substantive analysis (minimum 2-3 sentences)\n"
        f"- Include specific data points, dates, statistics\n"
        f"- Identify and include relevant vlog or video links (YouTube, etc.) in the vlog_links field\n"
        f"- Note source credibility and confidence level\n"
        f"- Identify gaps, contradictions, or areas needing more research\n\n"
        f"Produce ONLY valid JSON matching the expected schema. "
        f"Do not include any text outside the JSON block."
    )


def build_planner_prompt(state: dict[str, Any]) -> str:
    topic = state.get("topic", "Unknown topic")
    research = state.get("research_data", {})
    summary = research.get("summary", "No research available")
    key_points = research.get("key_points", [])
    points_list = key_points if isinstance(key_points, list) else []
    points_str = "\n".join(f"- {p}" for p in points_list[:10])
    return (
        f"## Content Planning Request\n\n"
        f"### Topic\n{topic}\n\n"
        f"### Research Summary\n{summary}\n\n"
        f"### Key Research Points\n{points_str}\n\n"
        f"### Instructions\n"
        f"Create a comprehensive content plan based on the research. "
        f"Define clear sections, target audience analysis, key themes, "
        f"and research directions.\n\n"
        f"Produce ONLY valid JSON matching the expected schema."
    )


def build_writer_prompt(state: dict[str, Any]) -> str:
    topic = state.get("topic", "Unknown topic")
    audience = state.get("audience", "general")
    tone = state.get("tone", "professional")
    research = state.get("research_data", {})
    plan = state.get("plan", {})
    outline = state.get("outline", {})

    research_summary = research.get("summary", "")
    key_points = research.get("key_points", [])
    statistics = research.get("statistics", [])

    sections = outline.get("sections", plan.get("sections", []))
    sections_str = ""
    for s in sections:
        if isinstance(s, dict):
            sections_str += f"\n### {s.get('title', 'Section')}\n"
            for kp in s.get("key_points", []):
                sections_str += f"- {kp}\n"

    stats_list = statistics if isinstance(statistics, list) else []
    points_list = key_points if isinstance(key_points, list) else []
    stats_str = "\n".join(f"- {s}" for s in stats_list[:5])
    points_str = "\n".join(f"- {p}" for p in points_list[:10])

    return (
        f"## Writing Assignment\n\n"
        f"### Title\n{topic}\n\n"
        f"### Target Audience\n{audience}\n\n"
        f"### Tone\n{tone}\n\n"
        f"### Research Context\n{research_summary}\n\n"
        f"### Key Findings to Include\n{points_str}\n\n"
        f"### Key Statistics\n{stats_str}\n\n"
        f"### Outline to Follow\n{sections_str}\n\n"
        f"### Instructions\n"
        f"Write complete, publication-ready content. Integrate research "
        f"findings naturally. Use proper markdown formatting. Minimum 800 words.\n\n"
        f"Produce ONLY valid JSON matching the expected schema."
    )


def build_seo_prompt(state: dict[str, Any]) -> str:
    content = state.get("draft_content", "")
    topic = state.get("topic", "")
    return (
        f"## SEO Optimization Request\n\n"
        f"### Topic\n{topic}\n\n"
        f"### Content to Optimize\n```markdown\n{content[:3000]}\n```\n\n"
        f"### Instructions\n"
        f"Optimize this content for search engines. Identify primary and "
        f"secondary keywords. Suggest heading improvements, meta description, "
        f"and URL slug. Improve keyword placement while maintaining readability.\n\n"
        f"Return the OPTIMIZED content as part of the JSON response.\n\n"
        f"Produce ONLY valid JSON matching the expected schema."
    )


def build_fact_check_prompt(state: dict[str, Any]) -> str:
    content = state.get("draft_content", "")
    research = state.get("research_data", {})
    research_summary = research.get("summary", "")
    citations = research.get("citations", [])
    citations_str = "\n".join(f"- {c}" for c in citations[:20])
    return (
        f"## Fact-Checking Request\n\n"
        f"### Content to Verify\n```markdown\n{content[:4000]}\n```\n\n"
        f"### Available Research Context\n{research_summary}\n\n"
        f"### Available Citations\n{citations_str}\n\n"
        f"### Instructions\n"
        f"Verify all factual claims in the content against the provided research. "
        f"Flag unsupported claims, exaggerated statements, and missing citations. "
        f"Provide specific corrections for each issue found.\n\n"
        f"Return the CORRECTED content as part of the JSON response.\n\n"
        f"Produce ONLY valid JSON matching the expected schema."
    )


def build_compliance_prompt(state: dict[str, Any]) -> str:
    content = state.get("draft_content", "")
    topic = state.get("topic", "")
    return (
        f"## Compliance Review Request\n\n"
        f"### Topic\n{topic}\n\n"
        f"### Content to Review\n```markdown\n{content[:4000]}\n```\n\n"
        f"### Instructions\n"
        f"Review this content for regulatory compliance, brand safety, "
        f"and legal issues. Check for:\n"
        f"- Defamatory or misleading statements\n"
        f"- Regulatory compliance requirements\n"
        f"- Brand safety risks\n"
        f"- Disclaimer and disclosure needs\n"
        f"- Industry-specific regulations\n\n"
        f"Return the CORRECTED content with all issues resolved.\n\n"
        f"Produce ONLY valid JSON matching the expected schema."
    )


def build_finalizer_prompt(state: dict[str, Any]) -> str:
    content = state.get("draft_content", "")
    seo = state.get("seo_metadata", {})
    fact_check = state.get("fact_check_results", {})
    compliance = state.get("compliance_results", {})
    topic = state.get("topic", "")
    return (
        f"## Final Content Assembly\n\n"
        f"### Title\n{topic}\n\n"
        f"### Final Content\n```markdown\n{content}\n```\n\n"
        f"### SEO Metadata\n{seo}\n\n"
        f"### Fact-Check Results\n{fact_check}\n\n"
        f"### Compliance Results\n{compliance}\n\n"
        f"### Instructions\n"
        f"Apply all corrections from fact-checking and compliance reviews. "
        f"Format the content for publication. Generate final metadata including "
        f"excerpt, word count, and reading time. Ensure the final output is "
        f"polished and publication-ready.\n\n"
        f"Produce ONLY valid JSON matching the expected schema."
    )


PROMPT_BUILDERS: dict[str, callable] = {
    "research": build_research_prompt,
    "planner": build_planner_prompt,
    "writer": build_writer_prompt,
    "seo": build_seo_prompt,
    "fact_checker": build_fact_check_prompt,
    "compliance": build_compliance_prompt,
    "finalizer": build_finalizer_prompt,
}


def build_user_prompt(agent_type: str, state: dict[str, Any]) -> str:
    builder = PROMPT_BUILDERS.get(agent_type)
    if builder:
        return builder(state)
    return f"Process the following: {state.get('topic', 'No topic provided')}"
