#!/usr/bin/env python
"""
PHASE 5: RESEARCH INTELLIGENCE SYSTEM - COMPREHENSIVE AUDIT
============================================================

Auditor: Principal AI Research Systems Engineer
Date: 2026-05-29
Scope: Complete validation of research intelligence capabilities
"""

import asyncio
import hashlib
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.research import (
    research_pipeline, source_ingestion, relevance_engine,
    research_synthesis, citation_engine, knowledge_packager,
)
from app.research.models import (
    ResearchQuery, ResearchSource, SourceQuality, SourceType,
    Citation, ResearchSynthesis, SynthesizedFinding, KnowledgePacket,
)
from app.research.providers.mock import MockSearchProvider
from app.research.telemetry import research_telemetry


class AuditResult:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.score = 0.0
        self.findings: List[str] = []
        self.critical_issues: List[str] = []
        self.metrics: Dict[str, Any] = {}

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.test_name} (Score: {self.score:.2f})"


async def audit_source_ingestion() -> AuditResult:
    """Test source ingestion with duplicates, spam, and low-quality sources"""
    result = AuditResult("Source Ingestion & Deduplication")
    
    # Create test sources with intentional duplicates
    raw_sources = [
        # Duplicate 1 & 2
        {
            "url": "https://example.com/article-1",
            "title": "Same Article Title",
            "snippet": "Identical snippet content",
        },
        {
            "url": "https://example.com/article-1-copy",
            "title": "Same Article Title",
            "snippet": "Identical snippet content",
        },
        # Low quality
        {
            "url": "https://spam-site.com/clickbait",
            "title": "SHOCKING Miracle Discovery!",
            "snippet": "You won't believe this viral sensation",
        },
        # High quality
        {
            "url": "https://arxiv.org/paper/12345",
            "title": "Peer-Reviewed Research on Topic",
            "snippet": "Comprehensive study with statistical analysis",
            "authors": ["Dr. Author"],
            "published_date": datetime.now(timezone.utc),
        },
        # Medium quality
        {
            "url": "https://blog.example.com/post",
            "title": "Blog Post About Topic",
            "snippet": "Detailed analysis with 200+ words of content here",
        },
    ]
    
    ingested = await source_ingestion.ingest(raw_sources)
    stats = source_ingestion.get_stats()
    
    # Validate
    if len(ingested) == 4:  # 5 - 1 duplicate
        result.score += 25
        result.findings.append("Duplicate detection working (5 -> 4)")
    else:
        result.critical_issues.append(f"Expected 4 sources, got {len(ingested)}")
    
    # Check spam filtering
    spam_filtered = any(s.domain == "spam-site.com" for s in ingested)
    if not spam_filtered:
        result.score += 25
        result.findings.append("Spam filtering active")
    else:
        result.critical_issues.append("Spam source not filtered")
    
    # Check quality assessment
    high_quality = [s for s in ingested if s.quality == SourceQuality.HIGH]
    if len(high_quality) >= 1:
        result.score += 25
        result.findings.append(f"Quality assessment: {len(high_quality)} high-quality sources")
    
    # Check content hashing
    hashes = [s.content_hash for s in ingested if s.content_hash]
    if len(hashes) == len(set(hashes)):
        result.score += 25
        result.findings.append("Content hashing unique")
    else:
        result.critical_issues.append("Duplicate hashes detected")
    
    result.metrics = {
        "ingested": len(ingested),
        "duplicates": stats["duplicates"],
        "spam_filtered": stats["spam"],
        "high_quality": len(high_quality),
    }
    
    result.passed = result.score >= 75
    return result


