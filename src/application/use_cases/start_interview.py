"""Start interview use case."""

from uuid import UUID

from ...domain.models.interview import Interview
from ...domain.models.cv_analysis import CVAnalysis
from ...domain.ports.vector_search_port import VectorSearchPort
from ...domain.ports.question_repository_port import QuestionRepositoryPort


class StartInterviewUseCase:
    """Use case for starting an interview.

    This orchestrates the interview initialization:
    1. Retrieve CV analysis
    2. Find suitable questions based on CV
    3. Create interview with selected questions
    4. Mark interview as ready
    """

    def __init__(
        self,
        vector_search: VectorSearchPort,
        question_repository: QuestionRepositoryPort,
    ):
        """Initialize use case with required ports.

        Args:
            vector_search: Vector database service
            question_repository: Question storage service
        """
        self.vector_search = vector_search
        self.question_repository = question_repository

    async def execute(
        self,
        candidate_id: UUID,
        cv_analysis: CVAnalysis,
        num_questions: int = 10,
    ) -> Interview:
        """Execute interview start process.

        Args:
            candidate_id: ID of the candidate
            cv_analysis: CV analysis results
            num_questions: Number of questions for the interview

        Returns:
            Interview ready to start

        Raises:
            ValueError: If CV analysis is invalid or insufficient questions found
        """
        # Step 1: Validate CV analysis
        if not cv_analysis.embedding:
            raise ValueError("CV analysis must have embedding")

        # Step 2: Find suitable questions using semantic search
        similar_questions = await self.vector_search.find_similar_questions(
            query_embedding=cv_analysis.embedding,
            top_k=num_questions * 2,  # Get more candidates for filtering
            filters={
                "difficulty": cv_analysis.suggested_difficulty,
            },
        )

        if len(similar_questions) < num_questions:
            raise ValueError(
                f"Insufficient questions found. Required: {num_questions}, "
                f"Found: {len(similar_questions)}"
            )

        # Step 3: Select top questions and retrieve full details
        selected_question_ids = [
            UUID(q["question_id"]) for q in similar_questions[:num_questions]
        ]

        questions = await self.question_repository.get_by_ids(selected_question_ids)

        # Step 4: Create interview
        interview = Interview(
            candidate_id=candidate_id,
            cv_analysis_id=cv_analysis.id,
        )

        # Add questions to interview
        for question in questions:
            interview.add_question(question.id)

        # Step 5: Mark interview as ready
        interview.mark_ready(cv_analysis.id)

        return interview
