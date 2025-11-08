"""LLM (Large Language Model) port interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from ..models.answer import AnswerEvaluation
from ..models.question import Question


class LLMPort(ABC):
    """Interface for Large Language Model providers.

    This port abstracts LLM interactions, allowing easy switching between
    providers like OpenAI, Claude, Llama, etc.
    """

    @abstractmethod
    async def generate_question(
        self,
        context: dict[str, Any],
        skill: str,
        difficulty: str,
    ) -> str:
        """Generate an interview question.

        Args:
            context: Interview context (CV analysis, previous answers, etc.)
            skill: Target skill to test
            difficulty: Question difficulty level

        Returns:
            Generated question text
        """
        pass

    @abstractmethod
    async def evaluate_answer(
        self,
        question: Question,
        answer_text: str,
        context: dict[str, Any],
    ) -> AnswerEvaluation:
        """Evaluate a candidate's answer.

        Args:
            question: The question that was asked
            answer_text: Candidate's answer
            context: Additional context for evaluation

        Returns:
            Evaluation results with score and feedback
        """
        pass

    @abstractmethod
    async def generate_feedback_report(
        self,
        interview_id: UUID,
        questions: list[Question],
        answers: list[dict[str, Any]],
    ) -> str:
        """Generate comprehensive feedback report.

        Args:
            interview_id: ID of the interview
            questions: All questions asked
            answers: All answers with evaluations

        Returns:
            Formatted feedback report
        """
        pass

    @abstractmethod
    async def summarize_cv(self, cv_text: str) -> str:
        """Generate a summary of a CV.

        Args:
            cv_text: Extracted CV text

        Returns:
            Summary of the CV
        """
        pass

    @abstractmethod
    async def extract_skills_from_text(self, text: str) -> list[dict[str, str]]:
        """Extract skills from CV text using NLP.

        Args:
            text: CV text to analyze

        Returns:
            List of extracted skills with metadata
        """
        pass

    @abstractmethod
    async def generate_ideal_answer(
        self,
        question_text: str,
        context: dict[str, Any],
    ) -> str:
        """Generate ideal answer for a question.

        Args:
            question_text: The interview question
            context: CV summary, skills, etc.

        Returns:
            Ideal answer text (150-300 words)
        """
        pass

    @abstractmethod
    async def generate_rationale(
        self,
        question_text: str,
        ideal_answer: str,
    ) -> str:
        """Generate rationale explaining why answer is ideal.

        Args:
            question_text: The question
            ideal_answer: The ideal answer

        Returns:
            Rationale text (50-100 words)
        """
        pass

    @abstractmethod
    async def detect_concept_gaps(
        self,
        answer_text: str,
        ideal_answer: str,
        question_text: str,
        keyword_gaps: list[str],
    ) -> dict[str, Any]:
        """Detect missing concepts in answer using LLM.

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer
            question_text: The question that was asked
            keyword_gaps: Potential missing keywords from keyword analysis

        Returns:
            Dict with keys:
                - concepts: list[str] - Missing key concepts
                - keywords: list[str] - Subset of confirmed missing keywords
                - confirmed: bool - Whether gaps are confirmed
                - severity: str - "minor" | "moderate" | "major"
        """
        pass

    @abstractmethod
    async def generate_followup_question(
        self,
        parent_question: str,
        answer_text: str,
        missing_concepts: list[str],
        severity: str,
        order: int,
    ) -> str:
        """Generate targeted follow-up question.

        Args:
            parent_question: Original question text
            answer_text: Candidate's answer to parent question
            missing_concepts: List of concepts missing from answer
            severity: Gap severity ("minor" | "moderate" | "major")
            order: Follow-up order in sequence (1, 2, 3, ...)

        Returns:
            Follow-up question text
        """
        pass
