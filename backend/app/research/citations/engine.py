from __future__ import annotations

import logging
from typing import Any, Optional

from app.research.models import Citation, ResearchSource, ResearchSynthesis

logger = logging.getLogger(__name__)


class CitationEngine:
    def __init__(self) -> None:
        self._citation_cache: dict[str, Citation] = {}

    def generate_citations(
        self,
        sources: list[ResearchSource],
        format: str = "inline",
    ) -> list[Citation]:
        citations = []
        
        for source in sources:
            citation = self._create_citation(source, format)
            
            if self._validate_citation(citation, source):
                citations.append(citation)
                self._citation_cache[source.canonical_url] = citation
        
        logger.info("Generated %d citations from %d sources", len(citations), len(sources))
        return citations

    def generate_inline_citation(self, source: ResearchSource) -> str:
        citation = self._create_citation(source, "inline")
        return citation.to_inline()

    def get_citation(self, url: str) -> Optional[Citation]:
        return self._citation_cache.get(url)

    def validate_citations(
        self,
        text: str,
        sources: list[ResearchSource],
    ) -> dict[str, Any]:
        source_urls = {s.canonical_url for s in sources}
        source_domains = {s.domain for s in sources}
        
        citations_in_text = self._extract_citations(text)
        
        valid = []
        invalid = []
        orphan = []
        
        for citation_text in citations_in_text:
            if any(url in citation_text for url in source_urls):
                valid.append(citation_text)
            elif any(domain in citation_text for domain in source_domains):
                valid.append(citation_text)
            else:
                invalid.append(citation_text)
        
        for source in sources:
            if not any(source.canonical_url in c or source.domain in c for c in citations_in_text):
                orphan.append(source.canonical_url)
        
        return {
            "total_citations": len(citations_in_text),
            "valid_citations": valid,
            "invalid_citations": invalid,
            "orphan_sources": orphan,
            "hallucinated_citations": [c for c in invalid if "Source:" in c],
            "is_valid": len(invalid) == 0,
        }

    def _create_citation(
        self,
        source: ResearchSource,
        format: str,
    ) -> Citation:
        return Citation(
            source_id=source.content_hash or source.canonical_url,
            url=source.url,
            title=source.title,
            authors=source.authors,
            published_date=source.published_date,
            citation_format=format,
            citation_text="",
        )

    def _validate_citation(
        self,
        citation: Citation,
        source: ResearchSource,
    ) -> bool:
        if not citation.url or not citation.title:
            logger.warning("Citation missing URL or title")
            return False
        
        if citation.title == "Untitled":
            logger.warning("Citation has untitled source")
            return False
        
        return True

    def _extract_citations(self, text: str) -> list[str]:
        import re
        
        pattern = r'\[Source:\s*[^\]]+\]'
        matches = re.findall(pattern, text)
        
        return matches


citation_engine = CitationEngine()