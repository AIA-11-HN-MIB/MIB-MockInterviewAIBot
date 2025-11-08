"""Mappers to convert between domain models and SQLAlchemy models.

These mappers handle the translation between the domain layer
(Pydantic models) and the persistence layer (SQLAlchemy models).
"""


from ...domain.models.answer import Answer, AnswerEvaluation
from ...domain.models.candidate import Candidate
from ...domain.models.cv_analysis import CVAnalysis, ExtractedSkill
from ...domain.models.interview import Interview, InterviewStatus
from ...domain.models.question import DifficultyLevel, Question, QuestionType
from .models import (
    AnswerModel,
    CandidateModel,
    CVAnalysisModel,
    InterviewModel,
    QuestionModel,
)


class CandidateMapper:
    """Mapper for Candidate domain model and CandidateModel database model."""

    @staticmethod
    def to_domain(db_model: CandidateModel) -> Candidate:
        """Convert database model to domain model.

        Args:
            db_model: SQLAlchemy model instance

        Returns:
            Domain model instance
        """
        return Candidate(
            id=db_model.id,
            name=db_model.name,
            email=db_model.email,
            cv_file_path=db_model.cv_file_path,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )

    @staticmethod
    def to_db_model(domain_model: Candidate) -> CandidateModel:
        """Convert domain model to database model.

        Args:
            domain_model: Domain model instance

        Returns:
            SQLAlchemy model instance
        """
        return CandidateModel(
            id=domain_model.id,
            name=domain_model.name,
            email=domain_model.email,
            cv_file_path=domain_model.cv_file_path,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at,
        )

    @staticmethod
    def update_db_model(db_model: CandidateModel, domain_model: Candidate) -> None:
        """Update database model from domain model.

        Args:
            db_model: SQLAlchemy model to update
            domain_model: Domain model with new data
        """
        db_model.name = domain_model.name
        db_model.email = domain_model.email
        db_model.cv_file_path = domain_model.cv_file_path
        db_model.updated_at = domain_model.updated_at


class QuestionMapper:
    """Mapper for Question domain model and QuestionModel database model."""

    @staticmethod
    def to_domain(db_model: QuestionModel) -> Question:
        """Convert database model to domain model."""
        return Question(
            id=db_model.id,
            text=db_model.text,
            question_type=QuestionType(db_model.question_type),
            difficulty=DifficultyLevel(db_model.difficulty),
            skills=list(db_model.skills) if db_model.skills else [],
            tags=list(db_model.tags) if db_model.tags else [],
            reference_answer=db_model.reference_answer,
            evaluation_criteria=db_model.evaluation_criteria,
            version=db_model.version,
            embedding=list(db_model.embedding) if db_model.embedding else None,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )

    @staticmethod
    def to_db_model(domain_model: Question) -> QuestionModel:
        """Convert domain model to database model."""
        return QuestionModel(
            id=domain_model.id,
            text=domain_model.text,
            question_type=domain_model.question_type.value,
            difficulty=domain_model.difficulty.value,
            skills=domain_model.skills,
            tags=domain_model.tags,
            reference_answer=domain_model.reference_answer,
            evaluation_criteria=domain_model.evaluation_criteria,
            version=domain_model.version,
            embedding=domain_model.embedding,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at,
        )

    @staticmethod
    def update_db_model(db_model: QuestionModel, domain_model: Question) -> None:
        """Update database model from domain model."""
        db_model.text = domain_model.text
        db_model.question_type = domain_model.question_type.value
        db_model.difficulty = domain_model.difficulty.value
        db_model.skills = domain_model.skills
        db_model.tags = domain_model.tags
        db_model.reference_answer = domain_model.reference_answer
        db_model.evaluation_criteria = domain_model.evaluation_criteria
        db_model.version = domain_model.version
        db_model.embedding = domain_model.embedding
        db_model.updated_at = domain_model.updated_at


class InterviewMapper:
    """Mapper for Interview domain model and InterviewModel database model."""

    @staticmethod
    def to_domain(db_model: InterviewModel) -> Interview:
        """Convert database model to domain model."""
        return Interview(
            id=db_model.id,
            candidate_id=db_model.candidate_id,
            status=InterviewStatus(db_model.status),
            cv_analysis_id=db_model.cv_analysis_id,
            question_ids=list(db_model.question_ids) if db_model.question_ids else [],
            answer_ids=list(db_model.answer_ids) if db_model.answer_ids else [],
            current_question_index=db_model.current_question_index,
            started_at=db_model.started_at,
            completed_at=db_model.completed_at,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )

    @staticmethod
    def to_db_model(domain_model: Interview) -> InterviewModel:
        """Convert domain model to database model."""
        return InterviewModel(
            id=domain_model.id,
            candidate_id=domain_model.candidate_id,
            status=domain_model.status.value,
            cv_analysis_id=domain_model.cv_analysis_id,
            question_ids=domain_model.question_ids,
            answer_ids=domain_model.answer_ids,
            current_question_index=domain_model.current_question_index,
            started_at=domain_model.started_at,
            completed_at=domain_model.completed_at,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at,
        )

    @staticmethod
    def update_db_model(db_model: InterviewModel, domain_model: Interview) -> None:
        """Update database model from domain model."""
        db_model.status = domain_model.status.value
        db_model.cv_analysis_id = domain_model.cv_analysis_id
        db_model.question_ids = domain_model.question_ids
        db_model.answer_ids = domain_model.answer_ids
        db_model.current_question_index = domain_model.current_question_index
        db_model.started_at = domain_model.started_at
        db_model.completed_at = domain_model.completed_at
        db_model.updated_at = domain_model.updated_at


