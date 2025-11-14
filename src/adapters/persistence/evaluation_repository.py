"""PostgreSQL evaluation repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.models.evaluation import Evaluation, ConceptGap, GapSeverity
from ...domain.ports.evaluation_repository_port import EvaluationRepositoryPort
from .models import EvaluationModel, EvaluationGapModel


class PostgreSQLEvaluationRepository(EvaluationRepositoryPort):
    """PostgreSQL implementation of evaluation repository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def save(self, evaluation: Evaluation) -> Evaluation:
        """Save evaluation with gaps."""
        # Convert domain model to database model
        db_model = self._to_db_model(evaluation)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)

        # Load gaps relationship
        await self.session.refresh(db_model, ["gaps"])

        return self._to_domain(db_model)

    async def get_by_id(self, evaluation_id: UUID) -> Evaluation | None:
        """Get evaluation by ID with gaps."""
        stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation_id)
        stmt = stmt.options(selectinload(EvaluationModel.gaps))
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()
        return self._to_domain(db_model) if db_model else None

    async def get_by_answer_id(self, answer_id: UUID) -> Evaluation | None:
        """Get evaluation for answer with gaps."""
        stmt = select(EvaluationModel).where(EvaluationModel.answer_id == answer_id)
        stmt = stmt.options(selectinload(EvaluationModel.gaps))
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()
        return self._to_domain(db_model) if db_model else None

    async def get_by_parent_evaluation_id(
        self, parent_id: UUID
    ) -> list[Evaluation]:
        """Get follow-up evaluations ordered by attempt_number."""
        stmt = (
            select(EvaluationModel)
            .where(EvaluationModel.parent_evaluation_id == parent_id)
            .options(selectinload(EvaluationModel.gaps))
            .order_by(EvaluationModel.attempt_number)
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def update(self, evaluation: Evaluation) -> Evaluation:
        """Update evaluation."""
        stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation.id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise ValueError(f"Evaluation {evaluation.id} not found")

        # Update fields
        db_model.raw_score = evaluation.raw_score
        db_model.penalty = evaluation.penalty
        db_model.final_score = evaluation.final_score
        db_model.similarity_score = evaluation.similarity_score
        db_model.completeness = evaluation.completeness
        db_model.relevance = evaluation.relevance
        db_model.sentiment = evaluation.sentiment
        db_model.reasoning = evaluation.reasoning
        db_model.strengths = evaluation.strengths
        db_model.weaknesses = evaluation.weaknesses
        db_model.improvement_suggestions = evaluation.improvement_suggestions
        db_model.attempt_number = evaluation.attempt_number
        db_model.parent_evaluation_id = evaluation.parent_evaluation_id
        db_model.evaluated_at = evaluation.evaluated_at

        # Update gaps (replace all)
        # Delete existing gaps
        await self.session.execute(
            select(EvaluationGapModel).where(
                EvaluationGapModel.evaluation_id == evaluation.id
            )
        )
        for gap_model in list(db_model.gaps):
            await self.session.delete(gap_model)

        # Add new gaps
        for gap in evaluation.gaps:
            gap_model = EvaluationGapModel(
                id=gap.id,
                evaluation_id=evaluation.id,
                concept=gap.concept,
                severity=gap.severity.value,
                resolved=gap.resolved,
                created_at=gap.created_at,
            )
            db_model.gaps.append(gap_model)

        await self.session.commit()
        await self.session.refresh(db_model, ["gaps"])
        return self._to_domain(db_model)

    async def delete(self, evaluation_id: UUID) -> None:
        """Delete evaluation (cascade deletes gaps)."""
        stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation_id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model:
            await self.session.delete(db_model)
            await self.session.commit()

    def _to_domain(self, db_model: EvaluationModel) -> Evaluation:
        """Convert database model to domain model."""
        gaps = [
            ConceptGap(
                id=gap.id,
                evaluation_id=gap.evaluation_id,
                concept=gap.concept,
                severity=GapSeverity(gap.severity),
                resolved=gap.resolved,
                created_at=gap.created_at,
            )
            for gap in db_model.gaps
        ]

        return Evaluation(
            id=db_model.id,
            answer_id=db_model.answer_id,
            question_id=db_model.question_id,
            interview_id=db_model.interview_id,
            raw_score=db_model.raw_score,
            penalty=db_model.penalty,
            final_score=db_model.final_score,
            similarity_score=db_model.similarity_score,
            completeness=db_model.completeness,
            relevance=db_model.relevance,
            sentiment=db_model.sentiment,
            reasoning=db_model.reasoning,
            strengths=list(db_model.strengths),
            weaknesses=list(db_model.weaknesses),
            improvement_suggestions=list(db_model.improvement_suggestions),
            attempt_number=db_model.attempt_number,
            parent_evaluation_id=db_model.parent_evaluation_id,
            gaps=gaps,
            created_at=db_model.created_at,
            evaluated_at=db_model.evaluated_at,
        )

    def _to_db_model(self, domain_model: Evaluation) -> EvaluationModel:
        """Convert domain model to database model."""
        gap_models = [
            EvaluationGapModel(
                id=gap.id,
                evaluation_id=domain_model.id,
                concept=gap.concept,
                severity=gap.severity.value,
                resolved=gap.resolved,
                created_at=gap.created_at,
            )
            for gap in domain_model.gaps
        ]

        return EvaluationModel(
            id=domain_model.id,
            answer_id=domain_model.answer_id,
            question_id=domain_model.question_id,
            interview_id=domain_model.interview_id,
            raw_score=domain_model.raw_score,
            penalty=domain_model.penalty,
            final_score=domain_model.final_score,
            similarity_score=domain_model.similarity_score,
            completeness=domain_model.completeness,
            relevance=domain_model.relevance,
            sentiment=domain_model.sentiment,
            reasoning=domain_model.reasoning,
            strengths=domain_model.strengths,
            weaknesses=domain_model.weaknesses,
            improvement_suggestions=domain_model.improvement_suggestions,
            attempt_number=domain_model.attempt_number,
            parent_evaluation_id=domain_model.parent_evaluation_id,
            gaps=gap_models,
            created_at=domain_model.created_at,
            evaluated_at=domain_model.evaluated_at,
        )
