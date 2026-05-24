import re
from typing import Any

from app.agents.base import BaseAgent


class ContradictionDetectionAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a contradiction detection specialist.
Analyze claims and evidence sources for contradictions.

Return JSON with this structure:
{
  "contradictions": [
    {
      "claim": "The conflicting claim text",
      "conflicting_sources": [
        {"source": "URL or domain", "statement": "What this source says"}
      ],
      "severity": "high|medium|low",
      "explanation": "Why these statements contradict each other",
      "category": "statistical|temporal|definitional|forecast"
    }
  ],
  "overall_assessment": "Summary of contradiction analysis"
}

Rules:
- High severity: Direct numerical contradictions (>10% difference)
- Medium severity: Inconsistent trends or forecasts
- Low severity: Minor inconsistencies in framing
- Return ONLY valid JSON"""

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            import json
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return {"contradictions": [], "overall_assessment": ""}

    def _extract_numbers(self, text: str) -> list[float]:
        return [float(n) for n in re.findall(r'\d+\.?\d*', text) if float(n) > 1]

    def _algorithmic_check(self, claims: list[dict], sources: list[dict]) -> dict:
        contradictions = []
        for i, c1 in enumerate(claims):
            c1_text = c1.get("claim_text", "") or c1.get("claim", "")
            c1_nums = self._extract_numbers(c1_text)
            for j, c2 in enumerate(claims):
                if j <= i:
                    continue
                c2_text = c2.get("claim_text", "") or c2.get("claim", "")
                c2_nums = self._extract_numbers(c2_text)
                if c1_nums and c2_nums:
                    for n1 in c1_nums:
                        for n2 in c2_nums:
                            if n2 > 0 and abs(n1 - n2) / n2 > 0.3 and abs(n1 - n2) > 5:
                                contradictions.append({
                                    "claim": f"{c1_text[:100]}... vs {c2_text[:100]}...",
                                    "conflicting_sources": [
                                        {"source": c1.get("source_url", "unknown"), "statement": c1_text[:150]},
                                        {"source": c2.get("source_url", "unknown"), "statement": c2_text[:150]},
                                    ],
                                    "severity": "high" if abs(n1 - n2) / n2 > 0.5 else "medium",
                                    "explanation": f"Numerical conflict: {n1} vs {n2} ({abs(n1 - n2)/n2:.0%} difference)",
                                    "category": "statistical",
                                })
                                break
                        if contradictions and contradictions[-1]["claim"].startswith(c1_text[:100]):
                            break

        return {
            "contradictions": contradictions[:5],
            "overall_assessment": f"Found {len(contradictions)} potential contradictions in claims",
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        claims = kwargs.get("claims", [])
        sources = kwargs.get("sources", [])
        if not claims:
            return {"contradictions": [], "overall_assessment": "No claims to analyze"}

        try:
            result = await super().run(**kwargs)
            if result.get("contradictions"):
                return result
        except Exception as e:
            self.logger.warning("LLM contradiction check failed, using algorithmic", extra={"error": str(e)})

        return self._algorithmic_check(claims, sources)
