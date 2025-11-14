"""PostgreSQL implementation of QuestionRepositoryPort."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.models.question import DifficultyLevel, Question, QuestionType
from ...domain.ports.question_repository_port import QuestionRepositoryPort
from .mappers import QuestionMapper
from .models import QuestionModel


class PostgreSQLQuestionRepository(QuestionRepositoryPort):
    """PostgreSQL implementation of question repository.

    This adapter implements the QuestionRepositoryPort interface
    using SQLAlchemy and PostgreSQL for persistence.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save(self, question: Question) -> Question:
        """Save a new question to the database."""
        db_model = QuestionMapper.to_db_model(question)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return QuestionMapper.to_domain(db_model)

    async def get_by_id(self, question_id: UUID) -> Question | None:
        """Retrieve a question by ID."""
        result = await self.session.execute(
            select(QuestionModel).where(QuestionModel.id == question_id)
        )
        db_model = result.scalar_one_or_none()
        return QuestionMapper.to_domain(db_model) if db_model else None

    async def get_by_ids(self, question_ids: list[UUID]) -> list[Question]:
        """Retrieve multiple questions by IDs."""
        result = await self.session.execute(
            select(QuestionModel).where(QuestionModel.id.in_(question_ids))
        )
        db_models = result.scalars().all()
        return [QuestionMapper.to_domain(db_model) for db_model in db_models]

    async def find_by_skill(
        self,
        skill: str,
        difficulty: DifficultyLevel | None = None,
        limit: int = 10,
    ) -> list[Question]:
        """Find questions by skill with optional difficulty filter."""
        query = select(QuestionModel).where(
            QuestionModel.skills.contains([skill])  # PostgreSQL array contains
        )

        if difficulty:
            query = query.where(QuestionModel.difficulty == difficulty.value)

        query = query.limit(limit)

        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [QuestionMapper.to_domain(db_model) for db_model in db_models]

    async def find_by_type(
        self,
        question_type: QuestionType,
        difficulty: DifficultyLevel | None = None,
        limit: int = 10,
    ) -> list[Question]:
        """Find questions by type with optional difficulty filter."""
        query = select(QuestionModel).where(
            QuestionModel.question_type == question_type.value
        )

        if difficulty:
            query = query.where(QuestionModel.difficulty == difficulty.value)

        query = query.limit(limit)

        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [QuestionMapper.to_domain(db_model) for db_model in db_models]

    async def find_by_tags(
        self,
        tags: list[str],
        match_all: bool = False,
        limit: int = 10,
    ) -> list[Question]:
        """Find questions by tags.

        Args:
            tags: List of tags to search for
            match_all: If True, match all tags; if False, match any tag
            limit: Maximum number of results
        """
        if match_all:
            # Match all tags (array contains all elements)
            query = select(QuestionModel).where(
                QuestionModel.tags.contains(tags)  # PostgreSQL @> operator
            )
        else:
            # Match any tag (array overlap)
            query = select(QuestionModel).where(
                QuestionModel.tags.overlap(tags)  # PostgreSQL && operator
            )

        query = query.limit(limit)

        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [QuestionMapper.to_domain(db_model) for db_model in db_models]

    async def update(self, question: Question) -> Question:
        """Update an existing question."""
        result = await self.session.execute(
            select(QuestionModel).where(QuestionModel.id == question.id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise ValueError(f"Question with id {question.id} not found")

        QuestionMapper.update_db_model(db_model, question)
        await self.session.commit()
        await self.session.refresh(db_model)
        return QuestionMapper.to_domain(db_model)

    async def delete(self, question_id: UUID) -> bool:
        """Delete a question by ID."""
        result = await self.session.execute(
            select(QuestionModel).where(QuestionModel.id == question_id)
        )
        db_model = result.scalar_one_or_none()

        if not db_model:
            return False

        await self.session.delete(db_model)
        await self.session.commit()
        return True

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Question]:
        """List all questions with pagination."""
        result = await self.session.execute(
            select(QuestionModel)
            .order_by(QuestionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        db_models = result.scalars().all()
        return [QuestionMapper.to_domain(db_model) for db_model in db_models]
