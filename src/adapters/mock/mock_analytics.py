"""Mock Analytics adapter for development and testing."""

from collections import defaultdict
from typing import Any
from uuid import UUID

from ...domain.models.answer import Answer
from ...domain.models.question import Question
from ...domain.ports.analytics_port import AnalyticsPort


class MockAnalyticsAdapter(AnalyticsPort):
    """Mock analytics adapter that simulates performance tracking.

    This adapter provides in-memory analytics calculations without
    requiring external analytics services or databases.

    Storage is maintained in memory per instance, so each test
    should use a fresh instance for isolation.
    """

    def __init__(self) -> None:
        """Initialize mock analytics with empty storage."""
        # Store evaluations per interview
        self._evaluations: dict[UUID, list[Answer]] = defaultdict(list)

        # Store candidate history (mock historical data)
        self._candidate_history: dict[UUID, list[dict[str, Any]]] = {}

    async def record_answer_evaluation(
        self,
        interview_id: UUID,
        answer: Answer,
    ) -> None:
        """Record answer evaluation for analytics.

        Args:
            interview_id: Interview identifier
            answer: Answer with evaluation data
        """
        self._evaluations[interview_id].append(answer)

    async def get_interview_statistics(
        self,
        interview_id: UUID,
    ) -> dict[str, Any]:
        """Get statistics for an interview.

        Args:
            interview_id: Interview identifier

        Returns:
            Dictionary with interview statistics
        """
        answers = self._evaluations.get(interview_id, [])

        if not answers:
            return {
                "interview_id": str(interview_id),
                "question_count": 0,
                "answers_count": 0,
                "avg_score": 0.0,
                "completion_rate": 0.0,
                "time_spent_minutes": 0,
            }

        # Calculate average score
        scores = [
            a.evaluation.score
            for a in answers
            if a.evaluation is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Mock time calculation (2-5 min per question)
        time_spent = len(answers) * 3.5  # Average 3.5 minutes per answer

        return {
            "interview_id": str(interview_id),
            "question_count": len(answers),
            "answers_count": len([a for a in answers if a.text]),
            "avg_score": round(avg_score, 2),
            "completion_rate": round(len([a for a in answers if a.text]) / len(answers) * 100, 2) if answers else 0.0,
            "time_spent_minutes": round(time_spent, 1),
            "highest_score": max(scores) if scores else 0.0,
            "lowest_score": min(scores) if scores else 0.0,
        }

    async def get_candidate_performance_history(
        self,
        candidate_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get candidate's performance across all interviews.

        Args:
            candidate_id: Candidate identifier

        Returns:
            List of historical interview performance data
        """
        # Check if we have mock history for this candidate
        if candidate_id in self._candidate_history:
            return self._candidate_history[candidate_id]

        # Generate mock historical data (0-3 past interviews)
        # Simulate improvement over time
        history = []
        num_past_interviews = 2  # Mock: 2 past interviews

        for i in range(num_past_interviews):
            history.append({
                "interview_date": f"2024-{10-i:02d}-15",
                "avg_score": round(65.0 + (i * 8.0), 2),  # Improving scores
                "questions_answered": 5 + i,
                "completion_rate": round(80.0 + (i * 10.0), 2),
                "strong_skills": ["Python", "SQL"] if i == 0 else ["Python", "FastAPI", "PostgreSQL"],
                "weak_skills": ["System Design", "Architecture"] if i == 0 else ["System Design"],
            })

        self._candidate_history[candidate_id] = history
        return history

    async def generate_improvement_recommendations(
        self,
        interview_id: UUID,
        questions: list[Question],
        answers: list[Answer],
    ) -> list[str]:
        """Generate improvement recommendations based on performance.

        Args:
            interview_id: Interview identifier
            questions: Questions asked
            answers: Answers with evaluations

        Returns:
            List of improvement recommendations
        """
        if not answers:
            return ["Complete the interview to receive personalized recommendations"]

        # Calculate average score
        scores = [
            a.evaluation.score
            for a in answers
            if a.evaluation is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Collect weaknesses from evaluations
        all_weaknesses = []
        weak_skills = []

        for answer, question in zip(answers, questions, strict=True):
            if answer.evaluation:
                all_weaknesses.extend(answer.evaluation.weaknesses)

                # Track skills with low scores (<70)
                if answer.evaluation.score < 70.0:
                    weak_skills.extend(question.skills)

        # Deduplicate and count weaknesses
        weakness_counts: dict[str, int] = defaultdict(int)
        for weakness in all_weaknesses:
            weakness_counts[weakness] += 1

        # Sort by frequency
        top_weaknesses = sorted(
            weakness_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Generate recommendations based on score ranges
        recommendations = []

        if avg_score < 60:
            recommendations.append("Focus on understanding fundamental concepts before diving into advanced topics")
            recommendations.append("Practice explaining technical concepts clearly and concisely")
            recommendations.append("Review and strengthen basic knowledge in your core skills")

            # Add specific weakness-based recommendations
            for weakness, _ in top_weaknesses[:2]:
                if "depth" in weakness.lower():
                    recommendations.append("Study topics in more depth with practical examples")
                elif "example" in weakness.lower():
                    recommendations.append("Prepare concrete examples from your experience")

        elif avg_score < 80:
            recommendations.append("Strengthen your understanding of intermediate concepts")
            recommendations.append("Practice providing more detailed and structured answers")

            # Add skill-specific recommendations
            if weak_skills:
                unique_weak_skills = list(set(weak_skills))[:2]
                for skill in unique_weak_skills:
                    recommendations.append(f"Improve your knowledge in {skill} through hands-on projects")

            # Add weakness-based recommendations
            for weakness, _ in top_weaknesses[:2]:
                recommendations.append(f"Work on: {weakness}")

        else:
            recommendations.append("Excellent performance! Continue building expertise in advanced topics")
            recommendations.append("Consider exploring cutting-edge technologies and patterns")

            # Even high performers can improve
            if top_weaknesses:
                recommendations.append(f"Minor area for growth: {top_weaknesses[0][0]}")

        # Limit to 3-5 recommendations
        return recommendations[:5]

    async def calculate_skill_scores(
        self,
        answers: list[Answer],
        questions: list[Question],
    ) -> dict[str, float]:
        """Calculate scores per skill based on answers.

        Args:
            answers: List of evaluated answers
            questions: Corresponding questions

        Returns:
            Dictionary mapping skill names to average scores
        """
        if not answers or not questions or len(answers) != len(questions):
            return {}

        # Group scores by skill
        skill_scores: dict[str, list[float]] = defaultdict(list)

        for answer, question in zip(answers, questions, strict=True):
            if answer.evaluation is None:
                continue

            score = answer.evaluation.score

            # Associate this score with all skills in the question
            for skill in question.skills:
                skill_scores[skill].append(score)

        # Calculate average score per skill
        result = {}
        for skill, scores in skill_scores.items():
            result[skill] = round(sum(scores) / len(scores), 2)

        return result
