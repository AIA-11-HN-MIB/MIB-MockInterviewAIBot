"""PostgreSQL implementation of CandidateRepositoryPort."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.models.candidate import Candidate
from ...domain.ports.candidate_repository_port import CandidateRepositoryPort
from .mappers import CandidateMapper
from .models import CandidateModel


class PostgreSQLCandidateRepository(CandidateRepositoryPort):
    """PostgreSQL implementation of candidate repository.

    This adapter implements the CandidateRepositoryPort interface
    using SQLAlchemy and PostgreSQL for persistence.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save(self, candidate: Candidate) -> Candidate:
        """Save a new candidate to the database."""
        db_model = CandidateMapper.to_db_model(candidate)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return CandidateMapper.to_domain(db_model)

    async def get_by_id(self, candidate_id: UUID) -> Candidate | None:
        """Retrieve a candidate by ID."""
        result = await self.session.execute(
            select(CandidateModel).where(CandidateModel.id == candidate_id)
        )
        db_model = result.scalar_one_or_none()
        return CandidateMapper.to_domain(db_model) if db_model else None

    async def get_by_email(self, email: str) -> Candidate | None:
        """Retrieve a candidate by email address."""
        result = await self.session.execute(
            select(CandidateModel).where(CandidateModel.email == email)
        )
        db_model = result.scalar_one_or_none()
        return CandidateMapper.to_domain(db_model) if db_model else None

    async def update(self, candidate: Candidate) -> Candidate:
        """Update an existing candidate."""
        result = await self.session.execute(
            select(CandidateModel).where(CandidateModel.id == candidate.id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise ValueError(f"Candidate with id {candidate.id} not found")

        CandidateMapper.update_db_model(db_model, candidate)
        await self.session.commit()
        await self.session.refresh(db_model)
        return CandidateMapper.to_domain(db_model)

    async def delete(self, candidate_id: UUID) -> bool:
        """Delete a candidate by ID."""
        result = await self.session.execute(
            select(CandidateModel).where(CandidateModel.id == candidate_id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            return False

        await self.session.delete(db_model)
        await self.session.commit()
        return True

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Candidate]:
        """List all candidates with pagination."""
        result = await self.session.execute(
            select(CandidateModel)
            .order_by(CandidateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        db_models = result.scalars().all()
        return [CandidateMapper.to_domain(db_model) for db_model in db_models]
