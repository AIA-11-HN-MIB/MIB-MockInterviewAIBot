# Follow-Up Question Evaluation Refactoring Implementation Plan

**Date**: 2025-11-14
**Version**: 1.0
**Estimated Effort**: 9 hours (Phase 1: 6h, Phase 2: 3h)
**Risk Level**: Medium

---

## Executive Summary

Implement Phase 1 (evaluations table migration) and Phase 2 (context-aware evaluation with penalties) of follow-up question evaluation refactoring. Extract evaluation data from embedded JSONB in `answers` table to dedicated `evaluations` + `evaluation_gaps` tables, enabling context-aware follow-up evaluation with attempt-based penalties.

**Current Bug**: `ProcessAnswerAdaptiveUseCase` crashes when `question_id` is follow-up (looks in `questions` table instead of `follow_up_questions`).

**Solution**: Separate `Evaluation` entity + context-aware LLM evaluation with gap tracking + penalty progression (0/-5/-15).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Phase 1: Evaluations Table Migration](#phase-2-evaluations-table-migration)
3. [Phase 2: Context-Aware Evaluation](#phase-3-context-aware-evaluation)
4. [Migration Strategy](#migration-strategy)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Checklist](#deployment-checklist)
7. [Risk Assessment](#risk-assessment)
8. [Appendix](#appendix)

---

## Architecture Overview

### Current State (Problems)

**Database Schema**:
```sql
-- answers table (current)
answers {
  evaluation JSONB,          -- Embedded AnswerEvaluation object
  similarity_score FLOAT,    -- Cosine similarity (0-1)
  gaps JSONB                 -- {concepts: [], keywords: [], confirmed: bool}
}
```

**Problems**:
- **P1**: Evaluation data tightly coupled to Answer entity (violates SRP)
- **P2**: Cannot track evaluation attempts/penalties independently
- **P3**: No gap resolution tracking across follow-ups
- **P4**: Context-blind evaluation (doesn't know attempt number)
- **P5**: ProcessAnswerAdaptiveUseCase looks up follow-ups in wrong repo (crashes)

### Target State (Solution)

**Database Schema**:
```sql
-- evaluations table (NEW)
evaluations {
  id UUID PRIMARY KEY,
  answer_id UUID REFERENCES answers(id),
  question_id UUID REFERENCES questions(id),  -- Main or follow-up
  interview_id UUID REFERENCES interviews(id),

  -- Scores
  raw_score FLOAT,           -- LLM score (0-100)
  penalty FLOAT,             -- Attempt penalty (0/-5/-15)
  final_score FLOAT,         -- raw_score + penalty
  similarity_score FLOAT,    -- Cosine similarity (0-1)

  -- LLM evaluation
  completeness FLOAT,
  relevance FLOAT,
  sentiment VARCHAR(50),
  reasoning TEXT,
  strengths TEXT[],
  weaknesses TEXT[],
  improvement_suggestions TEXT[],

  -- Context
  attempt_number INT,        -- 1, 2, or 3
  parent_evaluation_id UUID REFERENCES evaluations(id),  -- NULL if main question

  created_at TIMESTAMP,
  evaluated_at TIMESTAMP
}

-- evaluation_gaps table (NEW)
evaluation_gaps {
  id UUID PRIMARY KEY,
  evaluation_id UUID REFERENCES evaluations(id),
  concept TEXT,              -- Missing concept
  severity VARCHAR(20),      -- minor/moderate/major
  resolved BOOLEAN,          -- Filled in follow-up?
  created_at TIMESTAMP
}

-- answers table (UPDATED)
answers {
  -- REMOVE: evaluation JSONB
  -- REMOVE: similarity_score FLOAT
  -- REMOVE: gaps JSONB

  -- KEEP: all other fields
}
```

**Domain Models**:
```python
# NEW: Evaluation entity
class Evaluation(BaseModel):
    id: UUID
    answer_id: UUID
    question_id: UUID  # Main or follow-up
    interview_id: UUID

    raw_score: float  # 0-100
    penalty: float    # 0/-5/-15
    final_score: float
    similarity_score: float | None

    completeness: float
    relevance: float
    sentiment: str | None
    reasoning: str | None
    strengths: list[str]
    weaknesses: list[str]
    improvement_suggestions: list[str]

    attempt_number: int  # 1, 2, or 3
    parent_evaluation_id: UUID | None  # NULL if main question

    gaps: list[ConceptGap] = []  # Relationship to gaps

    created_at: datetime
    evaluated_at: datetime | None

# NEW: ConceptGap value object
class ConceptGap(BaseModel):
    id: UUID
    evaluation_id: UUID
    concept: str
    severity: str  # minor/moderate/major
    resolved: bool
    created_at: datetime

# UPDATED: Answer (remove evaluation fields)
class Answer(BaseModel):
    # REMOVE: evaluation: AnswerEvaluation | None
    # REMOVE: similarity_score: float | None
    # REMOVE: gaps: dict[str, Any] | None

    # ADD: relationship to evaluation (1:1)
    evaluation_id: UUID | None  # FK to evaluations

    # KEEP: all other fields unchanged
```

**LLM Adapter Changes** (Phase 2):
```python
# NEW: Follow-up evaluation context
@dataclass
class FollowUpEvaluationContext:
    attempt_number: int          # 1, 2, or 3
    parent_question_id: UUID
    cumulative_gaps: list[str]   # All gaps from previous attempts
    previous_evaluations: list[dict]  # Previous attempt results

# UPDATED: LLMPort
class LLMPort(ABC):
    @abstractmethod
    async def evaluate_answer(
        question: Question,
        answer_text: str,
        context: dict[str, Any],
        followup_context: FollowUpEvaluationContext | None = None,  # NEW
    ) -> AnswerEvaluation:
        """Evaluate with optional follow-up context for penalties."""
```

### Penalty Logic (Phase 2)

**Attempt-Based Penalties**:
- **1st attempt** (main question): penalty = 0
- **2nd attempt** (1st follow-up): penalty = -5
- **3rd attempt** (2nd follow-up): penalty = -15
- **4th+ attempt**: NOT ALLOWED (max 3 follow-ups)

**Final Score Calculation**:
```python
final_score = max(0, raw_score + penalty)  # Clamp to [0, 100]
```

**Gap Resolution Tracking**:
```python
# Mark gaps as resolved when:
- completeness >= 0.8 OR
- final_score >= 80 OR
- attempt_number == 3 (max reached)
```

---

## Phase 1: Evaluations Table Migration

**Duration**: 6 hours
**Dependencies**: None
**Risk**: Medium (data migration)

### 2.1 Database Migration

**File**: `alembic/versions/0003_create_evaluations_tables.py`

**Schema Changes**:
```sql
-- Step 1: Create evaluations table
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    answer_id UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    question_id UUID NOT NULL,  -- No FK (can be main or follow-up)
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,

    raw_score FLOAT NOT NULL CHECK (raw_score >= 0 AND raw_score <= 100),
    penalty FLOAT NOT NULL DEFAULT 0 CHECK (penalty >= -15 AND penalty <= 0),
    final_score FLOAT NOT NULL CHECK (final_score >= 0 AND final_score <= 100),
    similarity_score FLOAT CHECK (similarity_score >= 0 AND similarity_score <= 1),

    completeness FLOAT NOT NULL CHECK (completeness >= 0 AND completeness <= 1),
    relevance FLOAT NOT NULL CHECK (relevance >= 0 AND relevance <= 1),
    sentiment VARCHAR(50),
    reasoning TEXT,
    strengths TEXT[],
    weaknesses TEXT[],
    improvement_suggestions TEXT[],

    attempt_number INT NOT NULL DEFAULT 1 CHECK (attempt_number >= 1 AND attempt_number <= 3),
    parent_evaluation_id UUID REFERENCES evaluations(id) ON DELETE SET NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    evaluated_at TIMESTAMP
);

CREATE INDEX idx_evaluations_answer_id ON evaluations(answer_id);
CREATE INDEX idx_evaluations_question_id ON evaluations(question_id);
CREATE INDEX idx_evaluations_interview_id ON evaluations(interview_id);
CREATE INDEX idx_evaluations_parent_id ON evaluations(parent_evaluation_id);
CREATE INDEX idx_evaluations_attempt_number ON evaluations(attempt_number);

-- Step 2: Create evaluation_gaps table
CREATE TABLE evaluation_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    concept TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('minor', 'moderate', 'major')),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evaluation_gaps_evaluation_id ON evaluation_gaps(evaluation_id);
CREATE INDEX idx_evaluation_gaps_resolved ON evaluation_gaps(resolved);

-- Step 3: Add FK to answers table
ALTER TABLE answers ADD COLUMN evaluation_id UUID REFERENCES evaluations(id) ON DELETE SET NULL;
CREATE INDEX idx_answers_evaluation_id ON answers(evaluation_id);

-- Step 4: Migrate existing data
-- This SQL migrates embedded JSONB data to new tables
INSERT INTO evaluations (
    id, answer_id, question_id, interview_id,
    raw_score, penalty, final_score, similarity_score,
    completeness, relevance, sentiment, reasoning,
    strengths, weaknesses, improvement_suggestions,
    attempt_number, parent_evaluation_id,
    created_at, evaluated_at
)
SELECT
    gen_random_uuid(),
    a.id,
    a.question_id,
    a.interview_id,

    (a.evaluation->>'score')::FLOAT,  -- raw_score
    0,  -- penalty (always 0 for old data)
    (a.evaluation->>'score')::FLOAT,  -- final_score = raw_score
    a.similarity_score,

    (a.evaluation->>'completeness')::FLOAT,
    (a.evaluation->>'relevance')::FLOAT,
    a.evaluation->>'sentiment',
    a.evaluation->>'reasoning',

    ARRAY(SELECT jsonb_array_elements_text(a.evaluation->'strengths'))::TEXT[],
    ARRAY(SELECT jsonb_array_elements_text(a.evaluation->'weaknesses'))::TEXT[],
    ARRAY(SELECT jsonb_array_elements_text(a.evaluation->'improvement_suggestions'))::TEXT[],

    1,  -- attempt_number (assume main question)
    NULL,  -- parent_evaluation_id

    a.created_at,
    a.evaluated_at
FROM answers a
WHERE a.evaluation IS NOT NULL;

-- Migrate gaps
INSERT INTO evaluation_gaps (evaluation_id, concept, severity, resolved)
SELECT
    e.id,
    jsonb_array_elements_text(a.gaps->'concepts'),
    COALESCE(a.gaps->>'severity', 'moderate'),
    FALSE  -- Not resolved (old data)
FROM answers a
JOIN evaluations e ON e.answer_id = a.id
WHERE a.gaps IS NOT NULL
  AND a.gaps->'concepts' IS NOT NULL
  AND jsonb_array_length(a.gaps->'concepts') > 0;

-- Update FK references
UPDATE answers a
SET evaluation_id = e.id
FROM evaluations e
WHERE e.answer_id = a.id;

-- Step 5: Drop old columns (after verification)
ALTER TABLE answers DROP COLUMN evaluation;
ALTER TABLE answers DROP COLUMN similarity_score;
ALTER TABLE answers DROP COLUMN gaps;
```

**Downgrade**:
```sql
-- Recreate old columns
ALTER TABLE answers ADD COLUMN evaluation JSONB;
ALTER TABLE answers ADD COLUMN similarity_score FLOAT;
ALTER TABLE answers ADD COLUMN gaps JSONB;

-- Migrate back
UPDATE answers a
SET
    evaluation = jsonb_build_object(
        'score', e.raw_score,
        'completeness', e.completeness,
        'relevance', e.relevance,
        'sentiment', e.sentiment,
        'reasoning', e.reasoning,
        'strengths', to_jsonb(e.strengths),
        'weaknesses', to_jsonb(e.weaknesses),
        'improvement_suggestions', to_jsonb(e.improvement_suggestions)
    ),
    similarity_score = e.similarity_score,
    gaps = (
        SELECT jsonb_build_object(
            'concepts', jsonb_agg(g.concept),
            'severity', MIN(g.severity),
            'confirmed', BOOL_OR(NOT g.resolved)
        )
        FROM evaluation_gaps g
        WHERE g.evaluation_id = e.id
    )
FROM evaluations e
WHERE e.answer_id = a.id;

-- Drop new tables
ALTER TABLE answers DROP COLUMN evaluation_id;
DROP TABLE evaluation_gaps;
DROP TABLE evaluations;
```

### 2.2 Domain Models

**File**: `src/domain/models/evaluation.py` (NEW)

```python
"""Evaluation domain model."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class GapSeverity(str, Enum):
    """Concept gap severity levels."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


class ConceptGap(BaseModel):
    """Represents a missing concept in an answer.

    Value object - identified by evaluation_id + concept.
    """
    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID
    concept: str  # Missing concept (e.g., "event loop", "closure")
    severity: GapSeverity
    resolved: bool = False  # True if filled in follow-up
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True  # Immutable


class Evaluation(BaseModel):
    """Represents evaluation of an answer.

    Entity - tracks scoring, gaps, and penalties across follow-up attempts.
    """
    id: UUID = Field(default_factory=uuid4)
    answer_id: UUID
    question_id: UUID  # Main question OR follow-up question
    interview_id: UUID

    # Scores
    raw_score: float = Field(ge=0.0, le=100.0)  # LLM score before penalty
    penalty: float = Field(ge=-15.0, le=0.0, default=0.0)  # Attempt penalty
    final_score: float = Field(ge=0.0, le=100.0)  # raw_score + penalty
    similarity_score: float | None = Field(None, ge=0.0, le=1.0)  # Cosine similarity

    # LLM evaluation details
    completeness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    sentiment: str | None = None  # confident/uncertain/nervous
    reasoning: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)

    # Follow-up context
    attempt_number: int = Field(ge=1, le=3, default=1)  # 1 (main), 2-3 (follow-ups)
    parent_evaluation_id: UUID | None = None  # NULL if main question

    # Gaps (relationship)
    gaps: list[ConceptGap] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluated_at: datetime | None = None

    class Config:
        frozen = False

    def apply_penalty(self, attempt_number: int) -> None:
        """Apply penalty based on attempt number.

        Penalty progression: 0 (1st) / -5 (2nd) / -15 (3rd)

        Args:
            attempt_number: 1, 2, or 3
        """
        if attempt_number == 1:
            self.penalty = 0.0
        elif attempt_number == 2:
            self.penalty = -5.0
        elif attempt_number == 3:
            self.penalty = -15.0
        else:
            raise ValueError(f"Invalid attempt_number: {attempt_number} (must be 1-3)")

        self.attempt_number = attempt_number
        self.final_score = max(0.0, self.raw_score + self.penalty)

    def has_gaps(self) -> bool:
        """Check if unresolved gaps exist."""
        return any(not gap.resolved for gap in self.gaps)

    def resolve_gaps(self) -> None:
        """Mark all gaps as resolved."""
        for gap in self.gaps:
            gap.resolved = True

    def is_passing(self, threshold: float = 60.0) -> bool:
        """Check if final score meets threshold."""
        return self.final_score >= threshold
```

**File**: `src/domain/models/answer.py` (UPDATE)

```python
# REMOVE these fields:
# evaluation: AnswerEvaluation | None = None
# similarity_score: float | None = None
# gaps: dict[str, Any] | None = None

# ADD:
evaluation_id: UUID | None = None  # FK to evaluations table

# REMOVE methods:
# - evaluate()
# - has_gaps()
# - meets_threshold()
# - is_adaptive_complete()

# KEEP:
# - is_evaluated() -> check evaluation_id is not None
# - get_score() -> fetch from evaluation repository
```

### 2.3 Repository Ports & Adapters

**File**: `src/domain/ports/evaluation_repository_port.py` (NEW)

```python
"""Evaluation repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models.evaluation import Evaluation


class EvaluationRepositoryPort(ABC):
    """Interface for evaluation persistence."""

    @abstractmethod
    async def save(self, evaluation: Evaluation) -> Evaluation:
        """Save evaluation with gaps."""

    @abstractmethod
    async def get_by_id(self, evaluation_id: UUID) -> Evaluation | None:
        """Get evaluation by ID."""

    @abstractmethod
    async def get_by_answer_id(self, answer_id: UUID) -> Evaluation | None:
        """Get evaluation for answer (1:1 relationship)."""

    @abstractmethod
    async def get_by_parent_evaluation_id(
        self, parent_id: UUID
    ) -> list[Evaluation]:
        """Get follow-up evaluations for parent."""

    @abstractmethod
    async def update(self, evaluation: Evaluation) -> Evaluation:
        """Update evaluation."""

    @abstractmethod
    async def delete(self, evaluation_id: UUID) -> None:
        """Delete evaluation."""
```

**File**: `src/adapters/persistence/models.py` (UPDATE)

```python
# ADD new models
class EvaluationModel(Base):
    __tablename__ = "evaluations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    answer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("answers.id", ondelete="CASCADE"),
        nullable=False
    )
    question_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    interview_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False
    )

    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    penalty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    completeness: Mapped[float] = mapped_column(Float, nullable=False)
    relevance: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=[])
    weaknesses: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=[])
    improvement_suggestions: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=[])

    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_evaluation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    gaps: Mapped[list["EvaluationGapModel"]] = relationship(
        "EvaluationGapModel",
        back_populates="evaluation",
        cascade="all, delete-orphan"
    )


class EvaluationGapModel(Base):
    __tablename__ = "evaluation_gaps"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    evaluation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False
    )
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    evaluation: Mapped["EvaluationModel"] = relationship(
        "EvaluationModel",
        back_populates="gaps"
    )


# UPDATE AnswerModel
class AnswerModel(Base):
    # REMOVE:
    # evaluation: Mapped[dict | None] = ...
    # similarity_score: Mapped[float | None] = ...
    # gaps: Mapped[dict | None] = ...

    # ADD:
    evaluation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="SET NULL"),
        nullable=True
    )

    # ADD relationship
    evaluation: Mapped["EvaluationModel | None"] = relationship(
        "EvaluationModel",
        foreign_keys=[evaluation_id]
    )
```

**File**: `src/adapters/persistence/evaluation_repository.py` (NEW)

```python
"""PostgreSQL evaluation repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.models.evaluation import Evaluation
from ...domain.ports.evaluation_repository_port import EvaluationRepositoryPort
from .mappers import EvaluationMapper
from .models import EvaluationModel


class PostgreSQLEvaluationRepository(EvaluationRepositoryPort):
    """PostgreSQL implementation of evaluation repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, evaluation: Evaluation) -> Evaluation:
        """Save evaluation with gaps."""
        db_model = EvaluationMapper.to_db_model(evaluation)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return EvaluationMapper.to_domain(db_model)

    async def get_by_id(self, evaluation_id: UUID) -> Evaluation | None:
        """Get evaluation by ID."""
        stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation_id)
        stmt = stmt.options(selectinload(EvaluationModel.gaps))
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()
        return EvaluationMapper.to_domain(db_model) if db_model else None

    async def get_by_answer_id(self, answer_id: UUID) -> Evaluation | None:
        """Get evaluation for answer."""
        stmt = select(EvaluationModel).where(EvaluationModel.answer_id == answer_id)
        stmt = stmt.options(selectinload(EvaluationModel.gaps))
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()
        return EvaluationMapper.to_domain(db_model) if db_model else None

    async def get_by_parent_evaluation_id(
        self, parent_id: UUID
    ) -> list[Evaluation]:
        """Get follow-up evaluations."""
        stmt = select(EvaluationModel).where(
            EvaluationModel.parent_evaluation_id == parent_id
        )
        stmt = stmt.options(selectinload(EvaluationModel.gaps))
        result = await self.session.execute(stmt)
        return [EvaluationMapper.to_domain(row) for row in result.scalars().all()]

    async def update(self, evaluation: Evaluation) -> Evaluation:
        """Update evaluation."""
        stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation.id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise ValueError(f"Evaluation {evaluation.id} not found")

        EvaluationMapper.update_db_model(db_model, evaluation)
        await self.session.commit()
        await self.session.refresh(db_model)
        return EvaluationMapper.to_domain(db_model)

    async def delete(self, evaluation_id: UUID) -> None:
        """Delete evaluation."""
        stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation_id)
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model:
            await self.session.delete(db_model)
            await self.session.commit()
```

**File**: `src/adapters/persistence/mappers.py` (UPDATE)

```python
# ADD EvaluationMapper
class EvaluationMapper:
    """Mapper for Evaluation domain model."""

    @staticmethod
    def to_domain(db_model: EvaluationModel) -> Evaluation:
        """Convert database model to domain model."""
        gaps = [
            ConceptGap(
                id=gap.id,
                evaluation_id=gap.evaluation_id,
                concept=gap.concept,
                severity=GapSeverity(gap.severity),
                resolved=gap.resolved,
                created_at=gap.created_at
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
            evaluated_at=db_model.evaluated_at
        )

    @staticmethod
    def to_db_model(domain_model: Evaluation) -> EvaluationModel:
        """Convert domain model to database model."""
        gap_models = [
            EvaluationGapModel(
                id=gap.id,
                evaluation_id=domain_model.id,
                concept=gap.concept,
                severity=gap.severity.value,
                resolved=gap.resolved,
                created_at=gap.created_at
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
            evaluated_at=domain_model.evaluated_at
        )

    @staticmethod
    def update_db_model(db_model: EvaluationModel, domain_model: Evaluation) -> None:
        """Update database model from domain model."""
        db_model.raw_score = domain_model.raw_score
        db_model.penalty = domain_model.penalty
        db_model.final_score = domain_model.final_score
        db_model.similarity_score = domain_model.similarity_score
        db_model.completeness = domain_model.completeness
        db_model.relevance = domain_model.relevance
        db_model.sentiment = domain_model.sentiment
        db_model.reasoning = domain_model.reasoning
        db_model.strengths = domain_model.strengths
        db_model.weaknesses = domain_model.weaknesses
        db_model.improvement_suggestions = domain_model.improvement_suggestions
        db_model.attempt_number = domain_model.attempt_number
        db_model.parent_evaluation_id = domain_model.parent_evaluation_id
        db_model.evaluated_at = domain_model.evaluated_at

        # Update gaps (replace all)
        db_model.gaps.clear()
        for gap in domain_model.gaps:
            db_model.gaps.append(
                EvaluationGapModel(
                    id=gap.id,
                    evaluation_id=domain_model.id,
                    concept=gap.concept,
                    severity=gap.severity.value,
                    resolved=gap.resolved,
                    created_at=gap.created_at
                )
            )

# UPDATE AnswerMapper
class AnswerMapper:
    @staticmethod
    def to_domain(db_model: AnswerModel) -> Answer:
        """Convert database model to domain model."""
        return Answer(
            id=db_model.id,
            interview_id=db_model.interview_id,
            question_id=db_model.question_id,
            candidate_id=db_model.candidate_id,
            text=db_model.text,
            is_voice=db_model.is_voice,
            audio_file_path=db_model.audio_file_path,
            duration_seconds=db_model.duration_seconds,
            embedding=list(db_model.embedding) if db_model.embedding else None,
            metadata=dict(db_model.answer_metadata) if db_model.answer_metadata else {},
            evaluation_id=db_model.evaluation_id,  # NEW
            created_at=db_model.created_at,
        )

    @staticmethod
    def to_db_model(domain_model: Answer) -> AnswerModel:
        """Convert domain model to database model."""
        return AnswerModel(
            id=domain_model.id,
            interview_id=domain_model.interview_id,
            question_id=domain_model.question_id,
            candidate_id=domain_model.candidate_id,
            text=domain_model.text,
            is_voice=domain_model.is_voice,
            audio_file_path=domain_model.audio_file_path,
            duration_seconds=domain_model.duration_seconds,
            embedding=domain_model.embedding,
            answer_metadata=domain_model.metadata,
            evaluation_id=domain_model.evaluation_id,  # NEW
            created_at=domain_model.created_at,
        )
```

### 2.4 Update DI Container

**File**: `src/infrastructure/dependency_injection/container.py` (UPDATE)

```python
# ADD import
from ...adapters.persistence import PostgreSQLEvaluationRepository
from ...domain.ports import EvaluationRepositoryPort

class Container:
    # ADD method
    def evaluation_repository_port(
        self, session: AsyncSession
    ) -> EvaluationRepositoryPort:
        """Get evaluation repository."""
        return PostgreSQLEvaluationRepository(session)
```

### 2.5 Update Use Cases

**File**: `src/application/use_cases/process_answer_adaptive.py` (UPDATE)

```python
# UPDATE imports
from ...domain.models.evaluation import Evaluation, ConceptGap, GapSeverity
from ...domain.ports.evaluation_repository_port import EvaluationRepositoryPort

class ProcessAnswerAdaptiveUseCase:
    def __init__(
        self,
        answer_repository: AnswerRepositoryPort,
        evaluation_repository: EvaluationRepositoryPort,  # NEW
        interview_repository: InterviewRepositoryPort,
        question_repository: QuestionRepositoryPort,
        follow_up_question_repository: FollowUpQuestionRepositoryPort,
        llm: LLMPort,
        vector_search: VectorSearchPort,
        combine_evaluation: CombineEvaluationUseCase | None = None,
    ):
        self.answer_repo = answer_repository
        self.evaluation_repo = evaluation_repository  # NEW
        # ... rest

    async def execute(
        self,
        interview_id: UUID,
        question_id: UUID,
        answer_text: str,
        audio_file_path: str | None = None,
        voice_metrics: dict[str, float] | None = None,
    ) -> tuple[Answer, Evaluation, bool]:  # UPDATED return type
        """Process answer with adaptive evaluation.

        Returns:
            Tuple of (Answer, Evaluation, has_more_questions)
        """
        # ... existing validation ...

        # Step 3: Create answer (WITHOUT evaluation fields)
        answer = Answer(
            interview_id=interview_id,
            question_id=question_id,
            candidate_id=interview.candidate_id,
            text=answer_text,
            is_voice=bool(audio_file_path),
            audio_file_path=audio_file_path,
            # REMOVE: similarity_score, gaps, evaluation
            created_at=datetime.utcnow(),
        )

        # Step 4: Evaluate answer using LLM (Phase 2 will add context)
        llm_eval = await self.llm.evaluate_answer(
            question=question,
            answer_text=answer_text,
            context={
                "interview_id": str(interview_id),
                "candidate_id": str(interview.candidate_id),
            },
        )

        # Step 5: Calculate similarity (if ideal_answer exists)
        similarity_score = None
        if question.has_ideal_answer():
            similarity_score = await self._calculate_similarity(
                answer_text, question.ideal_answer
            )

        # Step 6: Detect gaps
        gaps_dict = await self._detect_gaps_hybrid(
            answer_text=answer_text,
            ideal_answer=question.ideal_answer or "",
            question_text=question.text,
        )

        # Step 7: Create Evaluation entity
        evaluation = Evaluation(
            answer_id=answer.id,
            question_id=question_id,
            interview_id=interview_id,
            raw_score=llm_eval.score,
            penalty=0.0,  # Phase 2 will add penalty logic
            final_score=llm_eval.score,
            similarity_score=similarity_score,
            completeness=llm_eval.completeness,
            relevance=llm_eval.relevance,
            sentiment=llm_eval.sentiment,
            reasoning=llm_eval.reasoning,
            strengths=llm_eval.strengths,
            weaknesses=llm_eval.weaknesses,
            improvement_suggestions=llm_eval.improvement_suggestions,
            attempt_number=1,  # Phase 2 will determine from context
            parent_evaluation_id=None,  # Phase 2 will link follow-ups
            gaps=[
                ConceptGap(
                    evaluation_id=answer.id,  # Will be set after save
                    concept=concept,
                    severity=GapSeverity(gaps_dict.get("severity", "moderate")),
                    resolved=False
                )
                for concept in gaps_dict.get("concepts", [])
            ],
            evaluated_at=datetime.utcnow()
        )

        # Step 8: Save evaluation
        saved_evaluation = await self.evaluation_repo.save(evaluation)

        # Step 9: Update answer with evaluation_id
        answer.evaluation_id = saved_evaluation.id
        saved_answer = await self.answer_repo.save(answer)

        # Step 10: Update interview
        interview.add_answer(saved_answer.id)
        await self.interview_repo.update(interview)

        has_more = interview.has_more_questions()

        return saved_answer, saved_evaluation, has_more
```

---

## Phase 2: Context-Aware Evaluation

**Duration**: 3 hours
**Dependencies**: Phase 1 complete
**Risk**: Low (additive changes)

### 3.1 Follow-Up Evaluation Context

**File**: `src/domain/models/evaluation.py` (UPDATE)

```python
from dataclasses import dataclass

@dataclass
class FollowUpEvaluationContext:
    """Context for evaluating follow-up answers.

    Provides LLM with full history to apply penalties and track gaps.
    """
    attempt_number: int  # 2 or 3 (1st/2nd follow-up)
    parent_question_id: UUID
    parent_evaluation_id: UUID
    cumulative_gaps: list[str]  # All unresolved gaps from previous attempts
    previous_evaluations: list[dict]  # Previous evaluation summaries
```

### 3.2 Update LLMPort

**File**: `src/domain/ports/llm_port.py` (UPDATE)

```python
from ..models.evaluation import FollowUpEvaluationContext

class LLMPort(ABC):
    @abstractmethod
    async def evaluate_answer(
        self,
        question: Question,
        answer_text: str,
        context: dict[str, Any],
        followup_context: FollowUpEvaluationContext | None = None,  # NEW
    ) -> AnswerEvaluation:
        """Evaluate answer with optional follow-up context.

        Args:
            question: Question being answered
            answer_text: Candidate's answer
            context: General context (interview_id, candidate_id)
            followup_context: Follow-up context with attempt number and gaps

        Returns:
            AnswerEvaluation (raw score, no penalty applied yet)
        """
```

### 3.3 Update LLM Adapters

**File**: `src/adapters/llm/openai_adapter.py` (UPDATE)

```python
async def evaluate_answer(
    self,
    question: Question,
    answer_text: str,
    context: dict[str, Any],
    followup_context: FollowUpEvaluationContext | None = None,  # NEW
) -> AnswerEvaluation:
    """Evaluate answer using OpenAI with follow-up context."""

    system_prompt = """You are an expert technical interviewer evaluating candidate answers.
    Provide objective, constructive feedback with specific scores."""

    user_prompt = f"""
    Question: {question.text}
    Question Type: {question.question_type}
    Difficulty: {question.difficulty}
    Expected Skills: {', '.join(question.skills)}

    Candidate's Answer: {answer_text}

    {"Ideal Answer: " + question.ideal_answer if question.ideal_answer else ""}
    """

    # ADD follow-up context
    if followup_context:
        user_prompt += f"""

        FOLLOW-UP CONTEXT:
        - This is attempt #{followup_context.attempt_number} (penalty will be -5 or -15)
        - Parent Question ID: {followup_context.parent_question_id}
        - Previous Missing Concepts: {', '.join(followup_context.cumulative_gaps)}

        Evaluate how well this answer addresses the missing concepts from previous attempts.
        Focus scoring on gap resolution and concept clarity.
        """

    user_prompt += """

    Evaluate this answer and provide:
    1. Overall score (0-100) - RAW score before penalties
    2. Completeness score (0-1)
    3. Relevance score (0-1)
    4. Sentiment (confident/uncertain/nervous)
    5. 2-3 strengths
    6. 2-3 weaknesses
    7. 2-3 improvement suggestions
    8. Brief reasoning for the score

    Return as JSON with keys: score, completeness, relevance, sentiment, strengths, weaknesses, improvements, reasoning
    """

    response = await self.client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    result = json.loads(content)

    return AnswerEvaluation(
        score=float(result.get("score", 0)),  # RAW score
        semantic_similarity=0.0,
        completeness=float(result.get("completeness", 0)),
        relevance=float(result.get("relevance", 0)),
        sentiment=result.get("sentiment"),
        reasoning=result.get("reasoning"),
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        improvement_suggestions=result.get("improvements", []),
    )
```

**File**: `src/adapters/llm/azure_openai_adapter.py` (UPDATE)

```python
# SAME changes as OpenAIAdapter above
# Add followup_context parameter and prompt augmentation
```

**File**: `src/adapters/mock/mock_llm_adapter.py` (UPDATE)

```python
# ADD followup_context parameter (optional)
async def evaluate_answer(
    self,
    question: Question,
    answer_text: str,
    context: dict[str, Any],
    followup_context: FollowUpEvaluationContext | None = None,
) -> AnswerEvaluation:
    """Mock evaluation with follow-up penalty simulation."""

    # Base score
    base_score = 75.0

    # Simulate penalty awareness in mock
    if followup_context:
        # Lower score for follow-ups (simulate gap-focused evaluation)
        if followup_context.attempt_number == 2:
            base_score = 70.0
        elif followup_context.attempt_number == 3:
            base_score = 65.0

    return AnswerEvaluation(
        score=base_score,
        semantic_similarity=0.0,
        completeness=0.8,
        relevance=0.85,
        sentiment="confident",
        reasoning="Mock evaluation",
        strengths=["Clear explanation"],
        weaknesses=["Could expand on examples"],
        improvement_suggestions=["Add more detail"],
    )
```

### 3.4 Update ProcessAnswerAdaptiveUseCase

**File**: `src/application/use_cases/process_answer_adaptive.py` (UPDATE)

```python
async def execute(
    self,
    interview_id: UUID,
    question_id: UUID,
    answer_text: str,
    audio_file_path: str | None = None,
    voice_metrics: dict[str, float] | None = None,
) -> tuple[Answer, Evaluation, bool]:
    """Process answer with context-aware evaluation."""

    # ... existing validation ...

    # NEW: Determine if this is a follow-up
    followup_context = None
    parent_evaluation = None

    # Check if question_id is in follow_up_questions table
    follow_up = await self.follow_up_question_repo.get_by_id(question_id)

    if follow_up:
        # This is a follow-up answer - build context
        parent_question_id = follow_up.parent_question_id

        # Get parent evaluation
        parent_answers = await self.answer_repo.get_by_question_id(parent_question_id)
        if parent_answers:
            parent_answer = parent_answers[0]  # Should be exactly 1
            parent_evaluation = await self.evaluation_repo.get_by_answer_id(
                parent_answer.id
            )

        # Count follow-ups for this parent
        existing_follow_ups = await self.follow_up_question_repo.get_by_parent_question_id(
            parent_question_id
        )
        attempt_number = len(existing_follow_ups)  # 1, 2, or 3

        # Get cumulative gaps from parent + previous follow-ups
        cumulative_gaps = []
        previous_evaluations = []

        if parent_evaluation:
            cumulative_gaps.extend([g.concept for g in parent_evaluation.gaps if not g.resolved])
            previous_evaluations.append({
                "attempt": 1,
                "score": parent_evaluation.final_score,
                "gaps": [g.concept for g in parent_evaluation.gaps]
            })

            # Get follow-up evaluations
            followup_evals = await self.evaluation_repo.get_by_parent_evaluation_id(
                parent_evaluation.id
            )
            for i, fe in enumerate(followup_evals, 2):
                cumulative_gaps.extend([g.concept for g in fe.gaps if not g.resolved])
                previous_evaluations.append({
                    "attempt": i,
                    "score": fe.final_score,
                    "gaps": [g.concept for g in fe.gaps]
                })

        followup_context = FollowUpEvaluationContext(
            attempt_number=attempt_number,
            parent_question_id=parent_question_id,
            parent_evaluation_id=parent_evaluation.id if parent_evaluation else None,
            cumulative_gaps=list(set(cumulative_gaps)),  # Dedupe
            previous_evaluations=previous_evaluations
        )

    # Step 4: Evaluate answer with context
    llm_eval = await self.llm.evaluate_answer(
        question=question,
        answer_text=answer_text,
        context={
            "interview_id": str(interview_id),
            "candidate_id": str(interview.candidate_id),
        },
        followup_context=followup_context,  # NEW
    )

    # ... similarity + gap detection ...

    # Step 7: Create Evaluation entity with penalty
    evaluation = Evaluation(
        answer_id=answer.id,
        question_id=question_id,
        interview_id=interview_id,
        raw_score=llm_eval.score,
        penalty=0.0,  # Will be set by apply_penalty
        final_score=llm_eval.score,
        similarity_score=similarity_score,
        completeness=llm_eval.completeness,
        relevance=llm_eval.relevance,
        sentiment=llm_eval.sentiment,
        reasoning=llm_eval.reasoning,
        strengths=llm_eval.strengths,
        weaknesses=llm_eval.weaknesses,
        improvement_suggestions=llm_eval.improvement_suggestions,
        attempt_number=followup_context.attempt_number if followup_context else 1,
        parent_evaluation_id=followup_context.parent_evaluation_id if followup_context else None,
        gaps=[
            ConceptGap(
                evaluation_id=answer.id,
                concept=concept,
                severity=GapSeverity(gaps_dict.get("severity", "moderate")),
                resolved=False
            )
            for concept in gaps_dict.get("concepts", [])
        ],
        evaluated_at=datetime.utcnow()
    )

    # NEW: Apply penalty based on attempt
    if followup_context:
        evaluation.apply_penalty(followup_context.attempt_number)

    # NEW: Resolve gaps if criteria met
    if evaluation.final_score >= 80 or evaluation.completeness >= 0.8:
        evaluation.resolve_gaps()
        # Also resolve parent gaps
        if parent_evaluation:
            parent_evaluation.resolve_gaps()
            await self.evaluation_repo.update(parent_evaluation)

    # ... save evaluation, answer, update interview ...

    return saved_answer, saved_evaluation, has_more
```

---

## Migration Strategy

### Pre-Migration Checklist

- [ ] **Backup database** (full dump via `pg_dump`)
- [ ] **Test migration on staging environment**
- [ ] **Verify data counts**: `SELECT COUNT(*) FROM answers WHERE evaluation IS NOT NULL`
- [ ] **Check for NULL fields**: Ensure no critical NULLs in `answers.evaluation`
- [ ] **Review migration SQL** (dry-run with `alembic upgrade --sql`)

### Migration Steps

1. **Apply migration** (5 min):
   ```bash
   alembic upgrade head
   ```

2. **Verify data migration** (2 min):
   ```sql
   -- Check counts match
   SELECT COUNT(*) FROM evaluations;  -- Should equal answers with evaluation
   SELECT COUNT(*) FROM evaluation_gaps;  -- Should equal total gaps

   -- Spot-check random records
   SELECT a.id, a.evaluation_id, e.final_score
   FROM answers a
   JOIN evaluations e ON e.answer_id = a.id
   LIMIT 10;
   ```

3. **Run smoke tests** (5 min):
   ```bash
   pytest tests/integration/test_evaluation_repository.py -v
   ```

4. **Monitor logs** (ongoing):
   - Watch for `ProcessAnswerAdaptiveUseCase` errors
   - Check evaluation creation rate

### Rollback Plan

**If migration fails**:

1. **Stop application**
2. **Rollback migration**:
   ```bash
   alembic downgrade -1
   ```
3. **Restore backup** (if data corruption):
   ```bash
   psql < backup.sql
   ```
4. **Investigate logs**, fix migration SQL, retry

**Rollback window**: 24 hours (before old columns dropped)

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/domain/test_evaluation.py` (NEW)

```python
"""Test Evaluation domain model."""

def test_apply_penalty_first_attempt():
    """Penalty should be 0 for 1st attempt."""
    eval = Evaluation(
        answer_id=uuid4(),
        question_id=uuid4(),
        interview_id=uuid4(),
        raw_score=80.0,
        completeness=0.7,
        relevance=0.8
    )
    eval.apply_penalty(1)
    assert eval.penalty == 0.0
    assert eval.final_score == 80.0
    assert eval.attempt_number == 1

def test_apply_penalty_second_attempt():
    """Penalty should be -5 for 2nd attempt."""
    eval = Evaluation(...)
    eval.apply_penalty(2)
    assert eval.penalty == -5.0
    assert eval.final_score == 75.0
    assert eval.attempt_number == 2

def test_apply_penalty_third_attempt():
    """Penalty should be -15 for 3rd attempt."""
    eval = Evaluation(...)
    eval.apply_penalty(3)
    assert eval.penalty == -15.0
    assert eval.final_score == 65.0

def test_has_gaps():
    """Should detect unresolved gaps."""
    eval = Evaluation(...)
    eval.gaps = [
        ConceptGap(concept="closure", severity=GapSeverity.MAJOR, resolved=False),
        ConceptGap(concept="hoisting", severity=GapSeverity.MINOR, resolved=True)
    ]
    assert eval.has_gaps() is True

def test_resolve_gaps():
    """Should mark all gaps as resolved."""
    eval = Evaluation(...)
    eval.gaps = [
        ConceptGap(concept="closure", severity=GapSeverity.MAJOR, resolved=False)
    ]
    eval.resolve_gaps()
    assert all(g.resolved for g in eval.gaps)
```

**File**: `tests/unit/repositories/test_evaluation_repository.py` (NEW)

```python
"""Test EvaluationRepository."""

async def test_save_evaluation_with_gaps():
    """Should save evaluation with gaps."""
    eval = Evaluation(...)
    eval.gaps = [ConceptGap(...)]

    saved = await repo.save(eval)

    assert saved.id == eval.id
    assert len(saved.gaps) == 1
    assert saved.gaps[0].concept == "closure"

async def test_get_by_answer_id():
    """Should retrieve evaluation by answer ID."""
    eval = await repo.save(Evaluation(...))

    retrieved = await repo.get_by_answer_id(eval.answer_id)

    assert retrieved.id == eval.id

async def test_get_by_parent_evaluation_id():
    """Should retrieve follow-up evaluations."""
    parent = await repo.save(Evaluation(...))
    followup1 = await repo.save(Evaluation(parent_evaluation_id=parent.id, ...))
    followup2 = await repo.save(Evaluation(parent_evaluation_id=parent.id, ...))

    followups = await repo.get_by_parent_evaluation_id(parent.id)

    assert len(followups) == 2
```

**File**: `tests/unit/use_cases/test_process_answer_adaptive.py` (UPDATE)

```python
"""Test ProcessAnswerAdaptiveUseCase with Phase 2 context."""

async def test_process_main_question_answer():
    """Should create evaluation with no penalty for main question."""
    answer, evaluation, has_more = await use_case.execute(
        interview_id=interview.id,
        question_id=main_question.id,
        answer_text="My answer"
    )

    assert evaluation.attempt_number == 1
    assert evaluation.penalty == 0.0
    assert evaluation.parent_evaluation_id is None

async def test_process_followup_answer():
    """Should create evaluation with penalty for follow-up."""
    # Setup: Create parent answer + follow-up
    parent_answer, parent_eval, _ = await use_case.execute(...)
    followup_q = await followup_repo.create(
        FollowUpQuestion(parent_question_id=main_question.id, ...)
    )

    # Act: Answer follow-up
    followup_answer, followup_eval, _ = await use_case.execute(
        interview_id=interview.id,
        question_id=followup_q.id,
        answer_text="Follow-up answer"
    )

    # Assert
    assert followup_eval.attempt_number == 2
    assert followup_eval.penalty == -5.0
    assert followup_eval.parent_evaluation_id == parent_eval.id

async def test_resolve_gaps_on_high_score():
    """Should resolve gaps when final_score >= 80."""
    answer, evaluation, _ = await use_case.execute(...)

    # Simulate high score
    evaluation.raw_score = 85.0
    evaluation.apply_penalty(1)

    assert evaluation.final_score == 85.0
    assert all(g.resolved for g in evaluation.gaps)
```

### Integration Tests

**File**: `tests/integration/test_evaluation_flow.py` (NEW)

```python
"""End-to-end evaluation flow test."""

async def test_main_question_to_followup_flow():
    """Test full flow: main Q -> follow-up -> gap resolution."""

    # Step 1: Answer main question (low score, gaps detected)
    answer1, eval1, _ = await process_answer_use_case.execute(
        interview_id=interview.id,
        question_id=main_q.id,
        answer_text="Incomplete answer"
    )

    assert eval1.attempt_number == 1
    assert eval1.penalty == 0.0
    assert eval1.has_gaps() is True

    # Step 2: Generate follow-up
    decision = await followup_decision_use_case.execute(
        interview_id=interview.id,
        parent_question_id=main_q.id,
        latest_answer=answer1
    )
    assert decision["needs_followup"] is True

    # Step 3: Answer follow-up (better score)
    followup_q = await followup_repo.create(...)
    answer2, eval2, _ = await process_answer_use_case.execute(
        interview_id=interview.id,
        question_id=followup_q.id,
        answer_text="Better answer addressing gaps"
    )

    assert eval2.attempt_number == 2
    assert eval2.penalty == -5.0
    assert eval2.parent_evaluation_id == eval1.id
    assert eval2.final_score == eval2.raw_score - 5.0

    # Step 4: Verify gap resolution
    if eval2.final_score >= 80:
        assert all(g.resolved for g in eval2.gaps)
        # Parent gaps should also be resolved
        updated_eval1 = await evaluation_repo.get_by_id(eval1.id)
        assert all(g.resolved for g in updated_eval1.gaps)
```

### Test Coverage Goals

- **Domain models**: 100% (Evaluation, ConceptGap)
- **Repositories**: 95% (EvaluationRepository)
- **Use cases**: 90% (ProcessAnswerAdaptiveUseCase)
- **Adapters**: 85% (LLM adapters with follow-up context)

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (`pytest --cov=src`)
- [ ] Code review approved
- [ ] Migration tested on staging
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

### Deployment Steps

1. [ ] **Announce maintenance window** (if needed)
2. [ ] **Backup production database**
3. [ ] **Deploy code** (with migration)
   ```bash
   git pull origin main
   pip install -e .
   alembic upgrade head
   systemctl restart elios-api
   ```
4. [ ] **Verify migration** (check evaluations table)
5. [ ] **Run smoke tests** (prod API)
6. [ ] **Monitor logs** (1 hour)

### Post-Deployment

- [ ] Verify evaluation creation (check logs)
- [ ] Monitor penalty application (sample evaluations)
- [ ] Check gap resolution tracking
- [ ] Performance monitoring (DB query times)
- [ ] User acceptance testing

### Rollback Triggers

- Migration fails (data loss/corruption)
- >10% error rate in ProcessAnswerAdaptiveUseCase
- DB performance degradation (>2x query time)
- Critical bugs in penalty logic

---

## Risk Assessment

### High Risk

**R1: Data Migration Corruption**
- **Probability**: Low
- **Impact**: Critical (data loss)
- **Mitigation**: Full backup, staging test, verify counts
- **Rollback**: Restore from backup + downgrade migration

### Medium Risk

**R2: Follow-Up Question Lookup Bug**
- **Probability**: Medium
- **Impact**: Moderate (crashes on follow-up answers)
- **Mitigation**: Unit tests for follow-up detection, integration tests
- **Rollback**: None (bug exists now, fix required)

**R3: Penalty Calculation Error**
- **Probability**: Low
- **Impact**: Moderate (incorrect scores)
- **Mitigation**: Extensive unit tests, manual QA
- **Rollback**: Fix penalty logic in `Evaluation.apply_penalty()`

### Low Risk

**R4: Performance Degradation**
- **Probability**: Low
- **Impact**: Low (slower queries)
- **Mitigation**: Indexes on FK columns, query optimization
- **Rollback**: Add missing indexes

**R5: Gap Resolution Logic Bug**
- **Probability**: Medium
- **Impact**: Low (gaps not marked resolved)
- **Mitigation**: Integration tests, manual verification
- **Rollback**: Fix logic in use case

---

## Appendix

### A. File Changes Summary

**Phase 1** (6 hours):

| File | Change Type | LOC | Complexity |
|------|-------------|-----|------------|
| `alembic/versions/0003_create_evaluations.py` | NEW | ~200 | High |
| `src/domain/models/evaluation.py` | NEW | ~120 | Medium |
| `src/domain/models/answer.py` | UPDATE | -50 | Low |
| `src/domain/ports/evaluation_repository_port.py` | NEW | ~40 | Low |
| `src/adapters/persistence/models.py` | UPDATE | +80 | Medium |
| `src/adapters/persistence/evaluation_repository.py` | NEW | ~100 | Medium |
| `src/adapters/persistence/mappers.py` | UPDATE | +120 | High |
| `src/infrastructure/dependency_injection/container.py` | UPDATE | +10 | Low |
| `src/application/use_cases/process_answer_adaptive.py` | UPDATE | ~80 | High |
| **Total** | | **~750** | |

**Phase 2** (3 hours):

| File | Change Type | LOC | Complexity |
|------|-------------|-----|------------|
| `src/domain/models/evaluation.py` | UPDATE | +20 | Low |
| `src/domain/ports/llm_port.py` | UPDATE | +10 | Low |
| `src/adapters/llm/openai_adapter.py` | UPDATE | +30 | Medium |
| `src/adapters/llm/azure_openai_adapter.py` | UPDATE | +30 | Medium |
| `src/adapters/mock/mock_llm_adapter.py` | UPDATE | +15 | Low |
| `src/application/use_cases/process_answer_adaptive.py` | UPDATE | +60 | High |
| **Total** | | **~165** | |

**Grand Total**: ~915 LOC

### B. Database Schema Diagram

```
┌──────────────────────────────────────────────────────┐
│ evaluations                                          │
├──────────────────────────────────────────────────────┤
│ id UUID PK                                           │
│ answer_id UUID FK → answers(id)                      │
│ question_id UUID (no FK)                             │
│ interview_id UUID FK → interviews(id)                │
│ raw_score FLOAT                                      │
│ penalty FLOAT                                        │
│ final_score FLOAT                                    │
│ similarity_score FLOAT                               │
│ completeness FLOAT                                   │
│ relevance FLOAT                                      │
│ sentiment VARCHAR(50)                                │
│ reasoning TEXT                                       │
│ strengths TEXT[]                                     │
│ weaknesses TEXT[]                                    │
│ improvement_suggestions TEXT[]                       │
│ attempt_number INT                                   │
│ parent_evaluation_id UUID FK → evaluations(id)       │
│ created_at TIMESTAMP                                 │
│ evaluated_at TIMESTAMP                               │
└──────────────────────────────────────────────────────┘
                    │
                    │ 1:N
                    ↓
┌──────────────────────────────────────────────────────┐
│ evaluation_gaps                                      │
├──────────────────────────────────────────────────────┤
│ id UUID PK                                           │
│ evaluation_id UUID FK → evaluations(id)              │
│ concept TEXT                                         │
│ severity VARCHAR(20)                                 │
│ resolved BOOLEAN                                     │
│ created_at TIMESTAMP                                 │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ answers                                              │
├──────────────────────────────────────────────────────┤
│ id UUID PK                                           │
│ evaluation_id UUID FK → evaluations(id)              │
│ ... (other fields unchanged)                         │
└──────────────────────────────────────────────────────┘
```

### C. Context-Aware Evaluation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ ProcessAnswerAdaptiveUseCase                                │
└─────────────────────────────────────────────────────────────┘
                    │
                    ↓
         Is question_id follow-up?
                    │
        ┌───────────┴───────────┐
        │                       │
       YES                     NO
        │                       │
        ↓                       ↓
┌──────────────────┐   ┌──────────────────┐
│ Build context    │   │ No context       │
│ - attempt_number │   │ - attempt = 1    │
│ - parent_eval_id │   │ - penalty = 0    │
│ - cumulative_gaps│   └──────────────────┘
│ - prev_evals     │            │
└──────────────────┘            │
        │                       │
        └───────────┬───────────┘
                    ↓
        LLM.evaluate_answer(followup_context)
                    │
                    ↓
        Create Evaluation (raw_score)
                    │
                    ↓
        Apply penalty (attempt_number)
                    │
                    ↓
        Check gap resolution
        - final_score >= 80?
        - completeness >= 0.8?
                    │
                    ↓
        Resolve gaps (if met)
                    │
                    ↓
        Save Evaluation + Gaps
```

### D. Unresolved Questions

1. **Should we backfill attempt_number for old follow-ups?**
   - Currently migration sets all to 1
   - Could infer from `follow_up_questions.order_in_sequence`
   - Decision: Skip (complexity vs value)

2. **Max penalty cap for extreme cases?**
   - Current: -15 max (3rd attempt)
   - Could add -20 for 4th+ (if we allow >3)
   - Decision: Stick to max 3 follow-ups

3. **Gap severity calculation logic?**
   - LLM returns severity string
   - Could derive from concept count/importance
   - Decision: Trust LLM judgment

---

**Plan Status**: Ready for Implementation
**Next Steps**: Phase 1 migration on staging → test → Phase 2 LLM updates
**Approval Required**: Database schema changes (DBA review)
