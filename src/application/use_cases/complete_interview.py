"""Complete interview use case."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ...domain.models.answer import Answer
from ...domain.models.evaluation import Evaluation
from ...domain.models.interview import Interview, InterviewStatus
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from ...domain.ports.evaluation_repository_port import EvaluationRepositoryPort
from ...domain.ports.follow_up_question_repository_port import (
    FollowUpQuestionRepositoryPort,
)
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.llm_port import LLMPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort
from ..dto.detailed_feedback_dto import (
    ConceptGapDetail,
    DetailedInterviewFeedback,
    EvaluationDetail,
    QuestionDetailedFeedback,
)
from ..dto.interview_completion_dto import InterviewCompletionResult


class CompleteInterviewUseCase:
    """Complete interview and generate comprehensive summary (atomic operation).

    This use case handles both interview completion state transition and
    comprehensive summary generation as a single atomic operation. All
    dependencies are required (no optional parameters).

    The summary generation logic is inlined from the former GenerateSummaryUseCase
    to eliminate use case composition anti-pattern and ensure atomic execution.
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
        """Initialize with all required dependencies.

        Args:
            interview_repository: Interview persistence port
            answer_repository: Answer persistence port
            question_repository: Question persistence port
            follow_up_question_repository: Follow-up question persistence port
            evaluation_repository: Evaluation persistence port
            llm: LLM port for generating recommendations
        """
        self.interview_repo = interview_repository
        self.answer_repo = answer_repository
        self.question_repo = question_repository
        self.follow_up_repo = follow_up_question_repository
        self.evaluation_repo = evaluation_repository
        self.llm = llm

    async def execute(self, interview_id: UUID) -> InterviewCompletionResult:
        """Complete interview and generate comprehensive summary.

        This method:
        1. Validates interview is in EVALUATING status
        2. Generates comprehensive summary (scores, gaps, recommendations)
        3. Stores summary in interview metadata
        4. Transitions interview to COMPLETE status
        5. Returns both interview and summary

        Args:
            interview_id: The interview UUID

        Returns:
            InterviewCompletionResult containing completed interview and summary

        Raises:
            ValueError: If interview not found or not in EVALUATING status
        """
        # 1. Load and validate interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.EVALUATING:
            raise ValueError(
                f"Cannot complete interview with status: {interview.status}. "
                f"Must be in EVALUATING status."
            )

        # 2. Generate comprehensive summary
        summary = await self._generate_summary(interview)

        # 3. Store summary in interview metadata
        if interview.plan_metadata is None:
            interview.plan_metadata = {}
        interview.plan_metadata["completion_summary"] = summary

        # 4. Mark interview as complete (state transition)
        interview.complete()
        updated_interview = await self.interview_repo.update(interview)

        # 5. Return result DTO
        return InterviewCompletionResult(
            interview=updated_interview,
            summary=summary,
        )

    async def _generate_summary(self, interview: Interview) -> DetailedInterviewFeedback:
        """Generate comprehensive interview summary with detailed DTOs.

        Aggregates all evaluations (main questions + follow-ups), analyzes gap
        progression, and generates personalized recommendations using LLM.

        Args:
            interview: Interview entity

        Returns:
            DetailedInterviewFeedback DTO with complete evaluation details
        """
        # Fetch all answers (main + follow-ups)
        all_answers = await self.answer_repo.get_by_interview_id(interview.id)

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

        # Create detailed per-question feedback
        question_feedback = await self._create_question_detailed_feedback(
            question_groups, evaluations_map
        )

        return DetailedInterviewFeedback(
            interview_id=interview.id,
            overall_score=metrics["overall_score"],
            theoretical_score_avg=metrics["theoretical_avg"],
            speaking_score_avg=metrics["speaking_avg"],
            total_questions=len(interview.question_ids),
            total_follow_ups=len(interview.adaptive_follow_ups),
            question_feedback=question_feedback,
            gap_progression=gap_progression,
            strengths=recommendations["strengths"],
            weaknesses=recommendations["weaknesses"],
            study_recommendations=recommendations["study_topics"],
            technique_tips=recommendations["technique_tips"],
            completion_time=datetime.now(UTC),
        )

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
                next((a for a in all_answers if a.question_id == fu.id), None)
                for fu in follow_ups
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
        evaluations_map: dict[UUID, Evaluation],
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
            a for a in all_answers if a.is_evaluated() and a.id in evaluations_map
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
            a.voice_metrics.get("overall_score", 50.0)
            for a in evaluated_answers
            if a.voice_metrics
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
        evaluations_map: dict[UUID, Evaluation],
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

    async def _create_question_detailed_feedback(
        self,
        question_groups: dict[UUID, dict[str, Any]],
        evaluations_map: dict[UUID, Evaluation],
    ) -> list[QuestionDetailedFeedback]:
        """Create detailed per-question feedback using strongly-typed DTOs.

        Args:
            question_groups: Grouped answers by main question
            evaluations_map: Dict mapping answer_id to Evaluation

        Returns:
            List of QuestionDetailedFeedback DTOs with complete evaluation details
        """
        feedback_list = []

        for main_question_id, group in question_groups.items():
            question = group["question"]
            main_answer = group["main_answer"]
            follow_up_answers = group["follow_up_answers"]
            follow_ups = group["follow_ups"]

            # Skip if no main answer
            if not main_answer or main_answer.id not in evaluations_map:
                continue

            # Build main evaluation detail
            main_eval = evaluations_map[main_answer.id]
            main_evaluation_detail = self._build_evaluation_detail(
                answer=main_answer,
                evaluation=main_eval,
                question_text=question.text if question else "Unknown",
            )

            # Build follow-up evaluation details
            follow_up_evaluation_details = []
            for fu_answer, fu_question in zip(follow_up_answers, follow_ups):
                if fu_answer.id in evaluations_map:
                    fu_eval = evaluations_map[fu_answer.id]
                    fu_detail = self._build_evaluation_detail(
                        answer=fu_answer,
                        evaluation=fu_eval,
                        question_text=fu_question.text if fu_question else "Follow-up",
                    )
                    follow_up_evaluation_details.append(fu_detail)

            # Calculate score progression
            score_progression = [main_eval.final_score]
            score_progression.extend(
                [
                    evaluations_map[fu_answer.id].final_score
                    for fu_answer in follow_up_answers
                    if fu_answer.id in evaluations_map
                ]
            )

            # Calculate gap filled count
            initial_gaps = {gap.concept for gap in main_eval.gaps if not gap.resolved}
            final_gaps = initial_gaps
            if follow_up_answers:
                last_fu_answer = follow_up_answers[-1]
                if last_fu_answer.id in evaluations_map:
                    last_fu_eval = evaluations_map[last_fu_answer.id]
                    final_gaps = {gap.concept for gap in last_fu_eval.gaps if not gap.resolved}
            gap_filled_count = len(initial_gaps - final_gaps)

            # Create QuestionDetailedFeedback DTO
            question_feedback = QuestionDetailedFeedback(
                question_id=main_question_id,
                question_text=question.text if question else "Unknown",
                main_evaluation=main_evaluation_detail,
                follow_up_evaluations=follow_up_evaluation_details,
                score_progression=score_progression,
                gap_filled_count=gap_filled_count,
            )

            feedback_list.append(question_feedback)

        return feedback_list

    def _build_evaluation_detail(
        self,
        answer: Answer,
        evaluation: Evaluation,
        question_text: str,
    ) -> EvaluationDetail:
        """Build EvaluationDetail DTO from domain entities.

        Args:
            answer: Answer entity
            evaluation: Evaluation entity
            question_text: Full text of question

        Returns:
            EvaluationDetail DTO with complete evaluation data
        """
        # Convert ConceptGap entities to ConceptGapDetail DTOs
        gap_details = [
            ConceptGapDetail(
                concept=gap.concept,
                severity=gap.severity.value,
                resolved=gap.resolved,
            )
            for gap in evaluation.gaps
        ]

        return EvaluationDetail(
            answer_id=answer.id,
            question_id=evaluation.question_id,
            question_text=question_text,
            attempt_number=evaluation.attempt_number,
            raw_score=evaluation.raw_score,
            penalty=evaluation.penalty,
            final_score=evaluation.final_score,
            similarity_score=evaluation.similarity_score,
            completeness=evaluation.completeness,
            relevance=evaluation.relevance,
            sentiment=evaluation.sentiment,
            reasoning=evaluation.reasoning,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            improvement_suggestions=evaluation.improvement_suggestions,
            gaps=gap_details,
            evaluated_at=evaluation.evaluated_at,
        )
