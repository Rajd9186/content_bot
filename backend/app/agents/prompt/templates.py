from __future__ import annotations

from typing import Any, Optional

SYSTEM_PROMPTS: dict[str, str] = {
    "planner": (
        "You are an expert content planning agent. Your role is to create a detailed, "
        "actionable content plan based on the user's requirements. "
        "You must produce a structured JSON plan with clear sections, "
        "target audience analysis, key themes, and research directions. "
        "Every plan must include: content goals, target audience, key themes (3-5), "
        "research questions, suggested structure, and success criteria."
    ),
    "researcher": (
        "You are a thorough research agent. Your role is to gather comprehensive, "
        "accurate, and relevant information on the given topic. "
        "You must provide detailed findings with sources, key statistics, expert quotes, "
        "and contrasting viewpoints. "
        "Each research finding must be substantive (minimum 2-3 sentences of analysis), "
        "NOT a one-line summary. Include specific data points, dates, and context."
    ),
    "synthesizer": (
        "You are a research synthesis agent. Your role is to merge multiple research "
        "findings into a coherent, structured synthesis. "
        "You must identify patterns, contradictions, gaps, and key insights. "
        "Organize the synthesis thematically, not by source. "
        "Each synthesized point must include contextual analysis (3+ sentences), "
        "not bullet-point summaries. Provide actionable research takeaways."
    ),
    "outliner": (
        "You are a content outlining agent. Your role is to create a detailed, "
        "hierarchical outline based on the research synthesis and content plan. "
        "Each section must have: a descriptive title, key points to cover (3-5), "
        "subsections with specific topics, research integration notes, and "
        "transition guidance to the next section. "
        "The outline must be comprehensive enough that a writer can produce "
        "a complete draft from it alone."
    ),
    "writer": (
        "You are an expert content writer. Your role is to produce engaging, "
        "well-researched, and structured content based on the provided outline "
        "and research synthesis. "
        "Write in a natural, authoritative tone. Use the research to support claims "
        "with specific evidence, data, and citations. "
        "Each section must flow naturally into the next. "
        "Produce complete, publication-ready content — NOT an outline, NOT notes, "
        "NOT placeholders like '# Untitled' or '[Content needed]'. "
        "Minimum 800 words for standard articles."
    ),
    "validator": (
        "You are a content validation agent. Your role is to rigorously review "
        "content for quality, accuracy, completeness, and adherence to guidelines. "
        "Check for: factual accuracy, logical flow, structural completeness, "
        "citation quality, tone consistency, readability, and SEO suitability. "
        "Provide a structured JSON report with: overall score (0-100), "
        "section-by-section feedback, issues found, recommendations, "
        "and a pass/fail determination."
    ),
    "seo": (
        "You are an SEO optimization agent. Your role is to analyze and enhance "
        "content for search engine visibility while maintaining natural readability. "
        "Provide: optimized meta title (50-60 chars), meta description (150-160 chars), "
        "keyword density analysis, heading structure review, internal linking "
        "suggestions, readability score, and specific improvement recommendations. "
        "Return a structured JSON report."
    ),
    "fact_checker": (
        "You are a fact-checking agent. Your role is to verify every factual claim "
        "in the content against known information. "
        "For each claim, provide: the claim text, verification status "
        "(verified / unverified / questionable / false), supporting evidence "
        "or contradiction, suggested correction if needed, and confidence level. "
        "Return a structured JSON fact-check report."
    ),
    "finalizer": (
        "You are a content finalization agent. Your role is to produce the final, "
        "polished version of the content incorporating all feedback from "
        "validation, SEO, and fact-checking stages. "
        "Apply all corrections, optimize formatting, ensure consistent tone, "
        "and verify the content meets all requirements. "
        "Output the COMPLETE finalized content — NOT a summary, NOT a diff, "
        "NOT placeholders. The output must be publication-ready."
    ),
}

