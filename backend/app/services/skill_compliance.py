from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class ComplianceEvaluator:
    CATEGORY_RULES = {
        "writing": ["tone", "style", "voice"],
        "seo": ["keyword", "meta", "heading"],
        "fact_check": ["source", "citation", "accuracy"],
        "compliance": ["regulation", "disclaimer", "restriction"],
        "brand_voice": ["brand", "voice", "terminology"],
        "youtube": ["intro", "hook", "cta"],
        "finance": ["disclaimer", "regulation", "risk"],
    }

    async def evaluate(
        self, content: str, skill_content_markdown: str, skill_category: str,
    ) -> dict:
        rules = await self._parse_rules(skill_content_markdown)
        violations: list[str] = []

        for rule in rules:
            if not await self._check_rule(rule, content):
                violations.append(rule)

        has_tone = any(k in skill_content_markdown.lower() for k in ("tone", "voice", "formality"))
        has_source = any(k in skill_content_markdown.lower() for k in ("source", "citation", "reference"))
        has_keyword = any(k in skill_content_markdown.lower() for k in ("keyword", "keyphrase", "seo"))

        if has_tone:
            tone_markers = r"\b(formal|professional|casual|conversational|customer|authoritative)\b"
            if not re.search(tone_markers, content, re.IGNORECASE):
                violations.append("Missing tone markers required by skill")

        if has_source:
            citation_pattern = r"\[.*?\]|\(.*?\d{4}.*?\)|https?://\S+"
            if not re.search(citation_pattern, content):
                violations.append("Missing required citations or sources")

        if has_keyword:
            keyword_lines = [
                line for line in skill_content_markdown.split("\n")
                if re.search(r"(keyword|keyphrase|seo)", line, re.IGNORECASE)
            ]
            for kl in keyword_lines:
                words = re.findall(r'"([^"]+)"', kl)
                for w in words:
                    if w.lower() not in content.lower():
                        violations.append(f"Required keyword \"{w}\" not found in content")
                        break

        score = max(0.0, 1.0 - (len(violations) / max(len(rules) + 2, 1)))
        return {"compliance_score": round(score, 2), "violations": violations}

    async def _check_rule(self, rule: str, content: str) -> bool:
        rule_lower = rule.lower().strip()

        if rule_lower.startswith("must include"):
            requirement = rule_lower.replace("must include", "").strip()
            return requirement in content.lower()

        if rule_lower.startswith("must not include"):
            forbidden = rule_lower.replace("must not include", "").strip()
            return forbidden not in content.lower()

        if rule_lower.startswith(("use ", "avoid ", "ensure ", "do not")):
            keywords = re.findall(r'"([^"]+)"', rule)
            if keywords:
                return any(k.lower() in content.lower() for k in keywords)

            tokens = rule.split()
            stop_words = {"use", "avoid", "ensure", "do", "not", "the", "and", "for"}
            meaningful = [t for t in tokens if len(t) > 3 and t not in stop_words]
            if meaningful:
                return any(w.lower() in content.lower() for w in meaningful)

        return True

    async def _parse_rules(self, markdown: str) -> list[str]:
        rules: list[str] = []
        for line in markdown.split("\n"):
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ")):
                rule_text = re.sub(r"^[\-\*\d]+\.\s*", "", stripped)
                if rule_text:
                    rules.append(rule_text)
        return rules
