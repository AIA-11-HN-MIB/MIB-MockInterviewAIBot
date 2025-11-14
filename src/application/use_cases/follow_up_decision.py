"""Follow-up decision logic use case."""

import logging
from typing import Any
from uuid import UUID

from ...domain.models.answer import Answer
from ...domain.models.evaluation import Evaluation
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from ...domain.ports.evaluation_repository_port import EvaluationRepositoryPort
from ...domain.ports.follow_up_question_repository_port import (
    FollowUpQuestionRepositoryPort,
)

logger = logging.getLogger(__name__)


class FollowUpDecisionUseCase:
    """Decide if follow-up question should be generated based on answer gaps.

    This use case implements the decision logic for adaptive follow-ups:
    1. Count existing follow-ups for parent question
    2. Check break conditions (max 3, similarity >= 0.8, no gaps)
    3. Accumulate gaps from all previous follow-up answers
    4. Return decision with context for follow-up generation
    """

    def __init__(
        self,
        answer_repository: AnswerRepositoryPort,
        evaluation_repository: EvaluationRepositoryPort,
        follow_up_question_repository: FollowUpQuestionRepositoryPort,
    ):
        """Initialize use case with required ports.

        Args:
            answer_repository: Answer storage
            evaluation_repository: Evaluation storage
            follow_up_question_repository: Follow-up question storage
        """
        self.answer_repo = answer_repository
        self.evaluation_repo = evaluation_repository
        self.follow_up_repo = follow_up_question_repository

    async def execute(
        self,
        interview_id: UUID,
        parent_question_id: UUID,
        latest_answer: Answer,
        latest_evaluation: Evaluation,
    ) -> dict[str, Any]:
        """Decide if follow-up needed and return decision details.

        Args:
            interview_id: Interview UUID
            parent_question_id: Parent question UUID (main question)
            latest_answer: Most recent answer (could be to follow-up)
            latest_evaluation: Most recent evaluation for the answer

        Returns:
            Decision dict with keys:
                - needs_followup: bool - Whether follow-up should be generated
                - reason: str - Explanation of decision
                - follow_up_count: int - Current count of follow-ups
                - cumulative_gaps: list[str] - All gaps across follow-up cycle
        """
        logger.info(
            f"Evaluating follow-up decision for question {parent_question_id}"
        )

        # Step 1: Count existing follow-ups for parent question
        follow_ups = await self.follow_up_repo.get_by_parent_question_id(
            parent_question_id
        )
        follow_up_count = len(follow_ups)
        logger.info(f"Found {follow_up_count} existing follow-ups")

        # Step 2: Check break condition - Max follow-ups reached
        # TODO: use domain instead
        if follow_up_count >= 3:
            logger.info("Break condition: Max follow-ups (3) reached")
            return {
                "needs_followup": False,
                "reason": "Max follow-ups (3) reached",
                "follow_up_count": follow_up_count,
                "cumulative_gaps": [],
            }

        # Step 3: Check break condition - Answer meets completion criteria
        if latest_evaluation.is_adaptive_complete():
            reason = "Answer meets completion criteria"
            if latest_evaluation.similarity_score and latest_evaluation.similarity_score >= 0.8:
                reason = f"Similarity score {latest_evaluation.similarity_score:.2f} >= 0.8"
            elif not latest_evaluation.has_gaps():
                reason = "No concept gaps detected"

            logger.info(f"Break condition: {reason}")
            return {
                "needs_followup": False,
                "reason": reason,
                "follow_up_count": follow_up_count,
                "cumulative_gaps": [],
            }

        # Step 4: Accumulate gaps from all follow-up answers
        cumulative_gaps = await self._accumulate_gaps(follow_ups, latest_evaluation)
        logger.info(f"Accumulated {len(cumulative_gaps)} unique concept gaps")

        # Step 5: Check if gaps exist - If no gaps, no follow-up needed
        if len(cumulative_gaps) == 0:
            logger.info("Break condition: No cumulative gaps detected")
            return {
                "needs_followup": False,
                "reason": "No cumulative gaps detected",
                "follow_up_count": follow_up_count,
                "cumulative_gaps": [],
            }

        # Step 6: Follow-up needed
        logger.info(f"Follow-up needed: {len(cumulative_gaps)} gaps to address")
        return {
            "needs_followup": True,
            "reason": f"Detected {len(cumulative_gaps)} missing concepts",
            "follow_up_count": follow_up_count,
            "cumulative_gaps": cumulative_gaps,
        }

    async def _accumulate_gaps(
        self,
        follow_ups: list[Any],
        latest_evaluation: Evaluation,
    ) -> list[str]:
        """Accumulate concept gaps from all follow-up answers.

        Args:
            follow_ups: List of follow-up questions for parent
            latest_evaluation: Most recent evaluation

        Returns:
            List of unique concept gaps across all answers
        """
        all_gaps = set()

        # Add gaps from latest evaluation
        for gap in latest_evaluation.gaps:
            if not gap.resolved:
                all_gaps.add(gap.concept)
        logger.debug(f"Latest evaluation contributes {len(all_gaps)} gaps")

        # Add gaps from previous follow-up evaluations
        for follow_up in follow_ups:
            # Fetch answer for this follow-up question
            prev_answer = await self.answer_repo.get_by_question_id(follow_up.id)
            if prev_answer and prev_answer.evaluation_id:
                prev_evaluation = await self.evaluation_repo.get_by_id(prev_answer.evaluation_id)
                if prev_evaluation:
                    for gap in prev_evaluation.gaps:
                        if not gap.resolved:
                            all_gaps.add(gap.concept)
                    logger.debug(f"Follow-up #{follow_up.order_in_sequence} contributes gaps")

        return list(all_gaps)
