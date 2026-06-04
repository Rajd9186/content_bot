from __future__ import annotations

import re
from typing import Optional

from app.log_config.logger import get_logger

logger = get_logger(__name__)

PLACEHOLDER_PATTERNS = [
    r"(?i)\buntitled\b",
    r"(?i)\blorem ipsum\b",
    r"(?i)\bcoming soon\b",
    r"(?i)\bto be written\b",
    r"(?i)\b\[placeholder\]",
    r"(?i)\byour content here\b",
    r"(?i)\bwrite here\b",
    r"(?i)\binsert content\b",
    r"(?i)\bexample\.com\b",
]


class ValidationReport:
    def __init__(self):
        self.is_valid: bool = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.word_count: int = 0
        self.citation_count: int = 0
        self.heading_count: int = 0
        self.quality_score: float = 1.0
        self.hallucination_risk: float = 0.0
        self.completeness_score: float = 1.0
        self.missing_sections: list[str] = []

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def compute_scores(self) -> None:
        n_errors = len(self.errors)
        n_warnings = len(self.warnings)
        self.quality_score = max(0.0, 1.0 - (n_errors * 0.3 + n_warnings * 0.05))
        self.hallucination_risk = min(1.0, n_errors * 0.2 + (1 - self.citation_count / max(self.word_count / 100, 1)))
        self.completeness_score = max(0.0, 1.0 - len(self.missing_sections) * 0.15)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "word_count": self.word_count,
            "citation_count": self.citation_count,
            "heading_count": self.heading_count,
            "quality_score": round(self.quality_score, 3),
            "hallucination_risk": round(self.hallucination_risk, 3),
            "completeness_score": round(self.completeness_score, 3),
            "missing_sections": self.missing_sections,
        }


def validate_markdown_structure(markdown: str) -> ValidationReport:
    report = ValidationReport()

    if not markdown:
        report.add_error("markdown is empty")
        return report

    stripped = markdown.strip()

    if len(stripped) < 50:
        report.add_error(f"markdown too short ({len(stripped)} chars, min 50)")

    if not stripped.startswith("# "):
        report.add_warning("markdown does not start with H1 heading")

    headings = re.findall(r"^#{1,3}\s.+", stripped, re.MULTILINE)
    report.heading_count = len(headings)

    if report.heading_count < 2:
        report.add_warning(f"only {report.heading_count} headings found (min 2 recommended)")

    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, stripped):
            report.add_error("placeholder content detected")
            break

    return report


def validate_citations(citations: list[dict], min_required: int = 1) -> ValidationReport:
    report = ValidationReport()
    report.citation_count = len(citations)

    if report.citation_count < min_required:
        report.add_warning(f"only {report.citation_count} citations (min {min_required} recommended)")

    for i, cit in enumerate(citations):
        if not cit.get("source_url"):
            report.add_warning(f"citation {i+1} missing source_url")
        if not cit.get("text"):
            report.add_warning(f"citation {i+1} missing text")

    return report


def validate_heading_coverage(
    headings_used: list[str],
    outline_sections: list[dict],
) -> ValidationReport:
    report = ValidationReport()

    if not outline_sections:
        return report

    expected = {s.get("heading", "").lower().strip() for s in outline_sections if s.get("heading")}
    actual = {h.lower().strip() for h in headings_used}

    missing = expected - actual
    report.missing_sections = list(missing)

    if missing:
        report.add_warning(f"missing {len(missing)} expected sections: {', '.join(list(missing)[:5])}")

    return report


def validate_draft(
    markdown: str,
    title: str = "",
    citations: list | None = None,
    headings_used: list[str] | None = None,
    outline_sections: list[dict] | None = None,
    min_word_count: int = 300,
    min_citations: int = 1,
) -> ValidationReport:
    citations = citations or []
    headings_used = headings_used or []
    outline_sections = outline_sections or []

    struct_report = validate_markdown_structure(markdown)
    cit_report = validate_citations(citations, min_citations)
    head_report = validate_heading_coverage(headings_used, outline_sections)

    combined = ValidationReport()
    combined.errors = struct_report.errors + cit_report.errors + head_report.errors
    combined.warnings = struct_report.warnings + cit_report.warnings + head_report.warnings
    combined.is_valid = len(combined.errors) == 0
    combined.word_count = len(markdown.split()) if markdown else 0
    combined.citation_count = len(citations)
    combined.heading_count = struct_report.heading_count
    combined.missing_sections = head_report.missing_sections

    title_lower = title.lower().strip() if title else ""
    if title_lower == "untitled" or title_lower == "":
        combined.add_error("invalid title: 'Untitled' or empty")

    if combined.word_count < min_word_count:
        combined.add_error(f"word count too low: {combined.word_count} (min {min_word_count})")

    combined.compute_scores()

    logger.info(
        "Draft validation",
        extra={
            "is_valid": combined.is_valid,
            "word_count": combined.word_count,
            "citations": combined.citation_count,
            "errors": len(combined.errors),
            "warnings": len(combined.warnings),
            "quality_score": combined.quality_score,
            "hallucination_risk": combined.hallucination_risk,
        },
    )

    return combined