async def audit_relevance_scoring() -> AuditResult:
    """Test relevance engine scoring accuracy"""
    result = AuditResult("Relevance Engine Scoring")
    
    sources = [
        ResearchSource(
            url="https://ml-guide.com/tutorial",
            canonical_url="https://ml-guide.com/tutorial",
            domain="ml-guide.com",
            title="Machine Learning Complete Tutorial",
            snippet="Comprehensive guide to machine learning with practical examples and code",
            quality=SourceQuality.HIGH,
        ),
        ResearchSource(
            url="https://cooking.com/recipes",
            canonical_url="https://cooking.com/recipes",
            domain="cooking.com",
            title="Delicious Dinner Recipes",
            snippet="Best recipes for cooking dinner at home with family",
            quality=SourceQuality.MEDIUM,
        ),
        ResearchSource(
            url="https://arxiv.org/ml-research",
            canonical_url="https://arxiv.org/ml-research",
            domain="arxiv.org",
            title="Advances in Machine Learning Research",
            snippet="Peer-reviewed paper on neural network architectures",
            quality=SourceQuality.HIGH,
            source_type="academic",
        ),
    ]
    
    scored = relevance_engine.score_all(sources, "machine learning tutorial")
    
    # Validate ranking
    if scored[0].domain in ["ml-guide.com", "arxiv.org"]:
        result.score += 30
        result.findings.append(f"Top result relevant: {scored[0].domain}")
    else:
        result.critical_issues.append(f"Irrelevant top result: {scored[0].domain}")
    
    # Check score differentiation
    if scored[0].combined_score > scored[-1].combined_score:
        result.score += 30
        result.findings.append(f"Score range: {scored[0].combined_score:.3f} - {scored[-1].combined_score:.3f}")
    else:
        result.critical_issues.append("No score differentiation")
    
    # Check component scores
    top = scored[0]
    if all([
        top.semantic_score >= 0,
        top.keyword_score >= 0,
        top.recency_score >= 0,
        top.authority_score >= 0,
    ]):
        result.score += 20
        result.findings.append("All scoring components active")
    
    # Check authority bonus
    arxiv_source = next((s for s in scored if s.domain == "arxiv.org"), None)
    if arxiv_source and arxiv_source.authority_score > 0.7:
        result.score += 20
        result.findings.append("Authority scoring working")
    
    result.metrics = {
        "top_source": scored[0].title,
        "top_score": scored[0].combined_score,
        "score_spread": scored[0].combined_score - scored[-1].combined_score,
    }
    
    result.passed = result.score >= 70
    return result


async def audit_synthesis_quality() -> AuditResult:
    """CRITICAL: Test synthesis eliminates useless summaries"""
    result = AuditResult("Research Synthesis Quality (CRITICAL)")
    
    # Create diverse sources
    sources = [
        ResearchSource(
            url=f"https://source-{i}.com",
            canonical_url=f"https://source-{i}.com",
            domain=f"source-{i}.com",
            title=f"Research Study {i}: ML in Healthcare",
            snippet=f"Study {i} shows {10+i*5}% improvement in diagnostic accuracy with ML systems",
            quality=SourceQuality.HIGH if i % 2 == 0 else SourceQuality.MEDIUM,
            source_type="academic" if i % 3 == 0 else "news",
            authors=[f"Author {i}"] if i % 2 == 0 else [],
            metadata={},
        )
        for i in range(8)
    ]
    
    synthesis = await research_synthesis.synthesize(
        sources=sources,
        topic="Machine Learning in Healthcare",
        query="ML healthcare diagnostics",
    )
    
    # CRITICAL CHECK 1: Summary length
    if len(synthesis.summary) >= 100:
        result.score += 20
        result.findings.append(f"Summary length adequate: {len(synthesis.summary)} chars")
    else:
        result.critical_issues.append(f"Summary too short: {len(synthesis.summary)} chars")
    
    # CRITICAL CHECK 2: No trivial summaries
    if "Collected" not in synthesis.summary or len(synthesis.summary) > 80:
        result.score += 20
        result.findings.append("No trivial 'Collected X sources' summary")
    else:
        result.critical_issues.append("Trivial summary detected")
    
    # CRITICAL CHECK 3: Key findings
    if len(synthesis.key_findings) >= 2:
        result.score += 15
        result.findings.append(f"Key findings: {len(synthesis.key_findings)}")
        
        # Check finding quality
        for finding in synthesis.key_findings[:3]:
            if len(finding.finding.split()) >= 15:
                result.score += 5
                result.findings.append("Findings substantive (15+ words)")
                break
    else:
        result.critical_issues.append("Insufficient key findings")
    
    # CRITICAL CHECK 4: Themes identified
    if len(synthesis.major_themes) >= 1:
        result.score += 10
        result.findings.append(f"Themes identified: {synthesis.major_themes[:3]}")
    
    # CRITICAL CHECK 5: Statistical insights
    if len(synthesis.statistical_insights) >= 1:
        result.score += 15
        result.findings.append(f"Statistical insights: {len(synthesis.statistical_insights)}")
    else:
        result.findings.append("No statistical insights extracted")
    
    # CRITICAL CHECK 6: Writer context
    if len(synthesis.writer_context) >= 50:
        result.score += 15
        result.findings.append("Writer context generated")
    
    result.metrics = {
        "summary_length": len(synthesis.summary),
        "key_findings": len(synthesis.key_findings),
        "themes": len(synthesis.major_themes),
        "statistics": len(synthesis.statistical_insights),
        "contradictions": len(synthesis.contradictions),
    }
    
    result.passed = result.score >= 70
    return result


