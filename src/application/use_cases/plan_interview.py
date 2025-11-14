"""Plan interview use case."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.models.cv_analysis import CVAnalysis
from ...domain.models.interview import Interview, InterviewStatus
from ...domain.models.question import DifficultyLevel, Question, QuestionType
from ...domain.ports.cv_analysis_repository_port import CVAnalysisRepositoryPort
from ...domain.ports.interview_repository_port import InterviewRepositoryPort
from ...domain.ports.llm_port import LLMPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort
from ...domain.ports.vector_search_port import VectorSearchPort

logger = logging.getLogger(__name__)


class PlanInterviewUseCase:
    """Use case for planning interview questions with ideal answers.

    This orchestrates the pre-planning phase:
    1. Load CV analysis
    2. Calculate n based on skill diversity (max 5)
    3. Generate n questions with ideal answers + rationale (using vector exemplars)
    4. Store questions with embeddings and mark interview as READY
    """

    def __init__(
        self,
        llm: LLMPort,
        cv_analysis_repo: CVAnalysisRepositoryPort,
        interview_repo: InterviewRepositoryPort,
        question_repo: QuestionRepositoryPort,
    ):
        """Initialize use case with required ports.

        Args:
            llm: LLM service for question generation
            vector_search: Vector search service for exemplar retrieval and embedding storage
            cv_analysis_repo: CV analysis storage
            interview_repo: Interview storage
            question_repo: Question storage
        """
        self.llm = llm
        self.cv_analysis_repo = cv_analysis_repo
        self.interview_repo = interview_repo
        self.question_repo = question_repo

    async def execute(
        self,
        cv_analysis_id: UUID,
        candidate_id: UUID,
    ) -> Interview:
        """Plan interview by generating n questions with ideal answers.

        Args:
            cv_analysis_id: CV analysis to base questions on
            candidate_id: Candidate being interviewed

        Returns:
            Interview entity with status=READY

        Raises:
            ValueError: If CV analysis not found
            Exception: If question generation fails
        """
        logger.info(
            "Starting interview planning",
            extra={
                "cv_analysis_id": str(cv_analysis_id),
                "candidate_id": str(candidate_id),
            },
        )

        # Step 1: Load CV analysis
        cv_analysis = await self.cv_analysis_repo.get_by_id(cv_analysis_id)
        if not cv_analysis:
            raise ValueError(f"CV analysis {cv_analysis_id} not found")

        # Step 2: Calculate n based on skill diversity
        n = self._calculate_question_count(cv_analysis)
        logger.info(f"Calculated n={n} questions based on CV complexity")

        # Step 3: Create interview (status=PREPARING)
        interview = Interview(
            candidate_id=candidate_id,
            status=InterviewStatus.PREPARING,
            cv_analysis_id=cv_analysis_id,
        )
        await self.interview_repo.save(interview)

        # Step 4: Generate n questions with embeddings (sequential for MVP)
        question_ids = []
        try:
            for i in range(n):
                question = await self._generate_question_with_ideal_answer(cv_analysis, i, n)
                await self.question_repo.save(question)
                question_ids.append(question.id)
                logger.info(f"Generated question {i + 1}/{n}: {question.id}")

                # Store question embedding in vector DB (non-blocking)
                # await self._store_question_embedding(question)

        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            # Rollback: Delete partially created questions
            for qid in question_ids:
                try:
                    await self.question_repo.delete(qid)
                except Exception:
                    pass  # Best effort cleanup
            raise

        # Step 5: Update interview (status=READY)
        interview.question_ids = question_ids
        interview.plan_metadata = {
            "n": n,
            "generated_at": datetime.utcnow().isoformat(),
            "strategy": "adaptive_planning_v1",
            "cv_summary": cv_analysis.summary or "No summary",
        }
        interview.mark_ready(cv_analysis_id)
        await self.interview_repo.update(interview)

        logger.info(
            "Interview planning complete",
            extra={
                "interview_id": str(interview.id),
                "question_count": n,
            },
        )

        return interview

    def _calculate_question_count(self, cv_analysis: CVAnalysis) -> int:
        """Calculate question count based on skill diversity only.

        Args:
            cv_analysis: Analyzed CV data

        Returns:
            Question count (2-5)
        """
        skill_count = len(cv_analysis.skills)

        # Skill-only calculation (ignore experience years)
        if skill_count <= 2:
            n = 2
        elif skill_count <= 4:
            n = 3
        elif skill_count <= 7:
            n = 4
        else:
            n = 5  # Max 5 questions

        return n

    def _build_search_query(
        self,
        skill: str,
        cv_analysis: CVAnalysis,
        difficulty: DifficultyLevel,
    ) -> str:
        """Build search query for exemplar retrieval.

        Args:
            skill: Target skill being tested
            cv_analysis: CV analysis with experience data
            difficulty: Question difficulty level

        Returns:
            Search query string for vector DB
        """
        experience = cv_analysis.work_experience_years or 0
        exp_level = "junior" if experience < 3 else "mid" if experience < 7 else "senior"

        return f"{skill} {difficulty.value.lower()} interview question for {exp_level} developer"

    async def _find_exemplar_questions(
        self,
        skill: str,
        question_type: QuestionType,
        difficulty: DifficultyLevel,
        cv_analysis: CVAnalysis,
    ) -> list[dict[str, Any]]:
        """Find similar questions as exemplars from vector DB.

        Args:
            skill: Target skill
            question_type: Question type (TECHNICAL/BEHAVIORAL/SITUATIONAL)
            difficulty: Question difficulty
            cv_analysis: CV analysis for context

        Returns:
            List of exemplar questions (max 3), empty list on failure
        """
        try:
            # Query by skill and difficulty
            questions = await self.question_repo.find_by_skill(skill, difficulty)
            
            # Filter by question type
            questions_by_type = [q for q in questions if q.question_type == question_type][:5]

            # Build search query
            # query_text = self._build_search_query(skill, cv_analysis, difficulty)

            # Get query embedding
            # query_embedding = await self.vector_search.get_embedding(query_text)

            # Search with filters
            # similar_questions = await self.vector_search.find_similar_questions(
            #     query_embedding=query_embedding,
            #     top_k=5,  # Request 5, use top 3
            #     filters={
            #         "question_type": question_type.value,
            #         "difficulty": difficulty.value,
            #     }
            # )

            # Format exemplars
            exemplars = [
                {
                    "text": question.text,
                    "skills": question.skills,
                    "difficulty": question.difficulty.value if question.difficulty else "",
                }
                for question in questions_by_type
            ]

            print(exemplars)

            logger.info(f"Found {len(exemplars)} exemplar questions for {skill}")
            return exemplars

        except Exception as e:
            logger.warning(f"Vector search failed: {e}. Falling back to no exemplars.")
            return []  # Fallback: empty exemplars

    async def _store_question_embedding(
        self,
        question: Question,
    ) -> None:
        """Store question embedding in vector DB.

        Args:
            question: Question entity to store embedding for

        Note:
            Non-critical operation - continues even if storage fails
        """
        try:
            # Generate embedding
            # embedding = await self.vector_search.get_embedding(question.text)

            # Store with metadata
            # await self.vector_search.store_question_embedding(
            #     question_id=question.id,
            #     embedding=embedding,
            #     metadata={
            #         "text": question.text,
            #         "skills": question.skills,
            #         "difficulty": question.difficulty.value,
            #         "question_type": question.question_type.value,
            #         "tags": question.tags or [],
            #     }
            # )

            logger.info(f"Stored embedding for question {question.id}")

        except Exception as e:
            logger.error(f"Failed to store embedding for {question.id}: {e}")
            # Non-critical: Continue even if embedding storage fails

    async def _generate_question_with_ideal_answer(
        self,
        cv_analysis: CVAnalysis,
        index: int,
        total: int,
    ) -> Question:
        """Generate single question with ideal answer + rationale using vector exemplars.

        Args:
            cv_analysis: CV data for context
            index: Current question index (0-based)
            total: Total questions to generate

        Returns:
            Question entity with ideal_answer + rationale populated
        """
        # Determine question type/difficulty based on index
        question_type, difficulty = self._get_question_distribution(index, total)

        # Select skill to test
        skills = cv_analysis.get_top_skills(limit=5)
        skill = skills[index % len(skills)].skill if skills else "general knowledge"

        # Find exemplar questions from vector DB
        exemplars = await self._find_exemplar_questions(
            skill=skill,
            question_type=question_type,
            difficulty=difficulty,
            cv_analysis=cv_analysis,
        )

        # Generate question with exemplars
        context = {
            "summary": cv_analysis.summary or "No summary",
            "skills": [s.skill for s in skills],
            "experience": cv_analysis.work_experience_years or 0,
        }

        # Generate question using exemplars (if found)
        question_text = await self.llm.generate_question(
            context=context,
            skill=skill,
            difficulty=difficulty.value,
            exemplars=exemplars if exemplars else None,
        )

        # Generate ideal answer
        ideal_answer = await self.llm.generate_ideal_answer(
            question_text=question_text,
            context=context,
        )

        # Generate rationale
        rationale = await self.llm.generate_rationale(
            question_text=question_text,
            ideal_answer=ideal_answer,
        )

        # Create Question entity
        question = Question(
            text=question_text,
            question_type=question_type,
            difficulty=difficulty,
            skills=[skill],
            ideal_answer=ideal_answer,
            rationale=rationale,
        )

        return question

    def _get_question_distribution(
        self, index: int, total: int
    ) -> tuple[QuestionType, DifficultyLevel]:
        """Determine question type and difficulty based on index.

        Distribution:
        - 60% technical, 30% behavioral, 10% situational
        - 50% easy, 30% medium, 20% hard

        Args:
            index: Current question index
            total: Total questions

        Returns:
            (QuestionType, DifficultyLevel)
        """
        # Question type distribution
        technical_count = int(total * 0.6)
        behavioral_count = int(total * 0.3)

        if index < technical_count:
            q_type = QuestionType.TECHNICAL
        elif index < technical_count + behavioral_count:
            q_type = QuestionType.BEHAVIORAL
        else:
            q_type = QuestionType.SITUATIONAL

        # Difficulty distribution
        easy_count = int(total * 0.5)
        medium_count = int(total * 0.3)

        if index < easy_count:
            difficulty = DifficultyLevel.EASY
        elif index < easy_count + medium_count:
            difficulty = DifficultyLevel.MEDIUM
        else:
            difficulty = DifficultyLevel.HARD

        return q_type, difficulty
