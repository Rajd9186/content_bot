from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.log_config.logger import get_logger
from app.repositories.project import ProjectRepository
from app.repositories.content import ContentRepository
from app.repositories.claim import ClaimRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.source import SourceRepository
from app.agents.topic_planner import TopicPlannerAgent
from app.agents.researcher import ResearchAgent
from app.agents.verifier import VerificationAgent
from app.agents.content_writer import ContentWriterAgent
from app.agents.self_verifier import SelfVerificationAgent
from app.services.research_service import ResearchService


class ContentGeneratorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(self.__class__.__name__)
        self.project_repo = ProjectRepository(session)
        self.content_repo = ContentRepository(session)
        self.claim_repo = ClaimRepository(session)
        self.evidence_repo = EvidenceRepository(session)
        self.source_repo = SourceRepository(session)
        self.research_service = ResearchService()

        self.topic_planner = TopicPlannerAgent()
        self.researcher = ResearchAgent()
        self.verifier = VerificationAgent()
        self.writer = ContentWriterAgent()
        self.self_verifier = SelfVerificationAgent()

    async def generate_full_content(self, project) -> dict:
        project_id = project.id
        self.logger.info("Starting content generation pipeline", extra={"project_id": str(project_id)})

        await self.project_repo.update_status(project_id, "planning")
        outline = await self._plan_topic(project)
        sections = outline.get("sections", [])
        self.logger.info("Planning complete", extra={"sections": len(sections)})

        await self.project_repo.update_status(project_id, "researching")
        research_data = await self._conduct_research(project, outline)
        self.logger.info("Research complete", extra={"sources": len(research_data.get("sources", []))})

        await self.project_repo.update_status(project_id, "verifying")
        extracted_claims = await self._extract_and_verify_claims(
            project_id, research_data
        )
        self.logger.info("Verification complete", extra={"claims": len(extracted_claims)})

        await self.project_repo.update_status(project_id, "generating")
        content_result = await self._write_content(
            project, outline, extracted_claims, research_data
        )
        self.logger.info(
            "Content generation complete",
            extra={
                "word_count": content_result.get("word_count", 0),
                "citations": len(content_result.get("citations", [])),
            },
        )

        await self.project_repo.update_status(project_id, "self_verifying")
        audit_result = await self._self_verify(content_result)

        final_confidence = self._compute_final_confidence(
            content_result, audit_result
        )

        saved_content = await self.content_repo.create(
            project_id=project_id,
            markdown=content_result.get("markdown", ""),
            summary=content_result.get("summary", ""),
            word_count=content_result.get("word_count", 0),
            citations=content_result.get("citations", []),
            seo_metadata=content_result.get("seo_metadata", {}),
            overall_confidence=final_confidence,
        )

        await self.project_repo.update_status(project_id, "completed")

        claims = await self.claim_repo.get_by_project(project_id)
        verification_summary = await self.claim_repo.get_verification_summary(project_id)

        self.logger.info(
            "Pipeline complete",
            extra={
                "project_id": str(project_id),
                "word_count": content_result.get("word_count"),
                "citations": len(content_result.get("citations", [])),
                "claims": len(claims),
                "confidence": final_confidence,
            },
        )

        return {
            "project_id": project_id,
            "content_id": saved_content.id,
            "markdown": saved_content.markdown,
            "summary": saved_content.summary or "",
            "word_count": saved_content.word_count or 0,
            "citations": saved_content.citations,
            "seo_metadata": saved_content.seo_metadata or {},
            "overall_confidence": final_confidence,
            "claims": [
                {
                    "id": str(c.id),
                    "claim_text": c.claim_text,
                    "confidence": c.confidence,
                    "status": c.status,
                }
                for c in claims
            ],
            "verification_summary": {
                **verification_summary,
                "audit_passed": audit_result.get("audit_passed"),
                "hallucination_risk_score": audit_result.get("hallucination_risk_score"),
                "issues_found": audit_result.get("flagged_issues_count", 0),
            },
        }

    async def _plan_topic(self, project) -> dict:
        try:
            outline = await self.topic_planner.run(
                topic=project.topic,
                title=project.title,
                content_type=project.content_type,
                tone=project.tone,
                target_audience=project.target_audience,
                points_to_cover=project.points_to_cover,
                seo_keywords=project.seo_keywords,
            )
        except Exception as e:
            self.logger.error("Topic planning failed", extra={"error": str(e)})
            outline = self.topic_planner._default_outline(project.title)

        await self.project_repo.update(project.id, outline=outline)
        return outline

    async def _conduct_research(self, project, outline: dict) -> dict:
        all_sources = []

        queries = []
        sections = outline.get("sections", [])
        for section in sections:
            queries.extend(section.get("research_queries", []))

        if not queries:
            queries = [
                f"{project.topic} current state research findings 2026",
                f"{project.topic} statistics data evidence",
                f"{project.topic} trusted source analysis",
                f"{project.topic} applications impact outcomes",
            ]

        self.logger.info("Executing research queries", extra={"queries_count": len(queries)})

        for query in queries:
            search_results = await self.research_service.search(query)
            for result in search_results:
                url = result.get("url", "")
                domain = url.split("/")[2] if "://" in url else ""
                snippet = result.get("content", "") or result.get("snippet", "") or ""

                source = await self.source_repo.create(
                    project_id=project.id,
                    url=url,
                    domain=domain,
                    title=result.get("title", ""),
                    trust_score=self.researcher.compute_trust_score(domain),
                    snippet=snippet[:500],
                )
                all_sources.append({
                    "url": source.url,
                    "domain": source.domain,
                    "title": source.title,
                    "snippet": source.snippet,
                    "trust_score": source.trust_score,
                    "relevance_score": result.get("score", 0.7),
                    "key_findings": [],
                    "evidence_snippets": [source.snippet] if source.snippet else [],
                })

        if not all_sources:
            self.logger.warning("No sources collected, returning empty research data")
            return {"sources": [], "summary": "", "key_insights": []}

        try:
            analysis = await self.researcher.run(query=project.topic, sources=all_sources)
            analyzed_sources = analysis.get("sources", all_sources)
            summary = analysis.get("summary", "")
        except Exception as e:
            self.logger.warning("Researcher analysis failed, using raw sources", extra={"error": str(e)})
            analyzed_sources = all_sources
            summary = f"Collected {len(all_sources)} sources about {project.topic}."

        return {
            "sources": analyzed_sources,
            "summary": summary,
            "key_insights": [s.get("snippet", "")[:100] for s in analyzed_sources[:3]],
        }

    async def _extract_and_verify_claims(self, project_id: UUID, research_data: dict) -> list:
        sources = research_data.get("sources", [])
        if not sources:
            self.logger.warning("No research data for claim extraction")
            return []

        claims_text = "\n".join(
            s.get("snippet", "") or s.get("content", "") or ""
            for s in sources
        )

        if not claims_text.strip():
            self.logger.warning("No text content in research data for claim extraction")
            return []

        try:
            verification_result = await self.verifier.run(
                research_data=claims_text,
                evidence_sources=sources,
            )
        except Exception as e:
            self.logger.warning("Verifier failed, using algorithmic extraction", extra={"error": str(e)})
            verification_result = self.verifier._algorithmic_verification(claims_text, sources)

        saved_claims = []
        for claim_data in verification_result.get("claims", []):
            claim = await self.claim_repo.create(
                project_id=project_id,
                claim_text=claim_data["claim_text"],
                confidence=claim_data.get("confidence"),
                status=claim_data.get("status", "unverified"),
                explanation=claim_data.get("explanation"),
                category=claim_data.get("category"),
            )
            saved_claims.append(claim)

        self.logger.info(
            "Claims extracted and saved",
            extra={"saved": len(saved_claims), "total_in_result": len(verification_result.get("claims", []))},
        )
        return saved_claims

    def _best_source_for_claim(self, claim_text: str, sources: list[dict]) -> tuple[str, str]:
        claim_words = set(claim_text.lower().split())
        best_url = ""
        best_domain = ""
        best_overlap = 0
        for s in sources:
            snippet = (s.get("snippet", "") or s.get("content", "") or "").lower()
            overlap = len(claim_words & set(snippet.split()))
            if overlap > best_overlap:
                best_overlap = overlap
                best_url = s.get("url", "") or ""
                best_domain = s.get("domain", "") or ""
        return best_url, best_domain

    async def _write_content(self, project, outline: dict, claims: list, research_data: dict) -> dict:
        sources = research_data.get("sources", [])
        verified_claims = [
            {
                "id": str(c.id),
                "claim_text": c.claim_text,
                "confidence": c.confidence,
                "status": c.status,
                "explanation": c.explanation,
                "category": c.category,
                "source_url": self._best_source_for_claim(c.claim_text, sources)[0],
                "supporting_evidence": (
                    [self._best_source_for_claim(c.claim_text, sources)[1]]
                    if self._best_source_for_claim(c.claim_text, sources)[1] else []
                ),
            }
            for c in claims
            if c.confidence and c.confidence >= 0.5
        ]

        self.logger.info(
            "Preparing content generation",
            extra={
                "total_claims": len(claims),
                "verified_claims_qualified": len(verified_claims),
            },
        )

        try:
            content_result = await self.writer.run(
                title=project.title,
                outline=outline,
                verified_claims=verified_claims,
                tone=project.tone,
                target_audience=project.target_audience,
                content_type=project.content_type,
                seo_keywords=project.seo_keywords,
                research_summary=research_data.get("summary", ""),
            )
            if content_result.get("markdown"):
                return content_result
        except Exception as e:
            self.logger.warning("LLM content writing failed, using template", extra={"error": str(e)})

        self.logger.info("Using template-based content generation")
        return self.writer._default_content(
            project.title,
            verified_claims,
            outline,
            research_data.get("summary", ""),
        )

    async def _self_verify(self, content_result: dict) -> dict:
        try:
            audit_result = await self.self_verifier.run(
                content=content_result.get("markdown", ""),
                citations=content_result.get("citations", []),
                claims_count=len(content_result.get("citations", [])),
            )
            if audit_result.get("final_assessment"):
                return audit_result
        except Exception as e:
            self.logger.warning("Self-verifier failed, using algorithmic audit", extra={"error": str(e)})

        return self.self_verifier._algorithmic_audit(
            content_result.get("markdown", ""),
            content_result.get("citations", []),
        )

    def _compute_final_confidence(self, content_result: dict, audit_result: dict) -> float:
        base = 0.85
        adjustment = audit_result.get("overall_confidence_adjustment", 0.0)
        risk = audit_result.get("hallucination_risk_score", 0)
        risk_penalty = risk * 0.3
        final = base + adjustment - risk_penalty
        return max(0.0, min(1.0, final))
