"""Process answer with adaptive follow-up logic."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.models.answer import Answer
from ...domain.models.follow_up_question import FollowUpQuestion
from ...domain.models.interview import InterviewStatus
from ...domain.ports.answer_repository_port import AnswerRepositoryPort
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

    This use case implements the adaptive interview flow:
    1. Evaluate answer using LLM
    2. Calculate similarity vs ideal_answer
    3. Detect concept gaps (hybrid: keywords + LLM)
    4. Decide if follow-up needed (similarity <80% OR gaps exist)
    5. Generate follow-up question if needed (max 3 per main question)
    """

    def __init__(
        self,
        answer_repository: AnswerRepositoryPort,
        interview_repository: InterviewRepositoryPort,
        question_repository: QuestionRepositoryPort,
        follow_up_question_repository: FollowUpQuestionRepositoryPort,
        llm: LLMPort,
        vector_search: VectorSearchPort,
    ):
        """Initialize use case with required ports.

        Args:
            answer_repository: Answer storage
            interview_repository: Interview storage
            question_repository: Question storage
            follow_up_question_repository: Follow-up question storage
            llm: LLM service for evaluation and gap detection
            vector_search: Vector database for similarity calculation
        """
        self.answer_repo = answer_repository
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
    ) -> tuple[Answer, FollowUpQuestion | None, bool]:
        """Process answer with adaptive evaluation.

        Args:
            interview_id: The interview UUID
            question_id: The question UUID
            answer_text: The answer text
            audio_file_path: Optional audio file path for voice answers

        Returns:
            Tuple of (Answer with evaluation, optional FollowUpQuestion, has_more_questions)

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

        if interview.status != InterviewStatus.IN_PROGRESS:
            raise ValueError(f"Interview not in progress: {interview.status}")

        # Step 2: Get question with ideal_answer
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Step 3: Create answer
        answer = Answer(
            interview_id=interview_id,
            question_id=question_id,
            candidate_id=interview.candidate_id,
            text=answer_text,
            is_voice=bool(audio_file_path),
            audio_file_path=audio_file_path,
            similarity_score=None,  # Will be calculated if ideal_answer exists
            gaps=None,  # Will be populated by gap detection
            created_at=datetime.utcnow(),
        )

        # Step 4: Evaluate answer using LLM
        evaluation = await self.llm.evaluate_answer(
            question=question,
            answer_text=answer_text,
            context={
                "interview_id": str(interview_id),
                "candidate_id": str(interview.candidate_id),
            },
        )
        answer.evaluate(evaluation)

        # Step 5: Calculate similarity score (if ideal_answer exists)
        if question.has_ideal_answer():
            similarity_score = await self._calculate_similarity(
                answer_text, question.ideal_answer  # type: ignore
            )

            if(similarity_score==0.0):
                similarity_score = 0.01  # avoid zero similarity
            answer.similarity_score = similarity_score
            logger.info(f"Similarity score: {similarity_score:.2f}")
        else:
            logger.warning(f"Question {question_id} has no ideal_answer, skipping similarity")

        # Step 6: Detect gaps using hybrid approach
        gaps = await self._detect_gaps_hybrid(
            answer_text=answer_text,
            ideal_answer=question.ideal_answer or "",
            question_text=question.text,
        )
        answer.gaps = gaps
        logger.info(f"Detected {len(gaps.get('concepts', []))} concept gaps")

        # Step 7: Save answer
        saved_answer = await self.answer_repo.save(answer)

        # Step 8: Update interview
        interview.add_answer(saved_answer.id)
        await self.interview_repo.update(interview)

        # Step 9: Decide if follow-up needed
        follow_up_question = None
        if question.has_ideal_answer():
            # Count existing follow-ups for this question
            follow_up_count = self._count_follow_ups_for_question(interview, question_id)

            if self._should_generate_followup(saved_answer, follow_up_count):
                follow_up_question = await self._generate_followup(
                    interview_id=interview_id,
                    parent_question=question,
                    answer=saved_answer,
                    gaps=gaps,
                    order=follow_up_count + 1,
                )
                # Save follow-up question to its own table
                await self.follow_up_question_repo.save(follow_up_question)
                # Track in interview
                interview.add_adaptive_followup(follow_up_question.id)
                await self.interview_repo.update(interview)
                logger.info(f"Generated follow-up question #{follow_up_count + 1}")

        # Step 10: Check if more questions
        has_more = interview.has_more_questions()

        return saved_answer, follow_up_question, has_more

    async def _calculate_similarity(self, answer_text: str, ideal_answer: str) -> float:
        """Calculate cosine similarity between answer and ideal_answer.

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer

        Returns:
            Similarity score (0-1)
        """
        # Get embeddings
        answer_embedding = await self.vector_search.get_embedding(answer_text)
        ideal_embedding = await self.vector_search.get_embedding(ideal_answer)

        # Calculate cosine similarity
        similarity = await self.vector_search.find_similar_answers(
            answer_embedding=answer_embedding,
            reference_embeddings=[ideal_embedding],
        )

        return similarity

    async def _detect_gaps_hybrid(
        self, answer_text: str, ideal_answer: str, question_text: str
    ) -> dict[str, Any]:
        """Detect concept gaps using hybrid approach (keywords + LLM).

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer
            question_text: The question asked

        Returns:
            Gaps dict with detected concepts and keywords
        """
        # Step 1: Keyword-based gap detection (fast)
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
            # No gaps detected by keywords
            return {"concepts": [], "keywords": [], "confirmed": False}

    def _detect_keyword_gaps(self, answer_text: str, ideal_answer: str) -> list[str]:
        """Fast keyword-based gap detection.

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer

        Returns:
            List of missing keywords
        """
        # Simple keyword extraction (lowercase, remove common words)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        # Extract words from ideal answer (strip punctuation)
        ideal_words = {
            word.lower().strip('.,!?;:"\'-')
            for word in ideal_answer.split()
            if len(word.strip('.,!?;:"\'-')) > 3 and word.lower().strip('.,!?;:"\'-') not in stop_words
        }

        # Extract words from candidate answer (strip punctuation)
        answer_words = {
            word.lower().strip('.,!?;:"\'-')
            for word in answer_text.split()
            if len(word.strip('.,!?;:"\'-')) > 3 and word.lower().strip('.,!?;:"\'-') not in stop_words
        }

        # Find missing keywords (in ideal but not in answer)
        missing = list(ideal_words - answer_words)

        # Only consider significant if >3 keywords missing
        return missing if len(missing) > 3 else []

    async def _detect_gaps_with_llm(
        self,
        answer_text: str,
        ideal_answer: str,
        question_text: str,
        keyword_gaps: list[str],
    ) -> dict[str, Any]:
        """Use LLM to confirm and refine gap detection.

        Args:
            answer_text: Candidate's answer
            ideal_answer: Reference ideal answer
            question_text: The question asked
            keyword_gaps: Keywords detected as missing

        Returns:
            Refined gaps dict with concepts and confirmation
        """
        # Use port method instead of direct client access
        return await self.llm.detect_concept_gaps(
            answer_text=answer_text,
            ideal_answer=ideal_answer,
            question_text=question_text,
            keyword_gaps=keyword_gaps,
        )

    def _should_generate_followup(self, answer: Answer, follow_up_count: int) -> bool:
        """Decide if follow-up question should be generated.

        Args:
            answer: The evaluated answer
            follow_up_count: Number of existing follow-ups

        Returns:
            True if follow-up needed
        """
        # Stop if already 3 follow-ups
        if follow_up_count >= 3:
            logger.info("Max follow-ups (3) reached")
            return False

        # Check if answer is adaptive complete
        if answer.is_adaptive_complete():
            logger.info("Answer meets adaptive completion criteria")
            return False

        # Check similarity threshold
        if answer.similarity_score and answer.similarity_score >= 0.8:
            logger.info(f"Similarity {answer.similarity_score:.2f} >= 0.8, no follow-up")
            return False

        # Check if confirmed gaps exist
        if answer.gaps and answer.gaps.get("confirmed"):
            logger.info("Confirmed gaps detected, generating follow-up")
            return True

        # Default: no follow-up
        return False

    async def _generate_followup(
        self,
        interview_id: UUID,
        parent_question: Any,
        answer: Answer,
        gaps: dict[str, Any],
        order: int,
    ) -> FollowUpQuestion:
        """Generate targeted follow-up question based on gaps.

        Args:
            interview_id: Interview ID
            parent_question: Original question
            answer: Candidate's answer
            gaps: Detected gaps
            order: Follow-up order (1, 2, or 3)

        Returns:
            Generated FollowUpQuestion
        """
        missing_concepts = gaps.get("concepts", [])
        severity = gaps.get("severity", "moderate")

        # Use port method instead of direct client access
        follow_up_text = await self.llm.generate_followup_question(
            parent_question=parent_question.text,
            answer_text=answer.text,
            missing_concepts=missing_concepts,
            severity=severity,
            order=order,
        )

        # Create FollowUpQuestion entity
        follow_up = FollowUpQuestion(
            parent_question_id=parent_question.id,
            interview_id=interview_id,
            text=follow_up_text,
            generated_reason=f"Missing concepts: {', '.join(missing_concepts[:3])}",
            order_in_sequence=order,
        )

        return follow_up

    def _count_follow_ups_for_question(self, interview: Any, question_id: UUID) -> int:
        """Count how many follow-ups already exist for a question.

        Args:
            interview: Interview entity
            question_id: Parent question ID

        Returns:
            Count of follow-ups for this question
        """
        # For MVP, count from adaptive_follow_ups list
        # TODO: In production, query FollowUpQuestion table by parent_question_id
        return len(interview.adaptive_follow_ups)
