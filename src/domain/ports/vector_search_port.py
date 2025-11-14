"""Vector search port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID


class VectorSearchPort(ABC):
    """Interface for vector database operations.

    This port abstracts vector storage and semantic search, allowing easy
    switching between Pinecone, Weaviate, ChromaDB, etc.
    """

    @abstractmethod
    async def store_question_embedding(
        self,
        question_id: UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Store a question's vector embedding.

        Args:
            question_id: Unique question identifier
            embedding: Vector embedding
            metadata: Additional metadata (skills, tags, difficulty, etc.)
        """
        pass

    @abstractmethod
    async def store_cv_embedding(
        self,
        cv_analysis_id: UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Store a CV analysis vector embedding.

        Args:
            cv_analysis_id: Unique CV analysis identifier
            embedding: Vector embedding
            metadata: Additional metadata (skills, experience, etc.)
        """
        pass

    @abstractmethod
    async def find_similar_questions(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Find similar questions using semantic search.

        Args:
            query_embedding: Query vector (e.g., from CV or previous context)
            top_k: Number of results to return
            filters: Optional filters (e.g., difficulty, skills)

        Returns:
            List of similar questions with similarity scores
        """
        pass

    @abstractmethod
    async def find_similar_answers(
        self,
        answer_embedding: list[float],
        reference_embeddings: list[list[float]],
    ) -> float:
        """Calculate similarity between answer and reference answers.

        Args:
            answer_embedding: Candidate's answer embedding
            reference_embeddings: Reference answer embeddings

        Returns:
            Similarity score (0-1)
        """
        pass

    @abstractmethod
    async def get_embedding(
        self,
        text: str,
    ) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Vector embedding
        """
        pass

    @abstractmethod
    async def delete_embeddings(
        self,
        ids: list[UUID],
    ) -> None:
        """Delete embeddings by IDs.

        Args:
            ids: List of IDs to delete
        """
        pass
