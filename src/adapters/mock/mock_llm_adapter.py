"""Mock LLM adapter for development and testing."""

import random
from typing import Any
from uuid import UUID

from ...domain.models.answer import AnswerEvaluation
from ...domain.models.question import Question
from ...domain.ports.llm_port import LLMPort


class MockLLMAdapter(LLMPort):
    """Mock LLM adapter that returns realistic but fake responses.

    This adapter simulates LLM behavior for development and testing
    without requiring actual API calls to external services.
    """

    async def generate_question(
        self,
        context: dict[str, Any],
        skill: str,
        difficulty: str,
        exemplars: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate mock question.

        Args:
            context: Interview context
            skill: Target skill to test
            difficulty: Question difficulty level
            exemplars: Optional list of similar questions (for testing)

        Returns:
            Mock question text
        """
        base_question = f"Mock question about {skill} at {difficulty} difficulty?"

        # Indicate exemplars were provided (for testing purposes)
        if exemplars:
            base_question += f" [Generated with {len(exemplars)} exemplar(s)]"

        return base_question

    async def evaluate_answer(
        self,
        question: Question,
        answer_text: str,
        context: dict[str, Any],
    ) -> AnswerEvaluation:
        """Generate mock evaluation with realistic scores."""
        # Random score between 70-95 for realistic feel
        score = random.uniform(70.0, 95.0)

        # Simulate different evaluation patterns based on score
        if score >= 85:
            strengths = [
                "Clear and comprehensive explanation",
                "Good use of examples",
                "Strong technical understanding",
            ]
            weaknesses = ["Could provide more edge case handling"]
            improvements = ["Consider discussing performance implications"]
            sentiment = "confident"
        elif score >= 75:
            strengths = [
                "Solid understanding of concepts",
                "Relevant examples provided",
            ]
            weaknesses = [
                "Missing some technical details",
                "Could be more structured",
            ]
            improvements = [
                "Add more specific examples",
                "Elaborate on implementation details",
            ]
            sentiment = "positive"
        else:
            strengths = ["Basic understanding demonstrated"]
            weaknesses = [
                "Lacks depth",
                "Missing key concepts",
                "Limited examples",
            ]
            improvements = [
                "Study the fundamentals more thoroughly",
                "Provide concrete examples",
                "Explain reasoning more clearly",
            ]
            sentiment = "uncertain"

        return AnswerEvaluation(
            score=score,
            semantic_similarity=random.uniform(0.7, 0.95),
            completeness=random.uniform(0.7, 0.95),
            relevance=random.uniform(0.8, 1.0),
            sentiment=sentiment,
            reasoning=f"Mock evaluation: Answer demonstrates {sentiment} understanding of {question.text[:50]}...",
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=improvements,
        )

    async def generate_feedback_report(
        self,
        interview_id: UUID,
        questions: list[Question],
        answers: list[dict[str, Any]],
    ) -> str:
        """Generate mock feedback report."""
        avg_score = sum(a.get("score", 75) for a in answers) / len(answers) if answers else 75
        return f"""
Mock Feedback Report for Interview {interview_id}

Overall Performance: {avg_score:.1f}/100

Questions Answered: {len(answers)} of {len(questions)}

Strengths:
- Good understanding of fundamental concepts
- Clear communication skills
- Relevant examples provided

Areas for Improvement:
- Dive deeper into technical details
- Practice explaining complex concepts
- Add more real-world examples

Recommendations:
- Review advanced topics in your field
- Practice mock interviews
- Study best practices and design patterns
"""

    async def summarize_cv(self, cv_text: str) -> str:
        """Generate mock CV summary."""
        return "Mock CV summary: Experienced professional with strong technical skills in software development."

    async def extract_skills_from_text(self, text: str) -> list[dict[str, str]]:
        """Extract mock skills."""
        return [
            {"name": "Python", "category": "programming", "proficiency": "expert"},
            {"name": "FastAPI", "category": "framework", "proficiency": "advanced"},
            {"name": "PostgreSQL", "category": "database", "proficiency": "intermediate"},
        ]

    async def generate_ideal_answer(
        self,
        question_text: str,
        context: dict[str, Any],
    ) -> str:
        """Generate mock ideal answer."""
        return f"""Mock ideal answer for '{question_text[:50]}...':
This demonstrates comprehensive understanding of the concept with clear explanation,
relevant examples, and practical application. The answer covers all key aspects
including fundamental principles, real-world use cases, and potential edge cases."""

    async def generate_rationale(
        self,
        question_text: str,
        ideal_answer: str,
    ) -> str:
        """Generate mock rationale."""
        return """This answer demonstrates mastery by covering fundamental concepts,
providing practical examples, and explaining the reasoning behind technical choices.
A weaker answer would miss these comprehensive details."""

    async def detect_concept_gaps(
        self,
        answer_text: str,
        ideal_answer: str,
        question_text: str,
        keyword_gaps: list[str],
    ) -> dict[str, Any]:
        """Mock gap detection based on answer length.

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer
            question_text: The question that was asked
            keyword_gaps: Potential missing keywords from keyword analysis

        Returns:
            Dict with concept gap analysis
        """
        # Simple heuristic: short answers have gaps
        word_count = len(answer_text.split())

        if word_count < 30:
            # Simulate gaps for short answers
            return {
                "concepts": keyword_gaps[:2] if keyword_gaps else ["depth", "examples"],
                "keywords": keyword_gaps[:5],
                "confirmed": True,
                "severity": "moderate",
            }
        else:
            # Good answer, no gaps
            return {
                "concepts": [],
                "keywords": [],
                "confirmed": False,
                "severity": "minor",
            }

    async def generate_followup_question(
        self,
        parent_question: str,
        answer_text: str,
        missing_concepts: list[str],
        severity: str,
        order: int,
    ) -> str:
        """Mock follow-up question generation.

        Args:
            parent_question: Original question text
            answer_text: Candidate's answer to parent question
            missing_concepts: List of concepts missing from answer
            severity: Gap severity
            order: Follow-up order in sequence

        Returns:
            Follow-up question text
        """
        concepts_str = ', '.join(missing_concepts[:2]) if missing_concepts else "that concept"
        return f"Can you elaborate more on {concepts_str}? Please provide specific examples."
