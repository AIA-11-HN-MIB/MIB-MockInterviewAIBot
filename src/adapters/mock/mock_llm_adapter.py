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
        cumulative_gaps: list[str] | None = None,
        previous_follow_ups: list[dict[str, Any]] | None = None,
    ) -> str:
        """Mock follow-up question generation with cumulative context.

        Args:
            parent_question: Original question text
            answer_text: Candidate's answer to parent question (or latest follow-up)
            missing_concepts: List of concepts missing from current answer
            severity: Gap severity
            order: Follow-up order in sequence
            cumulative_gaps: All unique gaps accumulated across follow-up cycle
            previous_follow_ups: Previous follow-up questions and answers for context

        Returns:
            Follow-up question text
        """
        # Use cumulative gaps if available, otherwise current missing concepts
        target_concepts = cumulative_gaps if cumulative_gaps else missing_concepts
        concepts_str = ', '.join(target_concepts[:2]) if target_concepts else "that concept"

        # Add order context to make questions unique per iteration
        if order == 1:
            return f"Can you elaborate more on {concepts_str}? Please provide specific examples."
        elif order == 2:
            return f"Let's dive deeper into {concepts_str}. Can you explain the underlying principles?"
        else:
            return f"Final question on {concepts_str}: How would you apply this in a real-world scenario?"

    async def generate_interview_recommendations(
        self,
        context: dict[str, Any],
    ) -> dict[str, list[str]]:
        """Generate mock personalized recommendations.

        Args:
            context: Interview context with evaluations and gap progression

        Returns:
            Dict with strengths, weaknesses, study topics, and technique tips
        """
        evaluations = context.get("evaluations", [])
        gap_progression = context.get("gap_progression", {})

        # Calculate average score from evaluations
        avg_score = (
            sum(e["score"] for e in evaluations) / len(evaluations)
            if evaluations
            else 75.0
        )

        # Generate recommendations based on score
        if avg_score >= 85:
            strengths = [
                "Exceptional understanding of core concepts",
                "Strong analytical and problem-solving skills",
                "Excellent communication and explanation abilities",
                "Good use of real-world examples and context",
            ]
            weaknesses = [
                "Could explore more edge cases in answers",
                "Consider discussing performance trade-offs more explicitly",
            ]
            study_topics = [
                "Advanced system design patterns",
                "Performance optimization techniques",
                "Security best practices",
            ]
            technique_tips = [
                "Continue your clear and structured communication style",
                "Consider adding more visual diagrams when explaining concepts",
            ]
        elif avg_score >= 70:
            strengths = [
                "Solid understanding of fundamental concepts",
                "Good ability to explain technical topics",
                "Relevant examples provided in most answers",
            ]
            weaknesses = [
                "Some technical depth missing in complex topics",
                "Could improve answer structure and organization",
                "Occasionally missed key concepts in follow-up questions",
            ]
            study_topics = [
                "Deep dive into data structures and algorithms",
                "Practice system design scenarios",
                "Review concurrency and threading concepts",
                "Study testing strategies and best practices",
            ]
            technique_tips = [
                "Use the STAR method (Situation, Task, Action, Result) for answering",
                "Practice explaining concepts at multiple levels of detail",
                "Slow down pace to ensure clarity in responses",
            ]
        else:
            strengths = [
                "Shows basic understanding of core concepts",
                "Willing to tackle challenging questions",
            ]
            weaknesses = [
                "Lacks depth in technical explanations",
                "Missing critical concepts in several answers",
                "Limited use of examples and practical applications",
                "Answer structure needs improvement",
            ]
            study_topics = [
                "Review fundamental programming concepts thoroughly",
                "Practice basic data structures and algorithms",
                "Study common design patterns",
                "Build small projects to reinforce learning",
                "Review language-specific best practices",
            ]
            technique_tips = [
                "Practice explaining concepts out loud before answering",
                "Use pen and paper to diagram ideas during preparation",
                "Structure answers: state the concept, explain it, give an example",
                "Take time to think before responding - silence is acceptable",
                "Ask clarifying questions if prompt is unclear",
            ]

        # Add gap-specific recommendations
        if gap_progression.get("gaps_remaining", 0) > 3:
            study_topics.append(
                "Focus on concepts that remained unclear after follow-up questions"
            )

        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "study_topics": study_topics,
            "technique_tips": technique_tips,
        }
