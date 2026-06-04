import json
from typing import Any

from app.agents.base import BaseAgent


class SelfVerificationAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a quality assurance auditor for AI-generated content.
Detect unsupported claims, hallucination risks, contradictions, and citation mismatches.

Return JSON with this structure:
{
  "audit_passed": true,
  "issues_found": [
    {
      "type": "unsupported_claim" | "hallucination_risk" | "contradiction" | "citation_mismatch",
      "severity": "high" | "medium" | "low",
      "excerpt": "Problematic text",
      "explanation": "Why flagged",
      "recommendation": "Suggested fix"
    }
  ],
  "overall_confidence_adjustment": 0.0,
  "final_assessment": "Quality assessment",
  "verified_claims_count": 0,
  "flagged_issues_count": 0,
  "hallucination_risk_score": 0.0
}

Rules:
- hallucination_risk_score 0.0 (none) to 1.0 (severe)
- If risk > 0.2, set audit_passed false
- Return ONLY valid JSON"""

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return self._algorithmic_audit("", [])

    def _algorithmic_audit(self, content: str, citations: list[dict]) -> dict:
        issues = []

        lines = content.split("\n") if content else []
        citation_refs = set()
        for line in lines:
            refs = [w for w in line.split() if w.startswith("[^") and w.endswith("]")]
            for r in refs:
                try:
                    num = int(r[2:-1])
                    citation_refs.add(num)
                except ValueError:
                    pass

        citation_ids = {c.get("id") for c in citations}
        orphan_refs = citation_refs - citation_ids
        for ref in orphan_refs:
            issues.append({
                "type": "citation_mismatch",
                "severity": "high",
                "excerpt": f"[^{ref}]",
                "explanation": f"Citation reference [^{ref}] has no matching citation entry",
                "recommendation": f"Add citation [^{ref}] entry or remove the reference",
            })

        sentences = [s.strip() for s in content.replace("? ", ". ").replace("! ", ". ").split(". ")]
        for sent in sentences:
            if len(sent) > 100 and "[^" not in sent:
                has_assertion = any(kw in sent.lower() for kw in
                                    ["according to", "research shows", "studies indicate",
                                     "data suggests", "experts say", "reported that"])
                if has_assertion:
                    issues.append({
                        "type": "unsupported_claim",
                        "severity": "medium",
                        "excerpt": sent[:200],
                        "explanation": "Factual assertion without citation reference",
                        "recommendation": "Add a citation to support this claim",
                    })

        risk_score = min(1.0, len(issues) * 0.1)
        audit_passed = risk_score <= 0.2
        conf_adjustment = max(-0.3, -len(issues) * 0.02)

        return {
            "audit_passed": audit_passed,
            "issues_found": issues,
            "overall_confidence_adjustment": round(conf_adjustment, 3),
            "final_assessment": f"Audit {'passed' if audit_passed else 'failed'}. "
                                f"Found {len(issues)} issues. Risk score: {risk_score:.2f}.",
            "verified_claims_count": len(citation_ids),
            "flagged_issues_count": len(issues),
            "hallucination_risk_score": round(risk_score, 3),
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        content = kwargs.get("content", "")
        citations = kwargs.get("citations", [])

        try:
            result = await super().run(**kwargs)
            if result.get("final_assessment"):
                self.logger.info(
                    "Self-verification completed via LLM",
                    extra={
                        "audit_passed": result.get("audit_passed"),
                        "issues": result.get("flagged_issues_count"),
                    },
                )
                return result
        except Exception as e:
            self.logger.warning("LLM self-verification failed, using algorithmic audit", extra={"error": str(e)})

        self.logger.info("Using algorithmic self-verification audit")
        return self._algorithmic_audit(content, citations)
