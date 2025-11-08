
import os
import chromadb
import json
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from ...domain.ports.vector_search_port import VectorSearchPort

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "cv_embedding"

embeddings_client = OpenAIEmbeddings(model="text-embedding-3-small", api_key=os.getenv("TEXT_EMBEDDING_API_KEY"))

chromaDB_client = chromadb.PersistentClient(path=CHROMA_PATH)
cv_collection = chromaDB_client.get_or_create_collection(name=COLLECTION_NAME)

def create_metadata_from_summary(summary: str) -> Dict[str, Any]:
    summarized_info = summary
    skills = json.loads(summary).get("skills", [])
    experience_years = json.loads(summary).get("experience", 0)
    education_level = json.loads(summary).get("education_level", "N/A")
    savetime = datetime.now().isoformat()

    metadata = {
        "summary": summarized_info,
        "skills": skills,
        "experience_years": experience_years,
        "education_level": education_level,
        "saved_at": savetime
    }
    return metadata

def create_embedding_info_from_summary(summary: str) -> List[float]:
    text = f"""
    Candidate Summary: {summary}
    Skills: {', '.join(json.loads(summary).get("skills", []))}
    Experience: {json.loads(summary).get("experience", 0)} years
    Education Level: {json.loads(summary).get("education_level", "N/A")}
    """.strip()
    try:
        embedding = embeddings_client.embed_query(text)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        embedding = []
    return embedding

class ChromaAdapter(VectorSearchPort):
    """Interface for vector database operations.

    This port abstracts vector storage and semantic search, allowing easy
    switching between Pinecone, Weaviate, ChromaDB, etc.
    """

    def __init__(
            self,
            dimension: int,
            embedding_model: str,
            index_name: str):
        
        self.dimension = dimension
        self.embedding_model = embedding_model
        self.index_name = index_name

    metadatas = create_metadata_from_summary(summary="")
    embedding = create_embedding_info_from_summary(summary="")

    async def store_cv_embedding(self, cv_analysis_id, embedding, metadatas):
        try:
            cv_collection.add(
                ids=[cv_analysis_id],
                embeddings=[embedding],
                metadatas=[metadatas]
            )
        except Exception as e:
            print(f"Error storing CV embedding: {e}")