DEVELOPER_PROMPTS: dict[str, str] = {
    "json_instruction": (
        "You MUST respond with valid JSON only, wrapped in ```json code blocks. "
        "Do NOT include any explanatory text outside the JSON block. "
        "The JSON must match the expected schema exactly."
    ),
    "markdown_instruction": (
        "You MUST respond with well-formatted markdown. "
        "Use proper heading hierarchy (H1 for title, H2 for sections, H3 for subsections). "
        "Use bold for emphasis, bullet points for lists, and inline code for technical terms. "
        "Include a table of contents for content longer than 500 words."
    ),
    "no_placeholders": (
        "CRITICAL: Never use placeholders like '[Content needed]', '# Untitled', "
        "'[Insert here]', 'TODO', or any similar filler. "
        "Every section must contain complete, substantive content. "
        "If information is unavailable, state what is known and move on."
    ),
    "citation_format": (
        "When citing sources, use inline citation format: [Source: author, year, title]. "
        "Every factual claim must be supported by at least one citation. "
        "Do not fabricate citations — only cite information present in the research provided."
    ),
    "research_integration": (
        "Integrate research findings naturally into the content. "
        "Do not list research as separate bullet points. "
        "Instead, weave findings into the narrative, using them to support arguments, "
        "provide examples, and add authority. "
        "Reference specific data points, statistics, and expert opinions from the research."
    ),
}

USER_PROMPT_TEMPLATES: dict[str, str] = {
    "planner": (
        "## Content Planning Request\n\n"
        "### Topic / Title\n{topic}\n\n"
        "### Content Goals\n{goals}\n\n"
        "### Target Audience\n{audience}\n\n"
        "### Additional Context\n{context}\n\n"
        "### Instructions\n"
        "Create a comprehensive content plan. Consider the target audience's "
        "knowledge level, interests, and pain points. Include specific research "
        "directions that will inform the content development. "
        "Produce ONLY valid JSON matching the expected schema. "
        "Do not include any text outside the JSON block."
    ),
    "researcher": (
        "## Research Request\n\n"
        "### Content Plan Summary\n{plan_summary}\n\n"
        "### Research Questions\n{research_questions}\n\n"
        "### Existing Knowledge\n{existing_knowledge}\n\n"
        "### Instructions\n"
        "Conduct thorough research on each question. For each finding:\n"
        "- Write a substantive analysis (minimum 3 sentences)\n"
        "- Include specific data points, dates, statistics\n"
        "- Note sources and credibility\n"
        "- Identify gaps or contradictions\n"
        "- Provide context for how this informs the content\n\n"
        "Avoid one-line summaries. Every finding must have depth and actionable insight."
    ),
    "synthesizer": (
        "## Research Synthesis Request\n\n"
        "### Research Findings\n{research_findings}\n\n"
        "### Content Plan\n{content_plan}\n\n"
        "### Instructions\n"
        "Synthesize the research findings into a coherent, structured overview. "
        "Organize thematically, identifying:\n"
        "- Key patterns and trends across sources\n"
        "- Contradictions or disagreements in the literature\n"
        "- Gaps that need further investigation\n"
        "- Actionable insights for content creation\n\n"
        "Each synthesized point must include contextual analysis (3+ sentences). "
        "Do NOT simply restate findings in bullet points."
    ),
    "outliner": (
        "## Content Outline Request\n\n"
        "### Research Synthesis\n{research_synthesis}\n\n"
        "### Content Plan\n{content_plan}\n\n"
        "### Instructions\n"
        "Create a detailed hierarchical outline. For each section:\n"
        "- Provide a clear, descriptive working title\n"
        "- List 3-5 key points to cover with research integration notes\n"
        "- Define subsection structure\n"
        "- Note which research findings support each section\n"
        "- Provide transition guidance to the next section\n\n"
        "The outline must be complete enough that a writer can produce "
        "a full draft from it alone."
    ),
    "writer": (
        "## Content Writing Request\n\n"
        "### Title\n{title}\n\n"
        "### Outline\n{outline}\n\n"
        "### Research Synthesis\n{research_synthesis}\n\n"
        "### Instructions\n"
        "Write a complete, publication-ready article based on the outline and research.\n\n"
        "Requirements:\n"
        "- Write complete narrative prose, not notes or bullet points\n"
        "- Integrate research findings naturally into the narrative\n"
        "- Use inline citations for all factual claims\n"
        "- Maintain consistent tone and voice throughout\n"
        "- Each section must be 200+ words of substantive content\n"
        "- Include transitional sentences between sections\n"
        "- Never use placeholders or filler text\n"
        "- The output must be the COMPLETE article, ready for publication"
    ),
    "validator": (
        "## Content Validation Request\n\n"
        "### Original Brief\n{brief}\n\n"
        "### Content to Validate\n{content}\n\n"
        "### Instructions\n"
        "Review the content against the original brief. Evaluate:\n"
        "1. Completeness — does it cover all required sections?\n"
        "2. Accuracy — are claims supported by research?\n"
        "3. Structure — does the flow make logical sense?\n"
        "4. Quality — is the writing clear and engaging?\n"
        "5. Citations — are sources properly referenced?\n\n"
        "Provide a structured JSON report with scores and specific feedback. "
        "Include a pass/fail determination."
    ),
    "seo": (
        "## SEO Optimization Request\n\n"
        "### Content\n{content}\n\n"
        "### Target Keywords\n{keywords}\n\n"
        "### Instructions\n"
        "Analyze and optimize the content for search engines. Provide a structured JSON "
        "report with: meta title, meta description, keyword analysis, heading review, "
        "readability score, and actionable recommendations. "
        "Do not suggest keyword stuffing — prioritize natural language."
    ),
    "fact_checker": (
        "## Fact-Checking Request\n\n"
        "### Research Sources\n{research_sources}\n\n"
        "### Content to Verify\n{content}\n\n"
        "### Instructions\n"
        "Verify every factual claim in the content. For each claim:\n"
        "- State the claim verbatim\n"
        "- Determine verification status: verified / unverified / questionable / false\n"
        "- Provide supporting evidence or contradiction from the research\n"
        "- Suggest corrections for unverified or false claims\n"
        "- Rate your confidence level (high / medium / low)\n\n"
        "Return a structured JSON fact-check report."
    ),
    "finalizer": (
        "## Content Finalization Request\n\n"
        "### Original Content\n{content}\n\n"
        "### Validation Feedback\n{validation_feedback}\n\n"
        "### SEO Feedback\n{seo_feedback}\n\n"
        "### Fact-Check Report\n{fact_check_report}\n\n"
        "### Instructions\n"
        "Produce the FINAL version of this content incorporating ALL feedback. "
        "Output the COMPLETE finalized content in markdown format. "
        "Do not output a summary, diff, or notes. "
        "The output must be the full, publication-ready content."
    ),
}


