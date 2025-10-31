"""PostgreSQL implementation of AnswerRepositoryPort."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.models.answer import Answer
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from .models import AnswerModel
from .mappers import AnswerMapper


class PostgreSQLAnswerRepository(AnswerRepositoryPort):
    """PostgreSQL implementation of answer repository.

    This adapter implements the AnswerRepositoryPort interface
    using SQLAlchemy and PostgreSQL for persistence.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save(self, answer: Answer) -> Answer:
        """Save a new answer to the database."""
        db_model = AnswerMapper.to_db_model(answer)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return AnswerMapper.to_domain(db_model)

    async def get_by_id(self, answer_id: UUID) -> Optional[Answer]:
        """Retrieve an answer by ID."""
        result = await self.session.execute(
            select(AnswerModel).where(AnswerModel.id == answer_id)
        )
        db_model = result.scalar_one_or_none()
        return AnswerMapper.to_domain(db_model) if db_model else None

    async def get_by_ids(self, answer_ids: List[UUID]) -> List[Answer]:
        """Retrieve multiple answers by IDs."""
        result = await self.session.execute(
            select(AnswerModel).where(AnswerModel.id.in_(answer_ids))
        )
        db_models = result.scalars().all()
        return [AnswerMapper.to_domain(db_model) for db_model in db_models]

    async def get_by_interview_id(self, interview_id: UUID) -> List[Answer]:
        """Retrieve all answers for an interview."""
        result = await self.session.execute(
            select(AnswerModel)
            .where(AnswerModel.interview_id == interview_id)
            .order_by(AnswerModel.created_at.asc())
        )
        db_models = result.scalars().all()
        return [AnswerMapper.to_domain(db_model) for db_model in db_models]

    async def get_by_question_id(self, question_id: UUID) -> List[Answer]:
        """Retrieve all answers for a question."""
        result = await self.session.execute(
            select(AnswerModel)
            .where(AnswerModel.question_id == question_id)
            .order_by(AnswerModel.created_at.desc())
        )
        db_models = result.scalars().all()
        return [AnswerMapper.to_domain(db_model) for db_model in db_models]

    async def get_by_candidate_id(self, candidate_id: UUID) -> List[Answer]:
        """Retrieve all answers by a candidate."""
        result = await self.session.execute(
            select(AnswerModel)
            .where(AnswerModel.candidate_id == candidate_id)
            .order_by(AnswerModel.created_at.desc())
        )
        db_models = result.scalars().all()
        return [AnswerMapper.to_domain(db_model) for db_model in db_models]

    async def update(self, answer: Answer) -> Answer:
        """Update an existing answer."""
        result = await self.session.execute(
            select(AnswerModel).where(AnswerModel.id == answer.id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise ValueError(f"Answer with id {answer.id} not found")

        AnswerMapper.update_db_model(db_model, answer)
        await self.session.commit()
        await self.session.refresh(db_model)
        return AnswerMapper.to_domain(db_model)

    async def delete(self, answer_id: UUID) -> bool:
        """Delete an answer by ID."""
        result = await self.session.execute(
            select(AnswerModel).where(AnswerModel.id == answer_id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            return False

        await self.session.delete(db_model)
        await self.session.commit()
        return True
