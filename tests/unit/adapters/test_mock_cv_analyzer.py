"""Unit tests for MockCVAnalyzerAdapter."""

import pytest
from uuid import UUID, uuid4

from src.adapters.mock.mock_cv_analyzer import MockCVAnalyzerAdapter
from src.domain.models.cv_analysis import CVAnalysis


@pytest.fixture
def cv_analyzer():
    """Create CV analyzer instance."""
    return MockCVAnalyzerAdapter()


class TestExtractTextFromFile:
    """Test extract_text_from_file method."""

    @pytest.mark.asyncio
    async def test_extract_text_pdf(self, cv_analyzer):
        """Test extracting text from PDF file."""
        text = await cv_analyzer.extract_text_from_file("test_cv.pdf")

        assert isinstance(text, str)
        assert len(text) > 200
        assert "John Doe" in text
        assert "Software Engineer" in text

    @pytest.mark.asyncio
    async def test_extract_text_doc(self, cv_analyzer):
        """Test extracting text from DOC file."""
        text = await cv_analyzer.extract_text_from_file("test_cv.doc")

        assert isinstance(text, str)
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_extract_text_docx(self, cv_analyzer):
        """Test extracting text from DOCX file."""
        text = await cv_analyzer.extract_text_from_file("test_cv.docx")

        assert isinstance(text, str)
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_unsupported_format(self, cv_analyzer):
        """Test error for unsupported file format."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            await cv_analyzer.extract_text_from_file("test_cv.txt")

    @pytest.mark.asyncio
    async def test_unsupported_format_xlsx(self, cv_analyzer):
        """Test error for XLSX file."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            await cv_analyzer.extract_text_from_file("test_cv.xlsx")


class TestAnalyzeCV:
    """Test analyze_cv method."""

    @pytest.mark.asyncio
    async def test_analyze_junior_cv(self, cv_analyzer):
        """Test analyzing junior-level CV."""
        candidate_id = str(uuid4())
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path="junior_developer.pdf",
            candidate_id=candidate_id
        )

        assert isinstance(cv_analysis, CVAnalysis)
        assert str(cv_analysis.candidate_id) == candidate_id
        assert len(cv_analysis.skills) >= 2
        assert len(cv_analysis.skills) <= 3
        assert cv_analysis.work_experience_years is not None
        assert 1.0 <= cv_analysis.work_experience_years <= 2.0
        assert cv_analysis.suggested_difficulty == "easy"
        assert cv_analysis.education_level == "Bachelor's"

    @pytest.mark.asyncio
    async def test_analyze_senior_cv(self, cv_analyzer):
        """Test analyzing senior-level CV."""
        candidate_id = str(uuid4())
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path="senior_engineer.pdf",
            candidate_id=candidate_id
        )

        assert isinstance(cv_analysis, CVAnalysis)
        assert len(cv_analysis.skills) >= 5
        assert len(cv_analysis.skills) <= 6
        assert cv_analysis.work_experience_years is not None
        assert 6.0 <= cv_analysis.work_experience_years <= 10.0
        assert cv_analysis.suggested_difficulty == "hard"
        assert cv_analysis.education_level == "Master's"

    @pytest.mark.asyncio
    async def test_analyze_mid_level_cv(self, cv_analyzer):
        """Test analyzing mid-level CV (default)."""
        candidate_id = str(uuid4())
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path="developer.pdf",
            candidate_id=candidate_id
        )

        assert isinstance(cv_analysis, CVAnalysis)
        assert len(cv_analysis.skills) >= 4
        assert len(cv_analysis.skills) <= 5
        assert cv_analysis.work_experience_years is not None
        assert 3.0 <= cv_analysis.work_experience_years <= 5.0
        assert cv_analysis.suggested_difficulty == "medium"
        assert cv_analysis.education_level == "Bachelor's"

    @pytest.mark.asyncio
    async def test_cv_analysis_structure(self, cv_analyzer):
        """Test CV analysis has all required fields."""
        candidate_id = str(uuid4())
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path="test.pdf",
            candidate_id=candidate_id
        )

        assert cv_analysis.id is not None
        assert cv_analysis.cv_file_path == "test.pdf"
        assert cv_analysis.extracted_text is not None
        assert len(cv_analysis.extracted_text) > 0
        assert isinstance(cv_analysis.skills, list)
        assert len(cv_analysis.skills) > 0
        assert isinstance(cv_analysis.suggested_topics, list)
        assert len(cv_analysis.suggested_topics) > 0
        assert cv_analysis.summary is not None
        assert "Mock CV analysis" in cv_analysis.summary

    @pytest.mark.asyncio
    async def test_skills_are_technical(self, cv_analyzer):
        """Test that extracted skills include technical skills."""
        candidate_id = str(uuid4())
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path="senior_engineer.pdf",
            candidate_id=candidate_id
        )

        technical_skills = cv_analysis.get_technical_skills()
        assert len(technical_skills) > 0

        # Check skill structure
        for skill in cv_analysis.skills:
            assert skill.name is not None
            assert skill.category in ["technical", "soft"]

    @pytest.mark.asyncio
    async def test_suggested_topics_from_skills(self, cv_analyzer):
        """Test that suggested topics are derived from skills."""
        candidate_id = str(uuid4())
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path="python_developer.pdf",
            candidate_id=candidate_id
        )

        # Topics should be related to skills
        assert len(cv_analysis.suggested_topics) > 0
        assert len(cv_analysis.suggested_topics) <= 5

    @pytest.mark.asyncio
    async def test_metadata_included(self, cv_analyzer):
        """Test that metadata is included in analysis."""
        candidate_id = str(uuid4())
        cv_analysis = await cv_analyzer.analyze_cv(
            cv_file_path="junior_dev.pdf",
            candidate_id=candidate_id
        )

        assert "experience_level" in cv_analysis.metadata
        assert "file_name" in cv_analysis.metadata
        assert "mock_adapter" in cv_analysis.metadata
        assert cv_analysis.metadata["mock_adapter"] is True
        assert cv_analysis.metadata["experience_level"] == "junior"

    @pytest.mark.asyncio
    async def test_consistent_results(self, cv_analyzer):
        """Test that same filename produces consistent experience level."""
        candidate_id = str(uuid4())

        # Call twice with same filename
        result1 = await cv_analyzer.analyze_cv("junior_dev.pdf", candidate_id)
        result2 = await cv_analyzer.analyze_cv("junior_dev.pdf", candidate_id)

        assert result1.suggested_difficulty == result2.suggested_difficulty
        assert len(result1.skills) == len(result2.skills)
        assert result1.education_level == result2.education_level
