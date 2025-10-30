"""Analyze CV use case."""

from uuid import UUID

from ...domain.ports.cv_analyzer_port import CVAnalyzerPort
from ...domain.ports.vector_search_port import VectorSearchPort
from ...domain.models.cv_analysis import CVAnalysis


class AnalyzeCVUseCase:
    """Use case for analyzing a candidate's CV.

    This orchestrates the CV analysis process:
    1. Extract text from CV file
    2. Analyze and extract structured information
    3. Generate embeddings for semantic search
    4. Store embeddings in vector database
    """

    def __init__(
        self,
        cv_analyzer: CVAnalyzerPort,
        vector_search: VectorSearchPort,
    ):
        """Initialize use case with required ports.

        Args:
            cv_analyzer: CV analysis service
            vector_search: Vector database service
        """
        self.cv_analyzer = cv_analyzer
        self.vector_search = vector_search

    async def execute(
        self,
        cv_file_path: str,
        candidate_id: UUID,
    ) -> CVAnalysis:
        """Execute CV analysis.

        Args:
            cv_file_path: Path to CV file
            candidate_id: ID of the candidate

        Returns:
            CVAnalysis with extracted information

        Raises:
            ValueError: If CV file is invalid or cannot be processed
        """
        # Step 1: Analyze CV using the CV analyzer port
        cv_analysis = await self.cv_analyzer.analyze_cv(
            cv_file_path=cv_file_path,
            candidate_id=str(candidate_id),
        )

        # Step 2: Generate embedding for the CV
        # Combine key information for embedding
        cv_text_for_embedding = f"""
        Skills: {', '.join([skill.name for skill in cv_analysis.skills])}
        Experience: {cv_analysis.work_experience_years} years
        Education: {cv_analysis.education_level}
        Summary: {cv_analysis.summary}
        """

        embedding = await self.vector_search.get_embedding(cv_text_for_embedding)
        cv_analysis.embedding = embedding

        # Step 3: Store embedding in vector database for future question matching
        await self.vector_search.store_cv_embedding(
            cv_analysis_id=cv_analysis.id,
            embedding=embedding,
            metadata={
                "candidate_id": str(candidate_id),
                "skills": [skill.name for skill in cv_analysis.skills],
                "experience_years": cv_analysis.work_experience_years,
                "education": cv_analysis.education_level,
                "suggested_difficulty": cv_analysis.suggested_difficulty,
            },
        )

        return cv_analysis
