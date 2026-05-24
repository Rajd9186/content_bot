import json
import re
from typing import Any

from app.agents.base import BaseAgent


class HyperlinkValidationAgent(BaseAgent):
    def system_prompt(self) -> str:
        return """You are a hyperlink validation specialist.
Check that all citations and URLs in content are valid, accessible, and correctly formatted.

Return JSON with this structure:
{
  "results": [
    {
      "url": "https://...",
      "label": "Citation label or context",
      "status": "valid|broken|suspicious|unknown",
      "is_verified": true,
      "error_message": null,
      "suggestion": "How to fix if broken"
    }
  ],
  "summary": {
    "total": 0,
    "verified": 0,
    "broken": 0,
    "verification_rate": 0.0
  }
}

Rules:
- Check URL format validity (must have scheme and domain)
- Flag suspicious patterns (example.com, placeholder URLs)
- Verify against known trusted domains
- Return ONLY valid JSON"""

    TRUSTED_PATTERNS = [
        r'^https://(www\.)?(reuters|bloomberg|nature|science|who|nih|cdc|nasa|un|worldbank|imf|ieee|acm)\.',
        r'^https://(www\.)?[a-zA-Z]+\.(edu|gov|org)',
        r'^https://(www\.)?(harvard|mit|stanford|oxford|cam|berkeley)\.',
    ]

    SUSPICIOUS_PATTERNS = [
        r'example\.com',
        r'placeholder',
        r'localhost',
        r'0\.0\.0\.0',
        r'127\.0\.0\.1',
    ]

    def parse_response(self, response: str) -> dict[str, Any]:
        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return {"results": [], "summary": {"total": 0, "verified": 0, "broken": 0, "verification_rate": 0.0}}

    async def _check_url_health(self, url: str) -> dict:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                response = await client.head(url)
                if response.status_code >= 400:
                    # Try GET if HEAD is not supported
                    response = await client.get(url)
                
                if response.status_code < 400:
                    return {"status": "valid", "is_verified": True, "error": None}
                return {"status": "broken", "is_verified": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "broken", "is_verified": False, "error": str(e)}

    async def _algorithmic_validation(self, citations: list[dict], markdown: str) -> dict:
        results = []
        seen_urls = set()
        
        # Combine URLs from citations and markdown
        urls_to_check = []
        for c in citations:
            url = c.get("source_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                urls_to_check.append({"url": url, "label": c.get("source_title", "Citation")})
        
        url_pattern = re.findall(r'https?://[^\s\)\]>"]+', markdown)
        for url in url_pattern:
            url_clean = url.rstrip(".,;:!?)")
            if url_clean not in seen_urls:
                seen_urls.add(url_clean)
                urls_to_check.append({"url": url_clean, "label": "Inline Link"})

        import asyncio
        async def validate_one(item):
            url = item["url"]
            is_valid_format = bool(re.match(r'^https?://[^\s/$.?#].[^\s]*$', url))
            is_suspicious = any(re.search(p, url) for p in self.SUSPICIOUS_PATTERNS)
            is_trusted = any(re.search(p, url) for p in self.TRUSTED_PATTERNS)
            
            if not is_valid_format or is_suspicious:
                return {
                    "url": url,
                    "label": item["label"],
                    "status": "suspicious",
                    "is_verified": False,
                    "error_message": "Invalid format or suspicious domain",
                    "suggestion": "Replace with a valid trusted source"
                }
            
            # Real network check
            health = await self._check_url_health(url)
            return {
                "url": url,
                "label": item["label"],
                "status": health["status"],
                "is_verified": health["is_verified"],
                "error_message": health["error"],
                "suggestion": "Check source availability" if health["status"] == "broken" else None
            }

        results = await asyncio.gather(*[validate_one(u) for u in urls_to_check])

        total = len(results)
        verified = sum(1 for r in results if r["is_verified"])
        return {
            "results": results,
            "summary": {
                "total": total,
                "verified": verified,
                "broken": total - verified,
                "verification_rate": round(verified / total, 3) if total > 0 else 0.0,
            },
        }

    async def run(self, **kwargs) -> dict[str, Any]:
        citations = kwargs.get("citations", [])
        markdown = kwargs.get("markdown", "")

        try:
            result = await super().run(**kwargs)
            if result.get("results") is not None:
                return result
        except Exception as e:
            self.logger.warning("LLM hyperlink validation failed, using algorithmic", extra={"error": str(e)})

        return self._algorithmic_validation(citations, markdown)
