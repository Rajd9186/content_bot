from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ResponseParser:
    _json_block_re = re.compile(
        r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL
    )
    _markdown_heading_re = re.compile(r"^#{1,6}\s+", re.MULTILINE)

    def parse_json(self, raw: str) -> tuple[dict[str, Any] | None, str | None]:
        if not raw or not raw.strip():
            return None, "Empty response"

        stripped = raw.strip()
        try:
            return json.loads(stripped), None
        except json.JSONDecodeError:
            pass

        match = self._json_block_re.search(stripped)
        if match:
            content = match.group(1).strip()
            if content:
                try:
                    return json.loads(content), None
                except json.JSONDecodeError as e:
                    recovered = self._attempt_json_recovery(content)
                    if recovered is not None:
                        return recovered, None
                    return None, f"JSON parse error in code block: {e}"

        recovered = self._attempt_json_recovery(stripped)
        if recovered is not None:
            return recovered, None

        return None, "No valid JSON found in response"

    def parse_markdown(self, raw: str) -> tuple[str, str | None]:
        if not raw or not raw.strip():
            return "", "Empty response"

        stripped = raw.strip()

        if self._is_empty_content(stripped):
            return "", "Empty content (placeholder detected)"

        placeholders = self._detect_placeholders(stripped)
        warnings = []
        if placeholders:
            warnings.append(f"Placeholders detected: {', '.join(placeholders)}")

        return stripped, None

    def _attempt_json_recovery(self, text: str) -> dict[str, Any] | None:
        text = re.sub(r",\s*([}\]])", r"\1", text)
        text = re.sub(r"'([^']*)'", r'"\1"', text)
        text = re.sub(r"(\w+):", r'"\1":', text)
        text = re.sub(r",\s*$", "", text.strip())

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        brace_stack = []
        for ch in text:
            if ch in ("{", "["):
                brace_stack.append(ch)
            elif ch in ("}", "]") and brace_stack:
                brace_stack.pop()

        if brace_stack:
            closing = "".join(
                "]" if b == "[" else "}" for b in reversed(brace_stack)
            )
            try:
                return json.loads(text + closing)
            except json.JSONDecodeError:
                pass

        return None

    def _is_empty_content(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped or len(stripped) < 20:
            return True

        empty_patterns = [
            r"^#\s*Untitled",
            r"^#\s*Title\s*$",
            r"^\[Content",
            r"^\[Insert",
            r"^TODO",
            r"^\[.*?needed.*?\]",
            r"^\*\*?\[.*?\]\*\*?$",
        ]
        for pattern in empty_patterns:
            if re.search(pattern, stripped, re.IGNORECASE):
                return True

        heading_count = len(self._markdown_heading_re.findall(stripped))
        return bool(heading_count == 0 and len(stripped.split()) < 50)

    def _detect_placeholders(self, text: str) -> list[str]:
        patterns = {
            "# Untitled": r"#\s*Untitled",
            "[Content needed]": r"\[Content.*?\]",
            "[Insert here]": r"\[Insert.*?\]",
            "TODO": r"\bTODO\b",
            "[needed]": r"\[.*?needed.*?\]",
            "lorem ipsum": r"\blorem\s+ipsum\b",
        }
        found = []
        for name, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(name)
        return found

    def has_hallucinated_citations(
        self, text: str, known_sources: list[str] | None = None,
    ) -> list[str]:
        citations = re.findall(r"\[Source:\s*([^\]]+)\]", text)
        if not known_sources:
            return []

        hallucinated = []
        known_lower = [s.lower() for s in known_sources]
        for cite in citations:
            cite_lower = cite.lower()
            if not any(k in cite_lower or cite_lower in k for k in known_lower):
                hallucinated.append(cite)
        return hallucinated
