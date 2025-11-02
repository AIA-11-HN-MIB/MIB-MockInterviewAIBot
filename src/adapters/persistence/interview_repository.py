"""PostgreSQL implementation of InterviewRepositoryPort."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.models.interview import Interview, InterviewStatus
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from .mappers import InterviewMapper
from .models import InterviewModel


class PostgreSQLInterviewRepository(InterviewRepositoryPort):
    """PostgreSQL implementation of interview repository.

    This adapter implements the InterviewRepositoryPort interface
    using SQLAlchemy and PostgreSQL for persistence.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save(self, interview: Interview) -> Interview:
        """Save a new interview to the database."""
        db_model = InterviewMapper.to_db_model(interview)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return InterviewMapper.to_domain(db_model)

    async def get_by_id(self, interview_id: UUID) -> Interview | None:
        """Retrieve an interview by ID."""
        result = await self.session.execute(
            select(InterviewModel).where(InterviewModel.id == interview_id)
        )
        db_model = result.scalar_one_or_none()
        return InterviewMapper.to_domain(db_model) if db_model else None

    async def get_by_candidate_id(
        self,
        candidate_id: UUID,
        status: InterviewStatus | None = None,
    ) -> list[Interview]:
        """Retrieve interviews for a candidate with optional status filter."""
        query = select(InterviewModel).where(InterviewModel.candidate_id == candidate_id)

        if status:
            query = query.where(InterviewModel.status == status.value)

        query = query.order_by(InterviewModel.created_at.desc())

        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [InterviewMapper.to_domain(db_model) for db_model in db_models]

    async def get_by_status(
        self,
        status: InterviewStatus,
        limit: int = 100,
    ) -> list[Interview]:
        """Retrieve interviews by status."""
        result = await self.session.execute(
            select(InterviewModel)
            .where(InterviewModel.status == status.value)
            .order_by(InterviewModel.created_at.desc())
            .limit(limit)
        )
        db_models = result.scalars().all()
        return [InterviewMapper.to_domain(db_model) for db_model in db_models]

    async def update(self, interview: Interview) -> Interview:
        """Update an existing interview."""
        result = await self.session.execute(
            select(InterviewModel).where(InterviewModel.id == interview.id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise ValueError(f"Interview with id {interview.id} not found")

        InterviewMapper.update_db_model(db_model, interview)
        await self.session.commit()
        await self.session.refresh(db_model)
        return InterviewMapper.to_domain(db_model)

    async def delete(self, interview_id: UUID) -> bool:
        """Delete an interview by ID."""
        result = await self.session.execute(
            select(InterviewModel).where(InterviewModel.id == interview_id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            return False

        await self.session.delete(db_model)
        await self.session.commit()
        return True

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Interview]:
        """List all interviews with pagination."""
        result = await self.session.execute(
            select(InterviewModel)
            .order_by(InterviewModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        db_models = result.scalars().all()
        return [InterviewMapper.to_domain(db_model) for db_model in db_models]
