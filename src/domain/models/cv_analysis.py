"""CV Analysis domain model."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExtractedSkill(BaseModel):
    """Represents a skill extracted from CV.

    This is a value object within CV analysis.
    """

    skill: str = Field(alias="skill")
    proficiency: str | None = Field(default=None, alias="proficiency")  # e.g., "beginner", "intermediate", "expert"
    years: float | None = Field(default=None, alias="years")

    def is_technical(self) -> bool:
        """Check if skill is technical.

        Returns:
            True if technical skill, False otherwise
        """
        return self.category.lower() == "technical"


class CVAnalysis(BaseModel):
    """Represents the analysis results of a candidate's CV.

    This is an entity in the interview domain.
    """

    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    cv_file_path: str
    extracted_text: str
    skills: list[ExtractedSkill] = Field(default_factory=list)
    work_experience_years: float | None = None
    education_level: str | None = None  # e.g., "Bachelor's", "Master's"
    suggested_topics: list[str] = Field(default_factory=list)  # Topics to cover
    suggested_difficulty: str = "medium"  # Overall difficulty level
    embedding: Optional[List[float]] = None  # Vector embedding of CV
    summary: Optional[str] = None  # AI-generated summary
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


    class Config:
        """Pydantic configuration."""
        frozen = False

    def get_technical_skills(self) -> list[ExtractedSkill]:
        """Get only technical skills.

        Returns:
            List of technical skills
        """
        return [skill for skill in self.skills if skill.is_technical()]

    def has_skill(self, skill_name: str) -> bool:
        """Check if a specific skill was found in CV.

        Args:
            skill_name: Name of skill to check

        Returns:
            True if skill exists, False otherwise
        """
        return any(
            skill.name.lower() == skill_name.lower()
            for skill in self.skills
        )

    def get_skill_by_name(self, skill_name: str) -> ExtractedSkill | None:
        """Get a skill by name.

        Args:
            skill_name: Name of skill to find

        Returns:
            ExtractedSkill if found, None otherwise
        """
        for skill in self.skills:
            if skill.skill.lower() == skill_name.lower():
                return skill
        return None

    def get_top_skills(self, limit: int = 5) -> list[ExtractedSkill]:
        """Get top skills by mention count.

        Args:
            limit: Maximum number of skills to return

        Returns:
            List of top skills
        """
        sorted_skills = sorted(
            self.skills,
            key=lambda s: s.skill,
            reverse=True
        )
        return sorted_skills[:limit]

    def is_experienced(self, min_years: float = 3.0) -> bool:
        """Check if candidate is experienced.

        Args:
            min_years: Minimum years of experience

        Returns:
            True if experienced, False otherwise
        """
        return (
            self.work_experience_years is not None
            and self.work_experience_years >= min_years
        )
