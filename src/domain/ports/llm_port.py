"""LLM (Large Language Model) port interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from ..models.answer import AnswerEvaluation
from ..models.evaluation import FollowUpEvaluationContext
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
        exemplars: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate an interview question.

        Args:
            context: Interview context (CV analysis, previous answers, etc.)
            skill: Target skill to test
            difficulty: Question difficulty level
            exemplars: Optional list of similar questions for inspiration.
                      Each dict should contain: 'text', 'skills', 'difficulty', 'similarity_score'.
                      Helps LLM understand desired question style and depth.
                      Default: None (generate without exemplars)

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
        followup_context: FollowUpEvaluationContext | None = None,
    ) -> AnswerEvaluation:
        """Evaluate a candidate's answer.

        Args:
            question: The question that was asked
            answer_text: Candidate's answer
            context: Additional context for evaluation
            followup_context: Optional context for follow-up question evaluation.
                Includes previous evaluations, cumulative gaps, attempt number.
                Used to provide LLM with history and apply attempt-based penalties.

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
        cumulative_gaps: list[str] | None = None,
        previous_follow_ups: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate targeted follow-up question.

        Args:
            parent_question: Original question text
            answer_text: Candidate's answer to parent question (or latest follow-up)
            missing_concepts: List of concepts missing from current answer
            severity: Gap severity ("minor" | "moderate" | "major")
            order: Follow-up order in sequence (1, 2, 3, ...)
            cumulative_gaps: All unique gaps accumulated across follow-up cycle (optional)
            previous_follow_ups: Previous follow-up questions and answers for context (optional)

        Returns:
            Follow-up question text
        """
        pass

    @abstractmethod
    async def generate_interview_recommendations(
        self,
        context: dict[str, Any],
    ) -> dict[str, list[str]]:
        """Generate personalized interview recommendations.

        Args:
            context: Interview context including:
                - interview_id: str
                - total_answers: int
                - gap_progression: dict (gaps filled, remaining, etc.)
                - evaluations: list[dict] (scores, strengths, weaknesses per answer)

        Returns:
            Dict with keys:
                - strengths: list[str] (top 3-5 strengths)
                - weaknesses: list[str] (top 3-5 weaknesses)
                - study_topics: list[str] (topic-specific study recommendations)
                - technique_tips: list[str] (voice, pacing, structure tips)
        """
        pass

    @abstractmethod
    async def generate_questions_batch(
        self,
        question_specs: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[str]:
        """Generate multiple interview questions in a single batch call.

        Args:
            question_specs: List of question specifications. Each dict should contain:
                - skill: str - Target skill to test
                - difficulty: str - Question difficulty level
                - exemplars: list[dict[str, Any]] | None - Optional exemplar questions
            context: Interview context (CV analysis, etc.)

        Returns:
            List of generated question texts in the same order as question_specs
        """
        pass

    @abstractmethod
    async def generate_ideal_answers_batch(
        self,
        question_texts: list[str],
        context: dict[str, Any],
    ) -> list[str]:
        """Generate ideal answers for multiple questions in a single batch call.

        Args:
            question_texts: List of interview questions
            context: CV summary, skills, etc.

        Returns:
            List of ideal answer texts (150-300 words each) in the same order as question_texts
        """
        pass

    @abstractmethod
    async def generate_rationales_batch(
        self,
        question_ideal_pairs: list[tuple[str, str]],
    ) -> list[str]:
        """Generate rationales for multiple question-answer pairs in a single batch call.

        Args:
            question_ideal_pairs: List of (question_text, ideal_answer) tuples

        Returns:
            List of rationale texts (50-100 words each) in the same order as question_ideal_pairs
        """
        pass