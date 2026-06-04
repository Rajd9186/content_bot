from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.log_config.logger import get_logger
from app.repositories.claim import ClaimRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.source import SourceRepository
from app.agents.verifier import VerificationAgent


class VerificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(self.__class__.__name__)
        self.agent = VerificationAgent()
        self.claim_repo = ClaimRepository(session)
        self.evidence_repo = EvidenceRepository(session)
        self.source_repo = SourceRepository(session)

    async def verify_claims(
        self, project_id, research_data: dict[str, Any], claims_text: str
    ) -> list[dict[str, Any]]:
        verification_result = await self.agent.run(
            claims=claims_text,
            evidence=research_data.get("sources", []),
        )

        claims = verification_result.get("claims", [])
        saved_claims = []

        for claim_data in claims:
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
            "Claims verified and saved",
            extra={
                "project_id": str(project_id),
                "claims_saved": len(saved_claims),
            },
        )

        return saved_claims
