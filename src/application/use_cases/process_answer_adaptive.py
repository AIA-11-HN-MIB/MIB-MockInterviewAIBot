"""Process answer with adaptive follow-up logic - Phase 2 complete."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.models.answer import Answer
from ...domain.models.evaluation import Evaluation, ConceptGap, GapSeverity, FollowUpEvaluationContext
from ...domain.models.interview import InterviewStatus
from ...domain.models.question import Question
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
from ...domain.ports.evaluation_repository_port import EvaluationRepositoryPort
from ...domain.ports.follow_up_question_repository_port import (
    FollowUpQuestionRepositoryPort,
)
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.llm_port import LLMPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort
from ...domain.ports.vector_search_port import VectorSearchPort

logger = logging.getLogger(__name__)


class ProcessAnswerAdaptiveUseCase:
    """Process answer with adaptive evaluation and follow-up generation.

    Phase 2 complete:
    - Uses separate Evaluation entity with structured gap tracking
    - Context-aware evaluation for follow-up questions
    - Attempt-based penalty system: 0/-5/-15 for attempts 1/2/3
    - Automatic gap resolution when criteria met
    """

    def __init__(
        self,
        answer_repository: AnswerRepositoryPort,
        evaluation_repository: EvaluationRepositoryPort,
        interview_repository: InterviewRepositoryPort,
        question_repository: QuestionRepositoryPort,
        follow_up_question_repository: FollowUpQuestionRepositoryPort,
        llm: LLMPort,
        vector_search: VectorSearchPort,
    ):
        """Initialize use case with required ports.

        Args:
            answer_repository: Answer storage
            evaluation_repository: Evaluation storage (NEW in Phase 1)
            interview_repository: Interview storage
            question_repository: Question storage
            follow_up_question_repository: Follow-up question storage
            llm: LLM service for evaluation and gap detection
            vector_search: Vector database for similarity calculation
        """
        self.answer_repo = answer_repository
        self.evaluation_repo = evaluation_repository
        self.interview_repo = interview_repository
        self.question_repo = question_repository
        self.follow_up_question_repo = follow_up_question_repository
        self.llm = llm
        self.vector_search = vector_search

    async def execute(
        self,
        interview_id: UUID,
        question_id: UUID,
        answer_text: str,
        audio_file_path: str | None = None,
        voice_metrics: dict[str, float] | None = None,
    ) -> tuple[Answer, Evaluation, bool]:
        """Process answer with adaptive evaluation.

        Phase 2: Context-aware evaluation with penalties and gap resolution.

        For main questions (attempt 1):
        - Standard evaluation, no penalty
        - Detects concept gaps

        For follow-up questions (attempts 2-3):
        - Builds context with previous evaluations and cumulative gaps
        - Passes context to LLM for smarter evaluation
        - Applies penalty: -5 (2nd attempt), -15 (3rd attempt)
        - Resolves gaps if: completeness >= 0.8 OR score >= 80 OR attempt == 3

        Args:
            interview_id: The interview UUID
            question_id: The question UUID (main or follow-up)
            answer_text: The answer text
            audio_file_path: Optional audio file path for voice answers
            voice_metrics: Optional voice quality metrics from STT

        Returns:
            Tuple of (Answer, Evaluation, has_more_questions)

        Raises:
            ValueError: If interview or question not found, or invalid state
        """
        logger.info(
            "Processing adaptive answer",
            extra={"interview_id": str(interview_id), "question_id": str(question_id)},
        )

        # Step 1: Validate interview
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.EVALUATING:
            raise ValueError(f"Interview not in progress: {interview.status}")

        # Step 2: Detect if this is a follow-up question
        is_followup, parent_question_id = await self._is_followup_question(question_id)

        # Step 3: Get question (main or follow-up parent)
        if is_followup:
            question = await self._get_follow_up_question(question_id)
        else:
            question = await self._get_question(question_id)

        # Step 4: Build follow-up context if applicable
        followup_context = None
        if is_followup and parent_question_id:
            followup_context = await self._build_followup_context(
                question_id=question_id,
                parent_question_id=parent_question_id,
                parent_ideal_answer=question.ideal_answer or "",
            )

        # Step 5: Create answer (simplified - no embedded evaluation)
        # For follow-up questions, use parent_question_id to satisfy foreign key constraint
        # The follow-up question ID will be tracked in the Evaluation instead
        answer_question_id = parent_question_id if is_followup else question_id

        answer = Answer(
            interview_id=interview_id,
            question_id=answer_question_id,  # Use parent question ID for follow-ups
            candidate_id=interview.candidate_id,
            text=answer_text,
            is_voice=bool(audio_file_path),
            audio_file_path=audio_file_path,
            voice_metrics=voice_metrics,
            created_at=datetime.utcnow(),
        )

        # Step 6: Evaluate answer using LLM (with follow-up context if applicable)
        llm_eval = await self.llm.evaluate_answer(
            question=question,
            answer_text=answer_text,
            context={
                "interview_id": str(interview_id),
                "candidate_id": str(interview.candidate_id),
            },
            followup_context=followup_context,
        )

        # Step 7: Calculate similarity (if ideal_answer exists)
        similarity_score = None
        if question.has_ideal_answer():
            similarity_score = await self._calculate_similarity(
                answer_text, question.ideal_answer
            )
            logger.info(f"Similarity score: {similarity_score:.2f}")

        # Step 6: Detect gaps
        gaps_dict = await self._detect_gaps_hybrid(
            answer_text=answer_text,
            ideal_answer=question.ideal_answer or "",
            question_text=question.text,
        )

        # Step 9: Determine attempt number and parent evaluation
        attempt_number = followup_context.attempt_number if followup_context else 1
        parent_evaluation_id = (
            followup_context.previous_evaluations[0].id
            if followup_context and followup_context.previous_evaluations
            else None
        )

        # Step 10: Create Evaluation entity
        evaluation = Evaluation(
            answer_id=answer.id,  # Will link after saving answer
            question_id=question_id,  # Keep follow-up question ID here (no FK constraint)
            interview_id=interview_id,
            raw_score=llm_eval.score,
            penalty=0.0,  # Will be set by apply_penalty()
            final_score=llm_eval.score,  # Will be recalculated by apply_penalty()
            similarity_score=similarity_score,
            completeness=llm_eval.completeness,
            relevance=llm_eval.relevance,
            sentiment=llm_eval.sentiment,
            reasoning=llm_eval.reasoning,
            strengths=llm_eval.strengths,
            weaknesses=llm_eval.weaknesses,
            improvement_suggestions=llm_eval.improvement_suggestions,
            attempt_number=attempt_number,
            parent_evaluation_id=parent_evaluation_id,
            gaps=[
                ConceptGap(
                    evaluation_id=answer.id,  # Temporary, will be updated
                    concept=concept,
                    severity=self._determine_gap_severity(concept, gaps_dict),
                    resolved=False,
                    created_at=datetime.utcnow(),
                )
                for concept in gaps_dict.get("concepts", [])
            ],
            evaluated_at=datetime.utcnow(),
        )

        # Step 11: Apply penalty based on attempt number
        evaluation.apply_penalty(attempt_number)

        # Step 12: Check if gaps should be resolved
        if evaluation.is_gap_resolved_by_criteria():
            evaluation.resolve_gaps()
            logger.info(
                f"Gaps resolved by criteria: completeness={evaluation.completeness:.2f}, "
                f"final_score={evaluation.final_score:.1f}, attempt={attempt_number}"
            )

        # Step 8: Save answer first (to get ID)
        saved_answer = await self.answer_repo.save(answer)

        # Step 9: Update evaluation with correct answer_id
        evaluation.answer_id = saved_answer.id
        for gap in evaluation.gaps:
            gap.evaluation_id = evaluation.id

        # Step 10: Save evaluation
        saved_evaluation = await self.evaluation_repo.save(evaluation)

        # Step 11: Link answer to evaluation
        saved_answer.evaluation_id = saved_evaluation.id
        saved_answer = await self.answer_repo.update(saved_answer)

        # Step 12: Update interview
        interview.add_answer(saved_answer.id)
        await self.interview_repo.update(interview)

        # Step 13: Check if more questions
        has_more = interview.has_more_questions()

        logger.info(
            f"Answer processed: score={evaluation.final_score:.1f}, "
            f"similarity={f'{similarity_score:.2f}' if similarity_score is not None else 'N/A'}, "
            f"gaps={len(evaluation.gaps)}, has_more={has_more}"
        )

        return saved_answer, saved_evaluation, has_more

    async def _get_question(self, question_id: UUID) -> Question:
        """Get main question.

        Args:
            question_id: Question UUID

        Returns:
            Question entity

        Raises:
            ValueError: If question not found
        """
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")
        return question

    async def _get_follow_up_question(self, question_id: UUID) -> Question:
        """Get follow-up question and return its parent question.

        Returns parent question for follow-ups (to access ideal_answer).
        Context building happens separately in _build_followup_context().

        Args:
            question_id: Follow-up question UUID

        Returns:
            Parent Question entity

        Raises:
            ValueError: If follow-up or parent question not found
        """
        # Get follow-up question
        follow_up = await self.follow_up_question_repo.get_by_id(question_id)
        if not follow_up:
            raise ValueError(f"Follow-up question {question_id} not found")

        # Get parent question (for ideal_answer)
        parent = await self.question_repo.get_by_id(follow_up.parent_question_id)
        if not parent:
            raise ValueError(f"Parent question {follow_up.parent_question_id} not found")

        return parent

    async def _calculate_similarity(self, answer_text: str, ideal_answer: str) -> float:
        """Calculate cosine similarity between answer and ideal_answer.

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer

        Returns:
            Similarity score (0-1)
        """
        answer_embedding = await self.vector_search.get_embedding(answer_text)
        ideal_embedding = await self.vector_search.get_embedding(ideal_answer)

        similarity = await self.vector_search.find_similar_answers(
            answer_embedding=answer_embedding,
            reference_embeddings=[ideal_embedding],
        )

        return max(0.01, similarity)  # Avoid zero

    async def _detect_gaps_hybrid(
        self, answer_text: str, ideal_answer: str, question_text: str
    ) -> dict[str, Any]:
        """Detect concept gaps using hybrid approach (keywords + LLM).

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer
            question_text: The question asked

        Returns:
            Gaps dict with detected concepts
        """
        # Step 1: Keyword-based gap detection
        keyword_gaps = self._detect_keyword_gaps(answer_text, ideal_answer)

        # Step 2: If keywords detected gaps, confirm with LLM
        if keyword_gaps:
            llm_gaps = await self._detect_gaps_with_llm(
                answer_text=answer_text,
                ideal_answer=ideal_answer,
                question_text=question_text,
                keyword_gaps=keyword_gaps,
            )
            return llm_gaps
        else:
            return {"concepts": [], "confirmed": False, "severity": "minor"}

    def _detect_keyword_gaps(self, answer_text: str, ideal_answer: str) -> list[str]:
        """Fast keyword-based gap detection."""
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "can", "this", "that",
            "these", "those",
        }

        ideal_words = {
            word.lower().strip('.,!?;:"\'-')
            for word in ideal_answer.split()
            if len(word.strip('.,!?;:"\'-')) > 3
            and word.lower().strip('.,!?;:"\'-') not in stop_words
        }

        answer_words = {
            word.lower().strip('.,!?;:"\'-')
            for word in answer_text.split()
            if len(word.strip('.,!?;:"\'-')) > 3
            and word.lower().strip('.,!?;:"\'-') not in stop_words
        }

        missing = list(ideal_words - answer_words)
        return missing if len(missing) > 3 else []

    async def _detect_gaps_with_llm(
        self,
        answer_text: str,
        ideal_answer: str,
        question_text: str,
        keyword_gaps: list[str],
    ) -> dict[str, Any]:
        """Use LLM to confirm and refine gap detection."""
        return await self.llm.detect_concept_gaps(
            answer_text=answer_text,
            ideal_answer=ideal_answer,
            question_text=question_text,
            keyword_gaps=keyword_gaps,
        )

    def _determine_gap_severity(
        self, concept: str, gaps_dict: dict[str, Any]
    ) -> GapSeverity:
        """Determine gap severity from LLM response.

        Args:
            concept: The missing concept
            gaps_dict: Gaps dictionary from LLM

        Returns:
            GapSeverity enum value
        """
        severity_str = gaps_dict.get("severity", "moderate")
        try:
            return GapSeverity(severity_str.lower())
        except ValueError:
            return GapSeverity.MODERATE

    async def _is_followup_question(self, question_id: UUID) -> tuple[bool, UUID | None]:
        """Check if question_id is a follow-up question.

        Args:
            question_id: Question UUID to check

        Returns:
            Tuple of (is_followup, parent_question_id)
        """
        # Try to get from follow_up_question_repository
        follow_up = await self.follow_up_question_repo.get_by_id(question_id)
        if follow_up:
            return True, follow_up.parent_question_id
        return False, None

    async def _build_followup_context(
        self,
        question_id: UUID,
        parent_question_id: UUID,
        parent_ideal_answer: str,
    ) -> FollowUpEvaluationContext:
        """Build follow-up evaluation context.

        Args:
            question_id: Follow-up question UUID
            parent_question_id: Parent question UUID
            parent_ideal_answer: Ideal answer from parent question

        Returns:
            FollowUpEvaluationContext with previous evaluations and gaps
        """
        # Get all answers for parent question (main + follow-ups)
        # We need to find all evaluations related to this parent question
        parent_answer_ids = []

        # Get main question answer
        main_answers = await self.answer_repo.get_by_question_id(parent_question_id)
        parent_answer_ids.extend([a.id for a in main_answers])

        # Get follow-up answers for this parent
        follow_ups = await self.follow_up_question_repo.get_by_parent_question_id(
            parent_question_id
        )
        for fu in follow_ups:
            fu_answers = await self.answer_repo.get_by_question_id(fu.id)
            parent_answer_ids.extend([a.id for a in fu_answers])

        # Get all evaluations for these answers
        previous_evaluations: list[Evaluation] = []
        for answer_id in parent_answer_ids:
            answer = await self.answer_repo.get_by_id(answer_id)
            if answer and answer.evaluation_id:
                evaluation = await self.evaluation_repo.get_by_id(answer.evaluation_id)
                if evaluation:
                    previous_evaluations.append(evaluation)

        # Sort by created_at to maintain order
        previous_evaluations.sort(key=lambda e: e.created_at)

        # Collect all unresolved gaps from previous evaluations
        cumulative_gaps: list[ConceptGap] = []
        for evaluation in previous_evaluations:
            for gap in evaluation.gaps:
                if not gap.resolved:
                    cumulative_gaps.append(gap)

        # Calculate attempt number (1-based index for this follow-up chain)
        attempt_number = len(previous_evaluations) + 1

        # Extract previous scores
        previous_scores = [e.final_score for e in previous_evaluations]

        return FollowUpEvaluationContext(
            parent_question_id=parent_question_id,
            follow_up_question_id=question_id,
            attempt_number=attempt_number,
            previous_evaluations=previous_evaluations,
            cumulative_gaps=cumulative_gaps,
            previous_scores=previous_scores,
            parent_ideal_answer=parent_ideal_answer,
        )
