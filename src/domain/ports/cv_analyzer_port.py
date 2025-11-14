"""CV Analyzer port interface."""

from abc import ABC, abstractmethod

from ..models.cv_analysis import CVAnalysis
from ..models.candidate import Candidate
from uuid import UUID

class CVAnalyzerPort(ABC):
    """Interface for CV analysis operations.

    This port abstracts CV parsing and analysis, allowing different
    implementations (spaCy, LangChain, etc.).
    """

    @abstractmethod
    async def analyze_cv(
        self,
        cv_file_path: str,
        candidate_id: str,
    ) -> CVAnalysis:
        """Analyze a CV file and extract structured information.

        Args:
            cv_file_path: Path to CV file (PDF, DOC, DOCX)
            candidate_id: ID of the candidate

        Returns:
            CVAnalysis with extracted skills, experience, and metadata
        """
        pass

    @abstractmethod
    async def generate_candidate_from_summary(
        self,
        summary_info: str,
        cv_file_path: str,
        candidate_id: UUID
    ) -> Candidate:
        """Generate a Candidate object from CV summary information using GPT-4o-mini.

        Args:
            summary_info: JSON string containing CV summary information
            cv_file_path: Path to the candidate's CV file
            candidate_id: ID of the candidate
        Returns:
            Candidate: Populated Candidate object
        """
        pass

    # @abstractmethod
    # async def generate_cv_summary(
    #     self,
    #     extracted_data: dict,
    #     cv_text: str,
    # ) -> str:
    #     """Generate a concise summary of the CV for HR evaluation.

    #     Args:
    #         extracted_data: Extracted skills and experiences
    #         cv_text: Full text of the CV
    #     Returns:
    #         Summary text
    #     """
    #     pass
    
    # @abstractmethod
    # async def extract_skills_and_experience(
    #     self,
    #     cv_text: str,
    # ) -> CVAnalysis:
    #     """Extract skills and experience from CV text.

    #     Args:
    #         cv_text: Full text of the CV
    #     Returns:
    #         CVAnalysis with extracted skills, experiences, and language
    #     """        
    #     pass

    # @abstractmethod
    # async def evaluate_cv_level_from_summary(
    #     self,
    #     cv_id: str,
    #     summary: str,
    # ) -> dict:
    #     """Evaluate CV level (e.g., Junior, Mid, Senior) based on summary.

    #     Args:
    #         cv_id: Unique CV identifier
    #         summary: CV summary text
    #     Returns:
    #         Dictionary with level, score, strengths, weaknesses, etc.
    #     """
    #     pass