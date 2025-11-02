"""Question domain model."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Question type enumeration."""
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"


class DifficultyLevel(str, Enum):
    """Question difficulty level."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(BaseModel):
    """Represents an interview question.

    Questions are value objects in the interview domain.
    They contain metadata for semantic search and categorization.
    """

    id: UUID = Field(default_factory=uuid4)
    text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    skills: list[str] = Field(default_factory=list)  # e.g., ["Python", "OOP"]
    tags: list[str] = Field(default_factory=list)  # e.g., ["algorithms", "data-structures"]
    reference_answer: str | None = None
    evaluation_criteria: str | None = None
    version: int = 1
    embedding: list[float] | None = None  # Vector embedding for semantic search
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True

    def has_skill(self, skill: str) -> bool:
        """Check if question tests a specific skill.

        Args:
            skill: Skill name to check

        Returns:
            True if skill is tested, False otherwise
        """
        return skill.lower() in [s.lower() for s in self.skills]

    def has_tag(self, tag: str) -> bool:
        """Check if question has a specific tag.

        Args:
            tag: Tag to check

        Returns:
            True if tag exists, False otherwise
        """
        return tag.lower() in [t.lower() for t in self.tags]

    def is_suitable_for_difficulty(self, max_difficulty: DifficultyLevel) -> bool:
        """Check if question difficulty is appropriate.

        Args:
            max_difficulty: Maximum allowed difficulty

        Returns:
            True if suitable, False otherwise
        """
        difficulty_order = {
            DifficultyLevel.EASY: 1,
            DifficultyLevel.MEDIUM: 2,
            DifficultyLevel.HARD: 3,
        }
        return difficulty_order[self.difficulty] <= difficulty_order[max_difficulty]