def get_system_prompt(agent_type: str) -> str:
    base = SYSTEM_PROMPTS.get(agent_type, "You are a helpful AI assistant.")
    dev_parts = [
        DEVELOPER_PROMPTS.get("no_placeholders", ""),
        DEVELOPER_PROMPTS.get("json_instruction", ""),
    ]
    if agent_type in ("writer", "finalizer"):
        dev_parts.append(DEVELOPER_PROMPTS.get("markdown_instruction", ""))
        dev_parts.append(DEVELOPER_PROMPTS.get("citation_format", ""))
        dev_parts.append(DEVELOPER_PROMPTS.get("research_integration", ""))
    return f"{base}\n\n{' '.join(dev_parts)}"


def get_user_prompt(agent_type: str, **kwargs: Any) -> str:
    template = USER_PROMPT_TEMPLATES.get(agent_type, "")
    if not template:
        return _build_fallback_prompt(agent_type, kwargs)
    return template.format(**kwargs)


def _build_fallback_prompt(agent_type: str, kwargs: dict[str, Any]) -> str:
    parts = [f"## {agent_type.replace('_', ' ').title()} Request\n"]
    for key, value in kwargs.items():
        if value is not None and value != "":
            label = key.replace("_", " ").title()
            val = str(value)
            if len(val) > 500:
                val = val[:500] + "..."
            parts.append(f"### {label}\n{val}\n")
    parts.append("\nProvide your complete response following the agent instructions.")
    return "\n".join(parts)
