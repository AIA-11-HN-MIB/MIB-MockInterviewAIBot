"""Generate comprehensive interview summary use case."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ...domain.models.answer import Answer
from ...domain.models.evaluation import Evaluation
from ...domain.models.interview import Interview
from ...domain.models.question import Question
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from ...domain.ports.evaluation_repository_port import EvaluationRepositoryPort
from ...domain.ports.follow_up_question_repository_port import (
    FollowUpQuestionRepositoryPort,
)
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.llm_port import LLMPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort


class GenerateSummaryUseCase:
    """Generate comprehensive interview summary.

    .. deprecated::
        Use :class:`CompleteInterviewUseCase` instead.
        This use case is deprecated and will be removed in the next major version.

    DEPRECATED: This use case has been merged into CompleteInterviewUseCase.
    Summary generation is now part of the atomic interview completion operation.

    Migration Guide:
        Replace GenerateSummaryUseCase with CompleteInterviewUseCase.
        The new use case handles both completion and summary generation together.

    Reason for Deprecation:
        Eliminates use case composition anti-pattern. Interview completion and
        summary generation are inherently related operations that should execute
        atomically, not as separate use cases.

    Aggregates all evaluations (main questions + follow-ups), analyzes gap
    progression, and generates personalized recommendations using LLM.
    """

    def __init__(
        self,
        interview_repository: InterviewRepositoryPort,
        answer_repository: AnswerRepositoryPort,
        question_repository: QuestionRepositoryPort,
        follow_up_question_repository: FollowUpQuestionRepositoryPort,
        evaluation_repository: EvaluationRepositoryPort,
        llm: LLMPort,
    ):
        import warnings

        warnings.warn(
            "GenerateSummaryUseCase is deprecated. "
            "Use CompleteInterviewUseCase instead. "
            "This class will be removed in the next major version.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.interview_repo = interview_repository
        self.answer_repo = answer_repository
        self.question_repo = question_repository
        self.follow_up_repo = follow_up_question_repository
        self.evaluation_repo = evaluation_repository
        self.llm = llm

    async def execute(self, interview_id: UUID) -> dict[str, Any]:
        """Generate comprehensive summary.

        Args:
            interview_id: Interview UUID

        Returns:
            dict containing:
                - interview_id: UUID
                - overall_score: float (weighted avg of all evaluations)
                - theoretical_score_avg: float
                - speaking_score_avg: float
                - total_questions: int (main questions only)
                - total_follow_ups: int
                - question_summaries: list[dict] (per-question analysis)
                - gap_progression: dict (how gaps changed after follow-ups)
                - strengths: list[str]
                - weaknesses: list[str]
                - study_recommendations: list[str]
                - technique_tips: list[str]
                - completion_time: datetime

        Raises:
            ValueError: If interview not found
        """
        # Fetch interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        # Fetch all answers (main + follow-ups)
        all_answers = await self.answer_repo.get_by_interview_id(interview_id)

        # Load evaluations for all answers from evaluations table
        evaluations_map = await self._load_evaluations(all_answers)

        # Group answers by main question
        question_groups = await self._group_answers_by_main_question(interview, all_answers)

        # Calculate aggregate metrics using evaluations
        metrics = self._calculate_aggregate_metrics(all_answers, evaluations_map)

        # Analyze gap progression using evaluations
        gap_progression = await self._analyze_gap_progression(question_groups, evaluations_map)

        # Generate LLM-powered recommendations using evaluations
        recommendations = await self._generate_recommendations(
            interview, all_answers, gap_progression, evaluations_map
        )

        return {
            "interview_id": str(interview_id),
            "overall_score": metrics["overall_score"],
            "theoretical_score_avg": metrics["theoretical_avg"],
            "speaking_score_avg": metrics["speaking_avg"],
            "total_questions": len(interview.question_ids),
            "total_follow_ups": len(interview.adaptive_follow_ups),
            "question_summaries": await self._create_question_summaries(question_groups, evaluations_map),
            "gap_progression": gap_progression,
            "strengths": recommendations["strengths"],
            "weaknesses": recommendations["weaknesses"],
            "study_recommendations": recommendations["study_topics"],
            "technique_tips": recommendations["technique_tips"],
            "completion_time": datetime.now(timezone.utc).isoformat(),
        }

    async def _group_answers_by_main_question(
        self,
        interview: Interview,
        all_answers: list[Answer],
    ) -> dict[UUID, dict[str, Any]]:
        """Group answers by main question with follow-ups.

        Args:
            interview: Interview entity
            all_answers: All answers (main + follow-ups)

        Returns:
            Dict mapping main_question_id to:
                - question: Main question entity
                - main_answer: Answer to main question
                - follow_ups: List of follow-up question entities
                - follow_up_answers: List of answers to follow-ups
        """
        groups = {}

        for main_question_id in interview.question_ids:
            main_question = await self.question_repo.get_by_id(main_question_id)

            # Find main answer
            main_answer = next(
                (a for a in all_answers if a.question_id == main_question_id),
                None,
            )

            # Find follow-up answers
            follow_ups = await self.follow_up_repo.get_by_parent_question_id(main_question_id)
            follow_up_answers = [
                next((a for a in all_answers if a.question_id == fu.id), None) for fu in follow_ups
            ]

            groups[main_question_id] = {
                "question": main_question,
                "main_answer": main_answer,
                "follow_ups": follow_ups,
                "follow_up_answers": [a for a in follow_up_answers if a is not None],
            }

        return groups

    async def _load_evaluations(self, answers: list[Answer]) -> dict[UUID, Evaluation]:
        """Load evaluations for all answers from evaluations table.

        Args:
            answers: List of answers

        Returns:
            Dict mapping answer_id to Evaluation
        """
        evaluations_map = {}
        for answer in answers:
            if answer.evaluation_id:
                evaluation = await self.evaluation_repo.get_by_id(answer.evaluation_id)
                if evaluation:
                    evaluations_map[answer.id] = evaluation
        return evaluations_map

    def _calculate_aggregate_metrics(
        self,
        all_answers: list[Answer],
        evaluations_map: dict[UUID, Evaluation]
    ) -> dict[str, float]:
        """Calculate aggregate scores using evaluations from evaluations table.

        Args:
            all_answers: All answers (main + follow-ups)
            evaluations_map: Dict mapping answer_id to Evaluation

        Returns:
            Dict with keys:
                - overall_score: Weighted average (70% theoretical + 30% speaking)
                - theoretical_avg: Average of theoretical scores
                - speaking_avg: Average of speaking scores
        """
        evaluated_answers = [
            a for a in all_answers
            if a.is_evaluated() and a.id in evaluations_map
        ]

        if not evaluated_answers:
            return {
                "overall_score": 0.0,
                "theoretical_avg": 0.0,
                "speaking_avg": 0.0,
            }

        # Theoretical score (from evaluation in evaluations table)
        theoretical_scores = [
            evaluations_map[a.id].final_score
            for a in evaluated_answers
            if a.id in evaluations_map
        ]

        # Speaking score (from voice metrics)
        speaking_scores = [
            a.voice_metrics.get("overall_score", 50.0) for a in evaluated_answers if a.voice_metrics
        ]

        # If no voice metrics, default to 50.0
        speaking_avg = sum(speaking_scores) / len(speaking_scores) if speaking_scores else 50.0

        theoretical_avg = sum(theoretical_scores) / len(theoretical_scores)

        # Overall = 70% theoretical + 30% speaking
        overall_score = (theoretical_avg * 0.7) + (speaking_avg * 0.3)

        return {
            "overall_score": round(overall_score, 2),
            "theoretical_avg": round(theoretical_avg, 2),
            "speaking_avg": round(speaking_avg, 2),
        }

    async def _analyze_gap_progression(
        self,
        question_groups: dict[UUID, dict[str, Any]],
        evaluations_map: dict[UUID, Evaluation]
    ) -> dict[str, Any]:
        """Analyze how gaps changed after follow-ups using evaluations table.

        Args:
            question_groups: Grouped answers by main question
            evaluations_map: Dict mapping answer_id to Evaluation

        Returns:
            Dict with keys:
                - questions_with_followups: int
                - gaps_filled: int (concepts mastered after follow-ups)
                - gaps_remaining: int (concepts still missing)
                - avg_followups_per_question: float
        """
        progression = {
            "questions_with_followups": 0,
            "gaps_filled": 0,
            "gaps_remaining": 0,
            "avg_followups_per_question": 0.0,
        }

        questions_with_followups = 0
        total_followups = 0
        gaps_filled = 0
        gaps_remaining = 0

        for group in question_groups.values():
            main_answer = group["main_answer"]
            follow_up_answers = group["follow_up_answers"]

            if not follow_up_answers or not main_answer:
                continue

            questions_with_followups += 1
            total_followups += len(follow_up_answers)

            # Get initial gaps from main answer's evaluation in evaluations table
            initial_gaps = set()
            if main_answer.id in evaluations_map:
                main_evaluation = evaluations_map[main_answer.id]
                initial_gaps = {gap.concept for gap in main_evaluation.gaps if not gap.resolved}

            # Get final gaps from last follow-up answer's evaluation in evaluations table
            final_answer = follow_up_answers[-1]
            final_gaps = set()
            if final_answer.id in evaluations_map:
                final_evaluation = evaluations_map[final_answer.id]
                final_gaps = {gap.concept for gap in final_evaluation.gaps if not gap.resolved}

            gaps_filled += len(initial_gaps - final_gaps)
            gaps_remaining += len(final_gaps)

        progression["questions_with_followups"] = questions_with_followups
        progression["gaps_filled"] = gaps_filled
        progression["gaps_remaining"] = gaps_remaining
        progression["avg_followups_per_question"] = (
            round(total_followups / questions_with_followups, 2)
            if questions_with_followups > 0
            else 0.0
        )

        return progression

    async def _generate_recommendations(
        self,
        interview: Interview,
        all_answers: list[Answer],
        gap_progression: dict[str, Any],
        evaluations_map: dict[UUID, Evaluation],
    ) -> dict[str, list[str]]:
        """Use LLM to generate personalized recommendations using evaluations table.

        Args:
            interview: Interview entity
            all_answers: All answers
            gap_progression: Gap progression analysis
            evaluations_map: Dict mapping answer_id to Evaluation

        Returns:
            Dict with keys:
                - strengths: list[str] (top 3-5 strengths)
                - weaknesses: list[str] (top 3-5 weaknesses)
                - study_topics: list[str] (topic-specific recommendations)
                - technique_tips: list[str] (voice, pacing, structure tips)
        """
        context = {
            "interview_id": str(interview.id),
            "total_answers": len(all_answers),
            "gap_progression": gap_progression,
            "evaluations": [
                {
                    "question_id": str(a.question_id),
                    "score": evaluations_map[a.id].final_score,
                    "strengths": evaluations_map[a.id].strengths,
                    "weaknesses": evaluations_map[a.id].weaknesses,
                }
                for a in all_answers
                if a.is_evaluated() and a.id in evaluations_map
            ],
        }

        return await self.llm.generate_interview_recommendations(context)

    async def _create_question_summaries(
        self,
        question_groups: dict[UUID, dict[str, Any]],
        evaluations_map: dict[UUID, Evaluation]
    ) -> list[dict[str, Any]]:
        """Create per-question analysis using evaluations table.

        Args:
            question_groups: Grouped answers by main question
            evaluations_map: Dict mapping answer_id to Evaluation

        Returns:
            List of dicts with keys:
                - question_id: UUID
                - question_text: str
                - main_answer_score: float
                - follow_up_count: int
                - initial_gaps: list[str]
                - final_gaps: list[str]
                - improvement: bool (whether gaps were filled)
        """
        summaries = []

        for main_question_id, group in question_groups.items():
            question = group["question"]
            main_answer = group["main_answer"]
            follow_up_answers = group["follow_up_answers"]

            # Get initial gaps from main answer's evaluation in evaluations table
            initial_gaps = []
            if main_answer and main_answer.id in evaluations_map:
                main_evaluation = evaluations_map[main_answer.id]
                initial_gaps = [gap.concept for gap in main_evaluation.gaps if not gap.resolved]

            final_gaps = initial_gaps

            if follow_up_answers:
                final_answer = follow_up_answers[-1]
                if final_answer.id in evaluations_map:
                    final_evaluation = evaluations_map[final_answer.id]
                    final_gaps = [gap.concept for gap in final_evaluation.gaps if not gap.resolved]

            main_answer_score = 0.0
            if main_answer and main_answer.id in evaluations_map:
                main_answer_score = evaluations_map[main_answer.id].final_score

            summaries.append(
                {
                    "question_id": str(main_question_id),
                    "question_text": question.text if question else "Unknown",
                    "main_answer_score": main_answer_score,
                    "follow_up_count": len(follow_up_answers),
                    "initial_gaps": initial_gaps,
                    "final_gaps": final_gaps,
                    "improvement": len(final_gaps) < len(initial_gaps),
                }
            )

        return summaries
