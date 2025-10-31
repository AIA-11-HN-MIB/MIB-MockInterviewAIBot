"""PostgreSQL implementation of CVAnalysisRepositoryPort."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.models.cv_analysis import CVAnalysis
from ...domain.ports.cv_analysis_repository_port import CVAnalysisRepositoryPort
from .models import CVAnalysisModel
from .mappers import CVAnalysisMapper


class PostgreSQLCVAnalysisRepository(CVAnalysisRepositoryPort):
    """PostgreSQL implementation of CV analysis repository.

    This adapter implements the CVAnalysisRepositoryPort interface
    using SQLAlchemy and PostgreSQL for persistence.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Save a new CV analysis to the database."""
        db_model = CVAnalysisMapper.to_db_model(cv_analysis)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return CVAnalysisMapper.to_domain(db_model)

    async def get_by_id(self, cv_analysis_id: UUID) -> Optional[CVAnalysis]:
        """Retrieve a CV analysis by ID."""
        result = await self.session.execute(
            select(CVAnalysisModel).where(CVAnalysisModel.id == cv_analysis_id)
        )
        db_model = result.scalar_one_or_none()
        return CVAnalysisMapper.to_domain(db_model) if db_model else None

    async def get_by_candidate_id(self, candidate_id: UUID) -> List[CVAnalysis]:
        """Retrieve all CV analyses for a candidate."""
        result = await self.session.execute(
            select(CVAnalysisModel)
            .where(CVAnalysisModel.candidate_id == candidate_id)
            .order_by(CVAnalysisModel.created_at.desc())
        )
        db_models = result.scalars().all()
        return [CVAnalysisMapper.to_domain(db_model) for db_model in db_models]

    async def get_latest_by_candidate_id(
        self,
        candidate_id: UUID,
    ) -> Optional[CVAnalysis]:
        """Retrieve the most recent CV analysis for a candidate."""
        result = await self.session.execute(
            select(CVAnalysisModel)
            .where(CVAnalysisModel.candidate_id == candidate_id)
            .order_by(CVAnalysisModel.created_at.desc())
            .limit(1)
        )
        db_model = result.scalar_one_or_none()
        return CVAnalysisMapper.to_domain(db_model) if db_model else None

    async def update(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Update an existing CV analysis."""
        result = await self.session.execute(
            select(CVAnalysisModel).where(CVAnalysisModel.id == cv_analysis.id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise ValueError(f"CV Analysis with id {cv_analysis.id} not found")

        CVAnalysisMapper.update_db_model(db_model, cv_analysis)
        await self.session.commit()
        await self.session.refresh(db_model)
        return CVAnalysisMapper.to_domain(db_model)

    async def delete(self, cv_analysis_id: UUID) -> bool:
        """Delete a CV analysis by ID."""
        result = await self.session.execute(
            select(CVAnalysisModel).where(CVAnalysisModel.id == cv_analysis_id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            return False

        await self.session.delete(db_model)
        await self.session.commit()
        return True
