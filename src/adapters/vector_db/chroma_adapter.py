
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

chromaDB_client = chromadb.PersistentClient(path=CHROMA_PATH)
cv_collection = chromaDB_client.get_or_create_collection(name=COLLECTION_NAME)

class ChromaAdapter(VectorSearchPort):
    """Interface for vector database operations.

    This port abstracts vector storage and semantic search, allowing easy
    switching between Pinecone, Weaviate, ChromaDB, etc.
    """

    def __init__(self):
        pass

    async def store_cv_embedding(self, cv_analysis_id, embedding, metadatas):
        try:
            cv_collection.add(
                ids=[cv_analysis_id],
                embeddings=[embedding],
                metadatas=[metadatas]
            )
        except Exception as e:
            print(f"Error storing CV embedding: {e}")