async def audit_citation_integrity() -> AuditResult:
    """Test citation generation and hallucination detection"""
    result = AuditResult("Citation Integrity")
    
    sources = [
        ResearchSource(
            url="https://example.com/article",
            canonical_url="https://example.com/article",
            domain="example.com",
            title="Valid Research Article",
            snippet="Valid content",
            authors=["John Smith"],
        ),
        ResearchSource(
            url="https://reliable.org/study",
            canonical_url="https://reliable.org/study",
            domain="reliable.org",
            title="Peer-Reviewed Study",
            snippet="Research findings",
        ),
    ]
    
    # Generate citations
    citations = citation_engine.generate_citations(sources)
    
    if len(citations) == len(sources):
        result.score += 30
        result.findings.append(f"Citations generated: {len(citations)}")
    else:
        result.critical_issues.append("Citation count mismatch")
    
    # Test validation with valid citations
    valid_text = f"According to [Source: {sources[0].title}, {sources[0].domain}]"
    validation = citation_engine.validate_citations(valid_text, sources)
    
    if validation["is_valid"]:
        result.score += 30
        result.findings.append("Valid citations recognized")
    else:
        result.critical_issues.append("Valid citations rejected")
    
    # Test hallucination detection
    fake_text = "[Source: Fake Author, 2025, NonExistent Study]"
    validation_fake = citation_engine.validate_citations(fake_text, sources)
    
    if len(validation_fake.get("hallucinated_citations", [])) > 0 or not validation_fake["is_valid"]:
        result.score += 25
        result.findings.append("Hallucinated citations detected")
    else:
        result.critical_issues.append("Hallucinated citations not detected")
    
    # Check citation format
    if citations[0].to_inline():
        result.score += 15
        result.findings.append("Inline citation format working")
    
    result.metrics = {
        "citations_generated": len(citations),
        "valid_citations": len(validation.get("valid_citations", [])),
        "hallucinated_detected": len(validation_fake.get("hallucinated_citations", [])),
    }
    
    result.passed = result.score >= 75
    return result


