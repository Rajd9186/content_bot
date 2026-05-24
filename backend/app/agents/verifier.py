import json
import re
from typing import Any

from app.agents.base import BaseAgent


class VerificationAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a fact-verification specialist.
Extract factual claims from the research data and verify them against the provided evidence.

Return JSON with this structure:
{
  "claims": [
    {
      "claim_text": "The factual statement",
      "confidence": 0.95,
      "status": "verified",
      "explanation": "Supported by evidence from [source domain]",
      "category": "statistical",
      "supporting_evidence": ["snippet from source"],
      "contradicting_evidence": []
    }
  ],
  "overall_assessment": "Summary",
  "average_confidence": 0.85
}

Rules:
- "verified" only if evidence directly supports it
- "unverified" if partial evidence exists
- "contradicted" if evidence contradicts
- "unsupported" if no evidence
- Return ONLY valid JSON"""

    CATEGORY_KEYWORDS = {
        "statistical": ["percent", "%", "statistic", "rate", "ratio", "average", "median", "growth", "decline", "increase", "decrease"],
        "economic": ["billion", "million", "trillion", "dollar", "market", "revenue", "funding", "investment", "cost", "economic"],
        "scientific": ["study", "research", "clinical", "trial", "peer-reviewed", "journal", "laboratory", "experiment", "finding"],
        "historical": ["since", "founded", "established", "traditionally", "historical", "past decade", "century", "era"],
        "legal": ["regulation", "compliance", "policy", "law", "legal", "mandate", "requirement", "standard"],
        "technological": ["technology", "platform", "system", "software", "algorithm", "AI", "machine learning", "digital"],
    }

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return {"claims": [], "overall_assessment": "", "average_confidence": 0.0}

    def _extract_claims_from_text(self, text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        claims = []
        for s in sentences:
            s = s.strip()
            if len(s) < 40 or len(s) > 500:
                continue
            if s.startswith(("http", "https", "www.")):
                continue
            has_data = any(c.isdigit() for c in s)
            has_content = any(kw in s.lower() for kw in
                              ["percent", "study", "according", "research",
                               "report", "data", "found", "shows", "indicates",
                               "estimated", "projected", "increased"])
            if has_data or has_content:
                claims.append(s)
        return claims[:10]

    def _categorize_claim(self, claim_text: str) -> str:
        lower = claim_text.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return category
        return "general"

    def _algorithmic_verification(self, claims_text: str, evidence_sources: list[dict]) -> dict:
        extracted_claims = self._extract_claims_from_text(claims_text)
        verified_claims = []

        for claim in extracted_claims:
            best_confidence = 0.0
            best_explanation = ""
            best_source = ""
            category = self._categorize_claim(claim)

            for src in evidence_sources:
                snippet = src.get("snippet", "") or src.get("content", "") or ""
                domain = src.get("domain", src.get("url", "unknown"))
                trust = src.get("trust_score", 0.6)

                claim_keywords = set(re.findall(r'\b\w+\b', claim.lower()))
                snippet_keywords = set(re.findall(r'\b\w+\b', snippet.lower()))
                overlap = claim_keywords & snippet_keywords
                match_ratio = len(overlap) / max(len(claim_keywords), 1) if claim_keywords else 0

                if match_ratio > 0.15:
                    confidence = min(1.0, match_ratio * trust * 1.5)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_explanation = f"Evidence from {domain} contains supporting keywords with {match_ratio:.0%} overlap"
                        best_source = domain

            if best_confidence > 0:
                status = "verified" if best_confidence >= 0.7 else "unverified"
                explanation = best_explanation or f"Claim relates to {category} topic"
            else:
                status = "unverified"
                best_confidence = 0.5
                explanation = f"No direct evidence match found. Claim relates to {category} topic."

            verified_claims.append({
                "claim_text": claim,
                "confidence": round(best_confidence, 3),
                "status": status,
                "explanation": explanation,
                "category": category,
                "supporting_evidence": [best_source] if best_source else [],
                "contradicting_evidence": [],
            })

        avg_conf = (
            sum(c["confidence"] for c in verified_claims) / len(verified_claims)
            if verified_claims else 0.0
        )

        return {
            "claims": verified_claims,
            "overall_assessment": f"Extracted {len(verified_claims)} claims from research data. "
                                  f"Average confidence: {avg_conf:.1%}.",
            "average_confidence": round(avg_conf, 3),
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        claims_text = kwargs.get("research_data", "")
        evidence = kwargs.get("evidence_sources", kwargs.get("sources", []))

        if not claims_text:
            return {"claims": [], "overall_assessment": "No research data provided", "average_confidence": 0.0}

        try:
            result = await super().run(**kwargs)
            if result.get("claims"):
                self.logger.info(
                    "Verification completed via LLM",
                    extra={"claims": len(result["claims"])},
                )
                return result
        except Exception as e:
            self.logger.warning("LLM verification failed, using algorithmic fallback", extra={"error": str(e)})

        self.logger.info("Using algorithmic claim extraction and verification")
        return self._algorithmic_verification(claims_text, evidence)
