
import os
import chromadb
import asyncio
import numpy as np
from uuid import UUID
from typing import Any, Dict
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from ...domain.ports.vector_search_port import VectorSearchPort
from ...infrastructure.config import Settings

load_dotenv()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
CV_COLLECTION_NAME = "cv_embedding"
QUESTION_COLLECTION_NAME = "question_embedding"


chromaDB_client = chromadb.PersistentClient(path=CHROMA_PATH)
cv_collection = chromaDB_client.get_or_create_collection(name=CV_COLLECTION_NAME)
question_collection = chromaDB_client.get_or_create_collection(name=QUESTION_COLLECTION_NAME)
settings = Settings()
embedding_client = OpenAIEmbeddings(
    model=settings.openai_embedding_model,
    api_key = settings.openai_embedding_api_key,
    dimensions=1536,
    max_retries=3,
    request_timeout=30
)

class ChromaAdapter(VectorSearchPort):
    """Interface for vector database operations.

    This port abstracts vector storage and semantic search, allowing easy
    switching between Pinecone, Weaviate, ChromaDB, etc.
    """

    def __init__(self):
        pass
    
    """
    This method stores a CV analysis vector embedding.
    """
    async def store_cv_embedding(self, cv_analysis_id, embedding, metadatas):
        try:
            cv_collection.add(
                ids=[cv_analysis_id],
                embeddings=[embedding],
                metadatas=[metadatas]
            )
        except Exception as e:
            print(f"Error storing CV embedding: {e}")

    """
    This method generates an embedding for the given text, in detail for this application is summarized info of a CV.
    """
    async def get_embedding(self, text):
        cleaned_text = text.strip()
        loop = asyncio.get_event_loop()
        try:
            embedding = await loop.run_in_executor(
                None,
                lambda: embedding_client.embed_query(cleaned_text)
            )
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e.__cause__}")
            return None

    """
    This method deletes embeddings by their IDs.
    """        
    async def delete_embeddings(self, ids):
        valid_ids = [id.strip() for id in ids if id and id.strip()]

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: cv_collection.delete(ids=valid_ids))
        except Exception as e:
            print(f"Error deleting embeddings: {e.__cause__}")

    """
    This method finds similar questions based on a query embedding.
    """
    async def find_similar_questions(self, query_embedding, top_k=5):

        loop = asyncio.get_event_loop()
        include_metadata = True
        try:
            raw_results = await loop.run_in_executor(
            None,
            lambda: cv_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "distances", "documents"] if include_metadata else ["distances"]
                )
            )
            ids = raw_results.get("ids", [[]])[0]
            distances = raw_results.get("distances", [[]])[0]
            metadatas = raw_results.get("metadatas", [[]])[0]
            results = []
            for i, doc_id in enumerate(ids):
                if i >= len(distances):
                    break
                distance = distances[i]
                # Convert distance → similarity (cosine: 0= giống nhất → 1=khác nhất)
                similarity_score = 1.0 - distance

                item = {
                    "id": doc_id,
                    "score": round(similarity_score, 4),
                    "distance": round(distance, 4)
                }
                if include_metadata and i < len(metadatas):
                    item["metadata"] = metadatas[i]

                results.append(item)
            return results
        except Exception as e:
            print(f"Error finding similar questions: {e}")
            return None
        
    async def store_question_embedding(self, question_id: UUID, embedding: list[float], metadatas: dict[str, Any]):
        try:
            question_collection.add(
                ids=[question_id],
                embeddings=[embedding],
                metadatas=[metadatas]
            )
        except Exception as e:
            print(f"Error storing question embedding: {e}")

    async def find_similar_answers(self, answer_embedding: list[float], reference_embeddings: list[list[float]]) -> float:
        return await super().find_similar_answers(answer_embedding, reference_embeddings)