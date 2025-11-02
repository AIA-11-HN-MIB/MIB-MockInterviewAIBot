"""SQLAlchemy models for persistence.

These models represent the database schema and map domain entities
to database tables using SQLAlchemy ORM.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...domain.models.interview import InterviewStatus
from ...domain.models.question import DifficultyLevel, QuestionType
from ...infrastructure.database.base import Base


class CandidateModel(Base):
    """SQLAlchemy model for Candidate entity."""

    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    cv_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    interviews: Mapped[list["InterviewModel"]] = relationship(
        "InterviewModel",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    cv_analyses: Mapped[list["CVAnalysisModel"]] = relationship(
        "CVAnalysisModel",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    answers: Mapped[list["AnswerModel"]] = relationship(
        "AnswerModel",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_candidates_email", "email"),
        Index("idx_candidates_created_at", "created_at"),
    )


class QuestionModel(Base):
    """SQLAlchemy model for Question entity."""

    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        SQLEnum(QuestionType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    difficulty: Mapped[str] = mapped_column(
        SQLEnum(DifficultyLevel, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    skills: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False, default=[])
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False, default=[])
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    answers: Mapped[list["AnswerModel"]] = relationship(
        "AnswerModel",
        back_populates="question",
    )

    __table_args__ = (
        Index("idx_questions_type", "question_type"),
        Index("idx_questions_difficulty", "difficulty"),
        Index("idx_questions_skills", "skills", postgresql_using="gin"),
        Index("idx_questions_tags", "tags", postgresql_using="gin"),
    )


class InterviewModel(Base):
    """SQLAlchemy model for Interview entity."""

    __tablename__ = "interviews"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(InterviewStatus, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    cv_analysis_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cv_analyses.id", ondelete="SET NULL"),
        nullable=True,
    )
    question_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)),
        nullable=False,
        default=[],
    )
    answer_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)),
        nullable=False,
        default=[],
    )
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    candidate: Mapped["CandidateModel"] = relationship(
        "CandidateModel",
        back_populates="interviews",
    )
    cv_analysis: Mapped["CVAnalysisModel | None"] = relationship(
        "CVAnalysisModel",
        foreign_keys=[cv_analysis_id],
    )
    answers: Mapped[list["AnswerModel"]] = relationship(
        "AnswerModel",
        back_populates="interview",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_interviews_candidate_id", "candidate_id"),
        Index("idx_interviews_status", "status"),
        Index("idx_interviews_created_at", "created_at"),
    )


class AnswerModel(Base):
    """SQLAlchemy model for Answer entity."""

    __tablename__ = "answers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    interview_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_voice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    audio_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)
    answer_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    interview: Mapped["InterviewModel"] = relationship(
        "InterviewModel",
        back_populates="answers",
    )
    question: Mapped["QuestionModel"] = relationship(
        "QuestionModel",
        back_populates="answers",
    )
    candidate: Mapped["CandidateModel"] = relationship(
        "CandidateModel",
        back_populates="answers",
    )

    __table_args__ = (
        Index("idx_answers_interview_id", "interview_id"),
        Index("idx_answers_question_id", "question_id"),
        Index("idx_answers_candidate_id", "candidate_id"),
        Index("idx_answers_created_at", "created_at"),
    )


class CVAnalysisModel(Base):
    """SQLAlchemy model for CV Analysis entity."""

    __tablename__ = "cv_analyses"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cv_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=[])
    work_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    suggested_topics: Mapped[list[str]] = mapped_column(
        ARRAY(String(200)),
        nullable=False,
        default=[],
    )
    suggested_difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    cv_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    candidate: Mapped["CandidateModel"] = relationship(
        "CandidateModel",
        back_populates="cv_analyses",
    )

    __table_args__ = (
        Index("idx_cv_analyses_candidate_id", "candidate_id"),
        Index("idx_cv_analyses_created_at", "created_at"),
    )
