
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

load_dotenv()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
CV_COLLECTION_NAME = "cv_embedding"
QUESTION_COLLECTION_NAME = "question_embedding"


chromaDB_client = chromadb.PersistentClient(path=CHROMA_PATH)
cv_collection = chromaDB_client.get_or_create_collection(name=CV_COLLECTION_NAME, namespace="cv_process")
question_collection = chromaDB_client.get_or_create_collection(name=QUESTION_COLLECTION_NAME, namespace="question_process")

embedding_client = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key = os.getenv("TEXT_EMBEDDING_API_KEY"),
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
        
    """
    This method calculate similarity between answer and given answer
    """
    async def find_similar_answers(self, answer_embedding: list[float], reference_embeddings: list[list[float]]):
        results = question_collection.query(
        query_embeddings=reference_embeddings,
        n_results=1,                            
        where={"answer": {"$exists": True}},    
        include=["embeddings", "metadatas"]
        )

        embeddings_nested = results["embeddings"]
        embeddings = [
            embedding
            for embedding_list in embeddings_nested
            for embedding in embedding_list
        ]

        ref_array = np.array(embeddings, dtype=np.float32)
        ans_array = np.array(answer_embedding, dtype=np.float32).reshape(1, -1)
        ref_norms = np.linalg.norm(ref_array, axis=1, keepdims=True)
        ans_norm = np.linalg.norm(ans_array)

        if ans_norm == 0 or np.any(ref_norms == 0):
            return 0.0

        ref_normalized = ref_array / ref_norms
        ans_normalized = ans_array / ans_norm

        similarities = np.dot(ref_normalized, ans_normalized.T).flatten()

        return float(np.max(similarities))
        
    async def store_question_embedding(self, question_id: UUID, embedding: list[float], metadatas: dict[str, Any]):
        try:
            question_collection.add(
                ids=[question_id],
                embeddings=[embedding],
                metadatas=[metadatas]
            )
        except Exception as e:
            print(f"Error storing question embedding: {e}")