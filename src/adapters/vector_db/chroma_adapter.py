
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from ...domain.ports.vector_search_port import VectorSearchPort

def create_metadata_from_summary(summary: str) -> str:
    """
    Tạo metadata từ summary (nội dung tóm tắt CV)

    Args:
        summary (str): Nội dung tóm tắt CV

    Returns:
        str: Metadata dưới dạng chuỗi JSON
    """
    # Giả sử summary đã là một chuỗi JSON hợp lệ
    return metadata

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

    