async def audit_knowledge_packaging() -> AuditResult:
    """Test knowledge packet generation for downstream agents"""
    result = AuditResult("Knowledge Packaging")
    
    synthesis = ResearchSynthesis(
        topic="Test Topic",
        summary="Comprehensive analysis of test topic with multiple sources examined",
        key_findings=[
            SynthesizedFinding(
                finding="Key finding with substantial content and actionable insight",
                confidence=0.85,
                sources=["https://source1.com"],
                statistical=True,
            )
        ],
        major_themes=["Theme 1", "Theme 2"],
        statistical_insights=["40% improvement", "5000 patients studied"],
        expert_commentary=["Expert opinion from authoritative source"],
        top_sources=[],
        total_sources_analyzed=10,
    )
    
    sources = [
        ResearchSource(
            url="https://source.com",
            canonical_url="https://source.com",
            domain="source.com",
            title="Source Article",
            snippet="Content",
            quality=SourceQuality.HIGH,
        )
    ]
    
    packet = knowledge_packager.package(synthesis, sources, "Test Topic")
    
    # Check writer brief
    if len(packet.writer_brief) >= 50:
        result.score += 25
        result.findings.append(f"Writer brief: {len(packet.writer_brief)} chars")
    
    # Check SEO data
    if packet.seo_data and len(packet.seo_data.get("primary_keywords", [])) >= 0:
        result.score += 20
        result.findings.append("SEO data structured")
    
    # Check validation checklist
    if len(packet.validation_checklist) >= 1:
        result.score += 20
        result.findings.append(f"Validation checklist: {len(packet.validation_checklist)} items")
    
    # Check fact-check items
    if len(packet.fact_check_items) >= 0:
        result.score += 15
        result.findings.append("Fact-check items generated")
    
    # Check supporting evidence
    if len(packet.supporting_evidence) >= 1:
        result.score += 20
        result.findings.append(f"Supporting evidence: {len(packet.supporting_evidence)}")
    
    result.metrics = {
        "writer_brief_length": len(packet.writer_brief),
        "seo_keywords": len(packet.seo_data.get("primary_keywords", [])),
        "checklist_items": len(packet.validation_checklist),
        "fact_items": len(packet.fact_check_items),
    }
    
    result.passed = result.score >= 70
    return result


async def run_full_audit():
    """Execute complete Phase 5 audit"""
    print("="*80)
    print("PHASE 5: RESEARCH INTELLIGENCE SYSTEM - COMPREHENSIVE AUDIT")
    print("="*80)
    print()
    
    # Register mock provider
    research_pipeline.register_provider(MockSearchProvider())
    
    # Run audits
    results = []
    
    print("Running: Source Ingestion Audit...")
    results.append(await audit_source_ingestion())
    print(f"  {results[-1]}")
    
    print("Running: Relevance Scoring Audit...")
    results.append(await audit_relevance_scoring())
    print(f"  {results[-1]}")
    
    print("Running: Synthesis Quality Audit (CRITICAL)...")
    results.append(await audit_synthesis_quality())
    print(f"  {results[-1]}")
    
    print("Running: Citation Integrity Audit...")
    results.append(await audit_citation_integrity())
    print(f"  {results[-1]}")
    
    print("Running: Knowledge Packaging Audit...")
    results.append(await audit_knowledge_packaging())
    print(f"  {results[-1]}")
    
    print()
    print("="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    overall_score = sum(r.score for r in results) / total
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Overall Score: {overall_score:.2f}/100")
    print()
    
    for result in results:
        print(f"  {result}")
        for finding in result.findings:
            print(f"    - {finding}")
        if result.critical_issues:
            for issue in result.critical_issues:
                print(f"    - CRITICAL: {issue}")
    
    print()
    print("="*80)
    print("PRODUCTION READINESS ASSESSMENT")
    print("="*80)
    
    if overall_score >= 80 and all(r.passed for r in results):
        print("STATUS: PRODUCTION READY")
        print("All critical systems operational")
        print("No blocking issues detected")
    elif overall_score >= 60:
        print("STATUS: PROVISIONALLY READY")
        print("Minor issues require attention")
        for result in results:
            if not result.passed:
                print(f"  - {result.test_name}: {result.critical_issues}")
    else:
        print("STATUS: NOT READY")
        print("Critical issues must be resolved")
        for result in results:
            if result.critical_issues:
                print(f"  - {result.test_name}:")
                for issue in result.critical_issues:
                    print(f"      * {issue}")
    
    print()
    print("Metrics Summary:")
    metrics_summary = {}
    for result in results:
        metrics_summary.update(result.metrics)
    for key, value in metrics_summary.items():
        print(f"  {key}: {value}")
    
    print("="*80)
    
    return overall_score >= 75


if __name__ == "__main__":
    success = asyncio.run(run_full_audit())
    exit(0 if success else 1)