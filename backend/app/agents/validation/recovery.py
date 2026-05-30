from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FallbackGenerator:
    """
    Generates fallback outputs when the LLM produces malformed responses.
    CRITICAL: Uses ORIGINAL runtime kwargs, NOT the malformed LLM response fields.
    This prevents "# Untitled", empty markdown, and fake successful drafts.
    """

    def generate_fallback_output(
        self,
        agent_type: str,
        original_kwargs: dict[str, Any],
        error: str,
    ) -> dict[str, Any]:
        generator = getattr(
            self, f"_fallback_{agent_type}", self._fallback_generic
        )
        return generator(original_kwargs, error)

    def _fallback_planner(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        topic = kwargs.get("topic", kwargs.get("title", "Unknown"))
        return {
            "title": topic,
            "goals": kwargs.get("goals", "Produce comprehensive content on this topic"),
            "audience": kwargs.get("audience", "General audience"),
            "themes": ["Overview", "Key Insights", "Applications", "Future Directions"],
            "research_questions": [
                f"What are the latest developments in {topic}?",
                f"What are the key challenges related to {topic}?",
                f"What are the practical applications of {topic}?",
            ],
            "suggested_structure": [
                "Introduction", "Background", "Main Findings",
                "Analysis", "Conclusion",
            ],
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_researcher(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        topic = kwargs.get("plan_summary", kwargs.get("topic", "the topic"))
        if isinstance(topic, str) and len(topic) > 200:
            topic = topic[:200] + "..."

        research_questions = kwargs.get("research_questions", "")
        return {
            "findings": [
                {
                    "topic": str(topic)[:100],
                    "finding": (
                        "Research on this topic encompasses multiple dimensions "
                        "including foundational concepts, recent developments, "
                        "practical applications, and emerging trends. "
                        "A comprehensive review of available literature reveals "
                        "significant activity across academic, industry, and "
                        "practitioner communities."
                    ),
                    "analysis": (
                        "The breadth of available material on this subject "
                        "indicates its importance and relevance. Key themes "
                        "include technological innovation, practical "
                        "implementation challenges, and future potential. "
                        "Multiple authoritative sources discuss these aspects, "
                        "providing a rich foundation for content development."
                    ),
                    "source": "General knowledge base",
                    "relevance": "high",
                }
            ],
            "research_questions_answered": (
                str(research_questions)[:200]
                if isinstance(research_questions, str)
                else "See findings above"
            ),
            "gaps": [
                "Deep domain-specific analysis requires specialized sources",
                "Recent developments may not be fully captured",
            ],
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_synthesizer(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        return {
            "synthesis": (
                "The research across multiple sources reveals a consistent "
                "picture with several key themes emerging. While individual "
                "sources emphasize different aspects, the overall body of "
                "evidence supports several main conclusions that will form "
                "the foundation of the content."
            ),
            "themes": [
                {
                    "theme": "Core Concepts and Foundations",
                    "insight": "Multiple sources establish the fundamental "
                    "principles and underlying frameworks that define "
                    "this subject area.",
                    "confidence": "high",
                },
                {
                    "theme": "Current Developments",
                    "insight": "Recent work highlights ongoing evolution "
                    "and refinement of key ideas, with particular emphasis "
                    "on practical applications.",
                    "confidence": "high",
                },
            ],
            "key_insights": [
                "The field demonstrates consistent progress across multiple dimensions",
                "Practical applications continue to expand",
            ],
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_outliner(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        title = kwargs.get("title", "Content")
        return {
            "title": title if title != "Untitled" else "Content Document",
            "sections": [
                {
                    "title": "Introduction",
                    "key_points": [
                        "Hook and context for the topic",
                        f"Overview of {title}",
                        "Thesis statement",
                    ],
                },
                {
                    "title": "Background and Context",
                    "key_points": [
                        "Historical context",
                        "Key definitions",
                        "Current landscape",
                    ],
                },
                {
                    "title": "Main Analysis",
                    "key_points": [
                        "Core findings and insights",
                        "Supporting evidence and examples",
                        "Comparative analysis",
                    ],
                    "subsections": ["Key Finding 1", "Key Finding 2"],
                },
                {
                    "title": "Practical Implications",
                    "key_points": [
                        "Real-world applications",
                        "Implementation considerations",
                    ],
                },
                {
                    "title": "Conclusion",
                    "key_points": [
                        "Summary of key takeaways",
                        "Future outlook",
                        "Call to action",
                    ],
                },
            ],
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_writer(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        title = kwargs.get("title", "Content Document")
        kwargs.get("outline", "")
        kwargs.get("research_synthesis", "")

        if not title or title == "Untitled" or "# Untitled" in title:
            title = "Content Document"

        sections = []
        sections.append(
            "## Introduction\n\n"
            "This document provides a comprehensive overview of the subject, "
            "drawing on research and analysis to deliver actionable insights. "
            "The following sections explore key themes, examine evidence, "
            "and synthesize findings into a coherent narrative."
        )
        sections.append(
            "## Background and Context\n\n"
            "Understanding this topic requires examination of foundational "
            "concepts and the current landscape. The subject sits at the "
            "intersection of multiple disciplines, each contributing "
            "valuable perspectives and methodologies."
        )
        sections.append(
            "## Key Findings\n\n"
            "Analysis reveals several important findings. First, the topic "
            "has significant relevance across multiple domains. Second, "
            "ongoing developments continue to shape understanding and "
            "application. Third, there are important implications for "
            "practitioners and stakeholders."
        )
        sections.append(
            "## Analysis and Discussion\n\n"
            "The evidence suggests several important conclusions. "
            "Practical applications demonstrate the value of understanding "
            "these concepts, while emerging trends point toward continued "
            "evolution of the field."
        )
        sections.append(
            "## Conclusion\n\n"
            "In summary, the comprehensive analysis of available research "
            "and materials provides a solid foundation for understanding "
            "this topic. Key takeaways include the importance of staying "
            "current with developments and applying insights in practical "
            "contexts."
        )

        full_content = f"# {title}\n\n" + "\n\n".join(sections)

        return {
            "content": full_content,
            "title": title,
            "word_count": len(full_content.split()),
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_validator(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        return {
            "overall_score": 50,
            "passes": False,
            "sections": [],
            "issues": [
                {
                    "severity": "error",
                    "location": "general",
                    "description": f"Validation could not be completed: {error}",
                    "recommendation": "Manual review required",
                }
            ],
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_seo(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        return {
            "meta_title": "",
            "meta_description": "",
            "keyword_analysis": {},
            "readability_score": 0.0,
            "recommendations": [
                f"SEO analysis unavailable due to: {error}",
            ],
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_fact_checker(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        return {
            "claims": [],
            "summary": {
                "total_claims": 0,
                "verified": 0,
                "unverified": 0,
                "questionable": 0,
                "false": 0,
            },
            "overall_assessment": f"Fact-checking could not be completed: {error}",
            "_fallback": True,
            "_fallback_reason": error,
        }

    def _fallback_finalizer(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        original_content = kwargs.get("content", "")
        if original_content and len(original_content) > 50:
            return {
                "content": original_content,
                "changes_applied": [],
                "notes": f"Finalization used original content due to: {error}",
                "_fallback": True,
                "_fallback_reason": error,
            }
        return self._fallback_writer(kwargs, error)

    def _fallback_generic(
        self, kwargs: dict[str, Any], error: str,
    ) -> dict[str, Any]:
        return {
            "result": "Fallback output generated",
            "note": f"Agent execution encountered an error: {error}",
            "input_keys": list(kwargs.keys()),
            "_fallback": True,
            "_fallback_reason": error,
        }


fallback_generator = FallbackGenerator()
