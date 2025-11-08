
import os
import chromadb
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from ...domain.ports.vector_search_port import VectorSearchPort

load_dotenv()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "cv_embedding"

chromaDB_client = chromadb.PersistentClient(path=CHROMA_PATH)
cv_collection = chromaDB_client.get_or_create_collection(name=COLLECTION_NAME)

embedding_client = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key = os.getenv("TEXT_EMBEDDING_API_KEY"),
    dimensions=1536,
    max_retries=3,
    request_timeout=30
)

def generate_interview_difficulty(experience_years: float) -> str:
        if experience_years >= 10:
            return "expert"
        elif experience_years >= 5:
            return "advanced"
        elif experience_years >= 2:
            return "medium"
        else:
            return "beginner"

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

        difficulty = generate_interview_difficulty(json.loads(cleaned_text).get("experience"))
        embeđding_text = f"""
            Candidate Name: {json.loads(cleaned_text).get("candidate_name", "N/A")}
            Candidate Summary: {cleaned_text}
            Skills: {', '.join(json.cleaned_text(cleaned_text).get("skills", []))}
            Experience: {json.loads(text).get("experience", 0)} years
            Education Level: {json.loads(cleaned_text).get("education_level", "N/A")}
            Difficulty: {difficulty}
        """.strip()

        try:
            embedding = embedding_client.embed_query(embeđding_text)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            embedding = []
        return embedding
        
    async def delete_embeddings(self, ids):
        try:
            cv_collection.delete(ids=ids)
        except Exception as e:
            print(f"Error deleting embeddings: {e}")
        pass