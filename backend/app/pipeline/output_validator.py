from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

PLACEHOLDER_PATTERNS = [
    re.compile(r"\b(LOREM|IPSUM)\b", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\[INSERT\s", re.IGNORECASE),
    re.compile(r"\[PLACEHOLDER", re.IGNORECASE),
    re.compile(r"\[YOUR\s+TEXT", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER\b", re.IGNORECASE),
]

MIN_CONTENT_WORDS = 100
MIN_RESEARCH_SOURCES = 1
MIN_PLAN_SECTIONS = 2
MIN_TITLE_LENGTH = 3


class ValidationResult:
    def __init__(self) -> None:
        self.valid: bool = True
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def __bool__(self) -> bool:
        return self.valid


class AgentOutputValidator:
    def validate(self, agent_type: str, output: dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        if not output:
            result.add_error(f"{agent_type}: Output is empty")
            return result

        raw = output.get("raw_content", "")
        parse_error = output.get("parse_error", "")
        if parse_error and not raw:
            result.add_warning(f"{agent_type}: JSON parse error — {parse_error}")

        validator_map = {
            "research": self._validate_research,
            "planner": self._validate_planner,
            "writer": self._validate_writer,
            "seo": self._validate_seo,
            "fact_checker": self._validate_fact_checker,
            "compliance": self._validate_compliance,
            "finalizer": self._validate_finalizer,
        }
        validator = validator_map.get(agent_type)
        if validator:
            validator(output, result)

        self._check_placeholders(agent_type, output, result)
        return result

    def _validate_research(
        self, output: dict[str, Any], result: ValidationResult,
    ) -> None:
        summary = output.get("summary", "")
        if not summary or len(summary.strip()) < 20:
            result.add_error("research: Summary is missing or too short")

        citations = output.get("citations", [])
        if not citations or len(citations) < MIN_RESEARCH_SOURCES:
            result.add_warning("research: No citations provided")

        key_points = output.get("key_points", [])
        if not key_points:
            result.add_warning("research: No key_points found")

    def _validate_planner(
        self, output: dict[str, Any], result: ValidationResult,
    ) -> None:
        title = output.get("title", "")
        if not title or len(title.strip()) < MIN_TITLE_LENGTH:
            result.add_error("planner: Title is missing or too short")

        sections = output.get("sections", [])
        if not sections or len(sections) < MIN_PLAN_SECTIONS:
            result.add_error("planner: Need at least 2 sections")

        goals = output.get("goals", "")
        if not goals:
            result.add_warning("planner: No goals specified")

    def _validate_writer(
        self, output: dict[str, Any], result: ValidationResult,
    ) -> None:
        content = output.get("content", "")
        if not content:
            result.add_error("writer: No content produced")
            return

        word_count = len(content.split())
        if word_count < MIN_CONTENT_WORDS:
            result.add_warning(
                f"writer: Content is short ({word_count} words, expected {MIN_CONTENT_WORDS}+)"
            )

        title = output.get("title", "")
        if not title or len(title.strip()) < MIN_TITLE_LENGTH:
            result.add_warning("writer: Title is missing or too short")

    def _validate_seo(
        self, output: dict[str, Any], result: ValidationResult,
    ) -> None:
        primary_kw = output.get("primary_keywords", [])
        if not primary_kw:
            result.add_warning("seo: No primary keywords identified")

        meta_desc = output.get("meta_description", "")
        if not meta_desc:
            result.add_warning("seo: No meta description provided")

        content = output.get("content", "")
        if not content:
            result.add_warning("seo: No optimized content returned")

    def _validate_fact_checker(
        self, output: dict[str, Any], result: ValidationResult,
    ) -> None:
        verified = output.get("verified_claims", [])
        unverified = output.get("unverified_claims", [])
        disputed = output.get("disputed_claims", [])
        if not verified and not unverified and not disputed:
            result.add_warning("fact_checker: No claims evaluated")

        assessment = output.get("overall_assessment", "")
        if not assessment:
            result.add_warning("fact_checker: No overall assessment provided")

    def _validate_compliance(
        self, output: dict[str, Any], result: ValidationResult,
    ) -> None:
        status_val = output.get("compliance_status", "")
        if not status_val:
            result.add_warning("compliance: No compliance status provided")

        verdict = output.get("overall_verdict", "")
        if not verdict:
            result.add_warning("compliance: No overall verdict provided")

    def _validate_finalizer(
        self, output: dict[str, Any], result: ValidationResult,
    ) -> None:
        final_content = output.get("final_content", "") or output.get("content", "")
        if not final_content:
            result.add_error("finalizer: No final content produced")
            return

        word_count = len(final_content.split())
        if word_count < MIN_CONTENT_WORDS:
            result.add_error(
                f"finalizer: Final content too short ({word_count} words)"
            )

        title = output.get("title", "")
        if not title or len(title.strip()) < MIN_TITLE_LENGTH:
            result.add_warning("finalizer: Title is missing or too short")

    def _check_placeholders(
        self,
        agent_type: str,
        output: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        text_fields = ["content", "final_content", "summary", "title", "meta_description"]
        for field in text_fields:
            value = output.get(field, "")
            if not isinstance(value, str):
                continue
            for pattern in PLACEHOLDER_PATTERNS:
                if pattern.search(value):
                    result.add_warning(
                        f"{agent_type}: Placeholder text detected in '{field}'"
                    )
                    break


class ContentQualityValidator:
    def validate(self, content: str, title: str = "") -> ValidationResult:
        result = ValidationResult()

        if not content or not content.strip():
            result.add_error("Content is empty")
            return result

        if not title or len(title.strip()) < MIN_TITLE_LENGTH:
            result.add_error("Title is missing or too short")

        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(content):
                result.add_error(
                    f"Placeholder text detected in content: {pattern.pattern}"
                )

        word_count = len(content.split())
        if word_count < MIN_CONTENT_WORDS:
            result.add_error(
                f"Content too short: {word_count} words (minimum {MIN_CONTENT_WORDS})"
            )

        fake_citation_patterns = [
            re.compile(r"\[\d+\]\s*https?://example\.com", re.IGNORECASE),
            re.compile(r"\[\d+\]\s*https?://fake", re.IGNORECASE),
            re.compile(r"\[\d+\]\s*https?://placeholder", re.IGNORECASE),
            re.compile(r"\[\d+\]\s*https?://test", re.IGNORECASE),
        ]
        for pattern in fake_citation_patterns:
            if pattern.search(content):
                result.add_warning(f"Possible fake citation detected: {pattern.pattern}")

        if content.strip() == content.strip().upper() and word_count > 10:
            result.add_warning("Content appears to be all uppercase")

        sentences = re.split(r"[.!?]+", content)
        long_sentences = [s for s in sentences if len(s.split()) > 60]
        if len(long_sentences) > 3:
            result.add_warning(
                f"{len(long_sentences)} sentences exceed 60 words — readability issue"
            )

        return result


agent_output_validator = AgentOutputValidator()
content_quality_validator = ContentQualityValidator()
