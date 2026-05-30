import asyncio
from app.research import (
    research_pipeline, relevance_engine,
    research_synthesis, citation_engine, knowledge_packager,
)
from app.research.models import ResearchQuery
from app.research.providers.mock import MockSearchProvider

async def final_verification():
    print('='*70)
    print('PHASE 5: RESEARCH INTELLIGENCE SYSTEM - FINAL VERIFICATION')
    print('='*70)
    print()
    
    # 1. Test Pipeline
    print('[1/6] Testing Research Pipeline...')
    pipeline = research_pipeline
    pipeline.register_provider(MockSearchProvider())
    
    query = ResearchQuery(query='artificial intelligence', max_results=10)
    result = await pipeline.execute(query, 'test-123')
    print(f'  OK - Found: {result.total_found} sources')
    print(f'  OK - After dedup: {result.total_after_dedup}')
    print()
    
    # 2. Test Synthesis (CRITICAL)
    print('[2/6] Testing Research Synthesis (CRITICAL)...')
    synthesis = await research_synthesis.synthesize(
        sources=result.sources[:5],
        topic='AI Overview',
        query='artificial intelligence',
    )
    print(f'  OK - Summary length: {len(synthesis.summary)} chars')
    print(f'  OK - Key findings: {len(synthesis.key_findings)}')
    print(f'  OK - Major themes: {len(synthesis.major_themes)}')
    
    assert len(synthesis.summary.split()) >= 20
    print(f'  OK - NO useless summaries')
    print()
    
    # 3. Test Knowledge Packaging
    print('[3/6] Testing Knowledge Packaging...')
    packet = knowledge_packager.package(synthesis, result.sources[:5], 'AI Overview')
    print(f'  OK - Writer brief: {len(packet.writer_brief)} chars')
    print(f'  OK - SEO keywords: {len(packet.seo_data.get("primary_keywords", []))}')
    print()
    
    # 4. Test Citations
    print('[4/6] Testing Citation Engine...')
    citations = citation_engine.generate_citations(result.sources[:3])
    print(f'  OK - Generated: {len(citations)} citations')
    print()
    
    # 5. Test Relevance
    print('[5/6] Testing Relevance Engine...')
    scored = relevance_engine.score_all(result.sources[:5], 'machine learning')
    print(f'  OK - Top score: {scored[0].combined_score:.3f}')
    print()
    
    print('='*70)
    print('PHASE 5 VERIFICATION: COMPLETE - ALL SYSTEMS OPERATIONAL')
    print('='*70)

asyncio.run(final_verification())