"""Mock vector search adapter for development and testing."""

import random
from typing import Any
from uuid import UUID

from ...domain.models.question import DifficultyLevel
from ...domain.ports.vector_search_port import VectorSearchPort


class MockVectorSearchAdapter(VectorSearchPort):
    """Mock vector search adapter that returns fake data.

    This adapter simulates vector database behavior without requiring
    external services like Pinecone, Weaviate, or ChromaDB.
    """

    def __init__(self):
        """Initialize mock adapter with seeded question IDs from database."""
        # Use actual question IDs from seed_data.sql
        # These IDs will exist in the database after running seed script
        self._mock_question_ids = [
            UUID("650e8400-e29b-41d4-a716-446655440001"),  # JS var/let/const - EASY
            UUID("650e8400-e29b-41d4-a716-446655440002"),  # REST API - EASY
            UUID("650e8400-e29b-41d4-a716-446655440003"),  # async/await - MEDIUM
            UUID("650e8400-e29b-41d4-a716-446655440004"),  # SOLID principles - MEDIUM
            UUID("650e8400-e29b-41d4-a716-446655440005"),  # Database normalization - HARD
            UUID("650e8400-e29b-41d4-a716-446655440006"),  # Microservices - HARD
            UUID("650e8400-e29b-41d4-a716-446655440007"),  # Behavioral - MEDIUM
            UUID("650e8400-e29b-41d4-a716-446655440008"),  # Behavioral teamwork - MEDIUM
            UUID("650e8400-e29b-41d4-a716-446655440009"),  # Reverse string - EASY
            UUID("650e8400-e29b-41d4-a716-446655440010"),  # Non-repeating char - MEDIUM
        ]

    async def store_question_embedding(
        self,
        question_id: UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Mock storing question embedding (no-op)."""
        # In mock mode, we just acknowledge the storage
        pass

    async def store_cv_embedding(
        self,
        cv_analysis_id: UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Mock storing CV embedding (no-op)."""
        # In mock mode, we just acknowledge the storage
        pass

    async def find_similar_questions(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return mock similar questions.

        Args:
            query_embedding: Query vector (ignored in mock)
            top_k: Number of results to return
            filters: Optional filters (difficulty, skills, etc.)

        Returns:
            List of mock question matches with metadata
        """
        # Generate mock results
        results = []
        difficulty = filters.get("difficulty", DifficultyLevel.MEDIUM) if filters else DifficultyLevel.MEDIUM

        for i in range(min(top_k, len(self._mock_question_ids))):
            # Generate realistic similarity scores (higher for first results)
            similarity = random.uniform(0.75, 0.95) - (i * 0.02)

            results.append({
                "question_id": str(self._mock_question_ids[i]),
                "similarity_score": similarity,
                "metadata": {
                    "difficulty": difficulty,
                    "skills": ["Python", "FastAPI", "PostgreSQL"][: i % 3 + 1],
                    "tags": ["backend", "api", "database"][: i % 3 + 1],
                },
            })

        return results

    async def find_similar_answers(
        self,
        answer_embedding: list[float],
        reference_embeddings: list[list[float]],
    ) -> float:

        return random.uniform(0.85, 0.9)

    async def get_embedding(
        self,
        text: str,
    ) -> list[float]:
        """Generate mock embedding vector.

        Args:
            text: Text to embed

        Returns:
            Mock 1536-dimensional vector (OpenAI embedding size)
        """
        # Return a mock embedding with realistic dimensions
        # OpenAI embeddings are 1536-dimensional
        return [random.uniform(-1.0, 1.0) for _ in range(1536)]

    async def delete_embeddings(
        self,
        ids: list[UUID],
    ) -> None:
        """Mock deleting embeddings (no-op)."""
        # In mock mode, we just acknowledge the deletion
        pass