class AnswerMapper:
    """Mapper for Answer domain model and AnswerModel database model."""

    @staticmethod
    def to_domain(db_model: AnswerModel) -> Answer:
        """Convert database model to domain model."""
        # Convert evaluation JSONB to AnswerEvaluation if present
        evaluation = None
        if db_model.evaluation:
            evaluation = AnswerEvaluation(**db_model.evaluation)

        return Answer(
            id=db_model.id,
            interview_id=db_model.interview_id,
            question_id=db_model.question_id,
            candidate_id=db_model.candidate_id,
            text=db_model.text,
            is_voice=db_model.is_voice,
            audio_file_path=db_model.audio_file_path,
            duration_seconds=db_model.duration_seconds,
            evaluation=evaluation,
            embedding=list(db_model.embedding) if db_model.embedding else None,
            metadata=dict(db_model.answer_metadata) if db_model.answer_metadata else {},
            created_at=db_model.created_at,
            evaluated_at=db_model.evaluated_at,
        )

    @staticmethod
    def to_db_model(domain_model: Answer) -> AnswerModel:
        """Convert domain model to database model."""
        # Convert AnswerEvaluation to dict for JSONB storage
        evaluation_dict = None
        if domain_model.evaluation:
            evaluation_dict = domain_model.evaluation.model_dump()

        return AnswerModel(
            id=domain_model.id,
            interview_id=domain_model.interview_id,
            question_id=domain_model.question_id,
            candidate_id=domain_model.candidate_id,
            text=domain_model.text,
            is_voice=domain_model.is_voice,
            audio_file_path=domain_model.audio_file_path,
            duration_seconds=domain_model.duration_seconds,
            evaluation=evaluation_dict,
            embedding=domain_model.embedding,
            answer_metadata=domain_model.metadata,
            created_at=domain_model.created_at,
            evaluated_at=domain_model.evaluated_at,
        )

    @staticmethod
    def update_db_model(db_model: AnswerModel, domain_model: Answer) -> None:
        """Update database model from domain model."""
        db_model.text = domain_model.text
        db_model.is_voice = domain_model.is_voice
        db_model.audio_file_path = domain_model.audio_file_path
        db_model.duration_seconds = domain_model.duration_seconds

        # Convert evaluation to dict if present
        if domain_model.evaluation:
            db_model.evaluation = domain_model.evaluation.model_dump()
        else:
            db_model.evaluation = None

        db_model.embedding = domain_model.embedding
        db_model.answer_metadata = domain_model.metadata
        db_model.evaluated_at = domain_model.evaluated_at


class CVAnalysisMapper:
    """Mapper for CVAnalysis domain model and CVAnalysisModel database model."""

    @staticmethod
    def to_domain(db_model: CVAnalysisModel) -> CVAnalysis:
        """Convert database model to domain model."""
        # Convert skills from JSONB to ExtractedSkill objects
        skills = []
        if db_model.skills:
            skills = [ExtractedSkill(**skill_dict) for skill_dict in db_model.skills]

        return CVAnalysis(
            id=db_model.id,
            candidate_id=db_model.candidate_id,
            cv_file_path=db_model.cv_file_path,
            extracted_text=db_model.extracted_text,
            skills=skills,
            work_experience_years=db_model.work_experience_years,
            education_level=db_model.education_level,
            suggested_topics=(
                list(db_model.suggested_topics) if db_model.suggested_topics else []
            ),
            suggested_difficulty=db_model.suggested_difficulty,
            embedding=list(db_model.embedding) if db_model.embedding else None,
            summary=db_model.summary,
            metadata=dict(db_model.cv_metadata) if db_model.cv_metadata else {},
            created_at=db_model.created_at,
        )

    @staticmethod
    def to_db_model(domain_model: CVAnalysis) -> CVAnalysisModel:
        """Convert domain model to database model."""
        # Convert ExtractedSkill objects to dicts for JSONB storage
        skills_dicts = [skill.model_dump() for skill in domain_model.skills]

        return CVAnalysisModel(
            id=domain_model.id,
            candidate_id=domain_model.candidate_id,
            cv_file_path=domain_model.cv_file_path,
            extracted_text=domain_model.extracted_text,
            skills=skills_dicts,
            work_experience_years=domain_model.work_experience_years,
            education_level=domain_model.education_level,
            suggested_topics=domain_model.suggested_topics,
            suggested_difficulty=domain_model.suggested_difficulty,
            embedding=domain_model.embedding,
            summary=domain_model.summary,
            cv_metadata=domain_model.metadata,
            created_at=domain_model.created_at,
        )

    @staticmethod
    def update_db_model(db_model: CVAnalysisModel, domain_model: CVAnalysis) -> None:
        """Update database model from domain model."""
        db_model.cv_file_path = domain_model.cv_file_path
        db_model.extracted_text = domain_model.extracted_text
        db_model.skills = [skill.model_dump() for skill in domain_model.skills]
        db_model.work_experience_years = domain_model.work_experience_years
        db_model.education_level = domain_model.education_level
        db_model.suggested_topics = domain_model.suggested_topics
        db_model.suggested_difficulty = domain_model.suggested_difficulty
        db_model.embedding = domain_model.embedding
        db_model.summary = domain_model.summary
        db_model.cv_metadata = domain_model.metadata
