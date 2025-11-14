"""Pinecone vector database adapter implementation."""

from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from pinecone import Pinecone, ServerlessSpec

from ...domain.ports.vector_search_port import VectorSearchPort


class PineconeAdapter(VectorSearchPort):
    """Pinecone implementation of vector search port.

    This adapter encapsulates all Pinecone-specific logic. Switching to
    another vector database (Weaviate, ChromaDB) only requires implementing
    the VectorSearchPort interface.
    """

    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small",
    ):
        """Initialize Pinecone adapter.

        Args:
            api_key: Pinecone API key
            environment: Pinecone environment
            index_name: Name of the Pinecone index to use
            openai_api_key: OpenAI API key for embeddings
            embedding_model: OpenAI embedding model to use
        """
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.index = None
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.embedding_model = embedding_model
        self.environment = environment

        # Initialize index if it doesn't exist
        self._ensure_index_exists()

    def _ensure_index_exists(self) -> None:
        """Ensure the Pinecone index exists."""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            # Create index with 1536 dimensions (OpenAI text-embedding-3-small)
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=self.environment),
            )

        self.index = self.pc.Index(self.index_name)

    async def store_question_embedding(
        self,
        question_id: UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Store a question's vector embedding in Pinecone.

        Args:
            question_id: Unique question identifier
            embedding: Vector embedding
            metadata: Additional metadata
        """
        self.index.upsert(
            vectors=[
                {
                    "id": f"question_{str(question_id)}",
                    "values": embedding,
                    "metadata": {
                        **metadata,
                        "type": "question",
                        "question_id": str(question_id),
                    },
                }
            ]
        )

    async def store_cv_embedding(
        self,
        cv_analysis_id: UUID,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Store a CV analysis vector embedding in Pinecone.

        Args:
            cv_analysis_id: Unique CV analysis identifier
            embedding: Vector embedding
            metadata: Additional metadata
        """
        self.index.upsert(
            vectors=[
                {
                    "id": f"cv_{str(cv_analysis_id)}",
                    "values": embedding,
                    "metadata": {
                        **metadata,
                        "type": "cv",
                        "cv_analysis_id": str(cv_analysis_id),
                    },
                }
            ]
        )

    async def find_similar_questions(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Find similar questions using semantic search.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Optional filters

        Returns:
            List of similar questions with similarity scores
        """
        # Build Pinecone filter
        pinecone_filter = {"type": "question"}
        if filters:
            pinecone_filter.update(filters)

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=pinecone_filter,
            include_metadata=True,
        )

        # Format results
        similar_questions = []
        for match in results.matches:
            similar_questions.append(
                {
                    "question_id": match.metadata.get("question_id"),
                    "score": match.score,
                    "metadata": match.metadata,
                }
            )

        return similar_questions

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
        # For simplicity, calculate cosine similarity with the first reference
        # In production, you might want to average or take max similarity
        if not reference_embeddings:
            return 0.0

        # Store temporary reference embedding
        temp_id = "temp_reference"
        self.index.upsert(
            vectors=[
                {
                    "id": temp_id,
                    "values": reference_embeddings[0],
                    "metadata": {"type": "temp"},
                }
            ]
        )

        # Query for similarity
        results = self.index.query(
            vector=answer_embedding,
            top_k=1,
            filter={"type": "temp"},
        )

        # Clean up temp vector
        self.index.delete(ids=[temp_id])

        return results.matches[0].score if results.matches else 0.0

    async def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Vector embedding
        """
        response = await self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )

        return response.data[0].embedding

    async def delete_embeddings(self, ids: list[UUID]) -> None:
        """Delete embeddings by IDs.

        Args:
            ids: List of IDs to delete
        """
        # Delete both question and CV embeddings
        pinecone_ids = []
        for id_ in ids:
            pinecone_ids.extend([f"question_{str(id_)}", f"cv_{str(id_)}"])

        self.index.delete(ids=pinecone_ids)
