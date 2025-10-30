"""LLM (Large Language Model) port interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from uuid import UUID

from ..models.question import Question
from ..models.answer import AnswerEvaluation


class LLMPort(ABC):
    """Interface for Large Language Model providers.

    This port abstracts LLM interactions, allowing easy switching between
    providers like OpenAI, Claude, Llama, etc.
    """

    @abstractmethod
    async def generate_question(
        self,
        context: Dict[str, Any],
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
        context: Dict[str, Any],
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
        questions: List[Question],
        answers: List[Dict[str, Any]],
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
    async def extract_skills_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract skills from CV text using NLP.

        Args:
            text: CV text to analyze

        Returns:
            List of extracted skills with metadata
        """
        pass