"""CV Analyzer port interface."""

from abc import ABC, abstractmethod

from ..models.cv_analysis import CVAnalysis


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
    async def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from a document file.

        Args:
            file_path: Path to document file

        Returns:
            Extracted text content
        """
        pass
