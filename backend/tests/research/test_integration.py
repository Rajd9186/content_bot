from __future__ import annotations

import asyncio
import pytest

from app.research.pipeline import ResearchPipeline
from app.research.models import ResearchQuery, SourceQuality
from app.research.synthesis.engine import ResearchSynthesisEngine
from app.research.knowledge import KnowledgePackager
from app.research.providers.mock import MockSearchProvider


async def test_full_research_pipeline() -> None:
    """Test complete research pipeline from query to knowledge packet"""
    
    pipeline = ResearchPipeline()
    mock_provider = MockSearchProvider()
    pipeline.register_provider(mock_provider)
    
    query = ResearchQuery(
        query="artificial intelligence in healthcare",
        topics=["diagnostics", "treatment"],
        max_results=20,
        time_range_days=90,
    )
    
    result = await pipeline.execute(
        query=query,
        correlation_id="test-research-123",
    )
    
    assert result.total_found > 0
    assert result.total_after_dedup > 0
    assert len(result.sources) > 0
    assert all(s.quality != SourceQuality.SPAM for s in result.sources)


async def test_research_synthesis_engine() -> None:
    """Test that synthesis generates meaningful summaries (NOT useless one-liners)"""
    
    pipeline = ResearchPipeline()
    mock_provider = MockSearchProvider()
    pipeline.register_provider(mock_provider)
    
    query = ResearchQuery(
        query="machine learning applications",
        topics=["healthcare"],
        max_results=10,
    )
    
    result = await pipeline.execute(query, "test-123")
    
    synthesis_engine = ResearchSynthesisEngine()
    synthesis = await synthesis_engine.synthesize(
        sources=result.sources,
        topic="Machine Learning Applications",
        query=query.query,
    )
    
    assert len(synthesis.summary) >= 100
    assert "Collected" not in synthesis.summary or len(synthesis.summary) > 50
    assert len(synthesis.key_findings) >= 1
    assert len(synthesis.major_themes) >= 1
    
    for finding in synthesis.key_findings:
        assert len(finding.finding.split()) >= 15
        assert finding.source_count >= 1


async def test_knowledge_packet_generation() -> None:
    """Test knowledge packet creation for downstream agents"""
    
    pipeline = ResearchPipeline()
    mock_provider = MockSearchProvider()
    pipeline.register_provider(mock_provider)
    
    query = ResearchQuery(
        query="renewable energy",
        max_results=10,
    )
    
    result = await pipeline.execute(query, "test-123")
    
    synthesis_engine = ResearchSynthesisEngine()
    synthesis = await synthesis_engine.synthesize(
        sources=result.sources,
        topic="Renewable Energy",
        query=query.query,
    )
    
    packager = KnowledgePackager()
    packet = packager.package(
        synthesis=synthesis,
        sources=result.sources,
        topic="Renewable Energy",
    )
    
    assert packet.topic == "Renewable Energy"
    assert len(packet.writer_brief) > 50
    assert isinstance(packet.seo_data, dict)
    assert len(packet.validation_checklist) > 0
    assert len(packet.fact_check_items) >= 0


async def test_research_eliminate_useless_summaries() -> None:
    """CRITICAL: Verify synthesis does NOT produce 'Collected 50 sources' summaries"""
    
    from app.research.models import ResearchSource, SourceQuality, SourceType
    
    synthesis_engine = ResearchSynthesisEngine()
    
    mock_sources = [
        ResearchSource(
            url=f'https://example.com/{i}',
            canonical_url=f'https://example.com/{i}',
            domain='example.com',
            title=f'Test Article {i}',
            snippet=f'Detailed snippet with substantial content about the topic {i} providing deep analysis and insights',
            quality=SourceQuality.HIGH,
            source_type=SourceType.WEB,
            authors=['Author'],
            content_hash=f'hash{i}',
            published_date=None,
        )
        for i in range(10)
    ]
    
    synthesis = await synthesis_engine.synthesize(
        sources=mock_sources,
        topic="Test Topic",
        query="test query",
    )
    
    summary = synthesis.summary
    
    assert len(summary.split()) >= 20
    assert summary.strip() != "Collected 10 sources"
    assert "Collected" not in summary or len(summary) > 80


async def test_citation_validation() -> None:
    """Test citation engine prevents hallucinated citations"""
    
    from app.research.citations.engine import CitationEngine
    from app.research.models import ResearchSource
    
    engine = CitationEngine()
    
    sources = [
        ResearchSource(
            url="https://example.com/article",
            canonical_url="https://example.com/article",
            domain="example.com",
            title="Valid Article",
            snippet="Valid snippet",
        )
    ]
    
    citations = engine.generate_citations(sources)
    assert len(citations) == 1
    
    validation = engine.validate_citations(
        text="According to [Source: Valid Article, example.com]",
        sources=sources,
    )
    
    assert validation["is_valid"] is True
    assert len(validation["hallucinated_citations"]) == 0


async def test_source_deduplication() -> None:
    """Test that duplicate sources are removed"""
    
    from app.research.ingestion import SourceIngestion
    
    ingestion = SourceIngestion()
    
    raw_sources = [
        {
            "url": "https://example.com/article",
            "title": "Same Article",
            "snippet": "Same Snippet",
        },
        {
            "url": "https://example.com/article",
            "title": "Same Article",
            "snippet": "Same Snippet",
        },
        {
            "url": "https://different.com/article",
            "title": "Different Article",
            "snippet": "Different Snippet",
        },
    ]
    
    ingested = await ingestion.ingest(raw_sources)
    
    assert len(ingested) == 2
    stats = ingestion.get_stats()
    assert stats["duplicates"] == 1


async def test_relevance_scoring() -> None:
    """Test relevance engine scores sources correctly"""
    
    from app.research.relevance import RelevanceEngine
    from app.research.models import ResearchSource
    
    engine = RelevanceEngine()
    
    sources = [
        ResearchSource(
            url="https://example.com/ml",
            canonical_url="https://example.com/ml",
            domain="example.com",
            title="Machine Learning Guide",
            snippet="Comprehensive guide to machine learning with practical examples",
            quality="high",
        ),
        ResearchSource(
            url="https://example.com/cooking",
            canonical_url="https://example.com/cooking",
            domain="example.com",
            title="Cooking Recipes",
            snippet="Delicious recipes for dinner",
            quality="medium",
        ),
    ]
    
    scored = engine.score_all(sources, "machine learning tutorial")
    
    assert scored[0].title == "Machine Learning Guide"
    assert scored[0].combined_score > scored[1].combined_score


async def test_research_pipeline_with_mock_provider() -> None:
    """End-to-end test with mock search provider"""
    
    pipeline = ResearchPipeline()
    pipeline.register_provider(MockSearchProvider())
    
    query = ResearchQuery(
        query="test query for research",
        max_results=10,
    )
    
    result = await pipeline.execute(query, "test-correlation")
    
    assert result.query == "test query for research"
    assert result.total_found > 0
    assert result.search_latency_ms >= 0
    assert result.ingestion_latency_ms >= 0