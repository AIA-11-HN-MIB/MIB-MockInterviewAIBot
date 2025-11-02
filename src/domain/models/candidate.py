"""Candidate domain model."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Candidate(BaseModel):
    """Represents a candidate participating in an interview.

    This is a rich domain model that encapsulates candidate-related business logic.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    cv_file_path: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        frozen = False  # Allow updates

    def update_cv(self, cv_file_path: str) -> None:
        """Update candidate's CV file path.

        Args:
            cv_file_path: Path to the CV file
        """
        self.cv_file_path = cv_file_path
        self.updated_at = datetime.utcnow()

    def has_cv(self) -> bool:
        """Check if candidate has uploaded a CV.

        Returns:
            True if CV exists, False otherwise
        """
        return self.cv_file_path is not None
