import spacy
import os
import json
import pdfplumber
from langchain_openai import OpenAIEmbeddings
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List
from datetime import datetime, timezone
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ...domain.ports.cv_analyzer_port import CVProcessingPort
from ...domain.models.cv_analysis import CVAnalysis
from ...domain.ports.vector_search_port import VectorSearchPort

_nlp_models = {}

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

embeddings_client = OpenAIEmbeddings(model="text-embedding-3-small", api_key=os.getenv("TEXT_EMBEDDING_API_KEY"))

def get_nlp_model(lang: str):
    if lang not in _nlp_models:
        try:
            _nlp_models[lang] = spacy.load("vi_core_news_sm" if lang == 'vi' else "en_core_web_sm")
        except:
            _nlp_models[lang] = spacy.load("en_core_web_sm")
        return _nlp_models[lang]

def load_skill_patterns() -> Dict:
    path = os.path.join(os.path.dirname(__file__), "skill_patterns.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "common": data.get("common", []),
        "get_patterns": lambda lang: data.get("common", []) + data.get(lang, [])
    }

def clean_json_string(s: str) -> str:
    """Trích xuất JSON từ chuỗi dù có code block, text thừa"""
    if not s:
        return "{}"
    s = s.strip()

    # Bỏ code block ```json ... ```
    s = re.sub(r"^```json\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"```$", "", s)

    # Tìm {} đầu tiên và cuối cùng
    start = s.find("{")
    end = s.rfind("}") + 1
    if start == -1 or end == 0:
        return "{}"
    return s[start:end]

class CVEmbeddingPreprocessor:
    @staticmethod
    def create_metadata_from_summary(self, summary: str, difficulty: str) -> Dict[str, Any]:
        summarized_info = summary
        candidate_name = json.loads(summary).get("candidate_name", "N/A")
        skills = json.loads(summary).get("skills", [])
        experience_years = json.loads(summary).get("experience", 0)
        education_level = json.loads(summary).get("education_level", "N/A")
        savetime = datetime.now().isoformat()

        metadata = {
            "candidate_name": candidate_name,
            "summary": summarized_info,
            "skills": skills,
            "experience_years": experience_years,
            "education_level": education_level,
            "difficulty": difficulty,
            "saved_at": savetime
        }
        return metadata

class CVProcessingAdapter(CVProcessingPort):
    
    def __init__(
            self,
            api_key:str,
            openai_api_key:str,
            embedding_model:str="text-embedding-3-small",
            model:str="gpt-4o-mini",
            vector_db: VectorSearchPort = None):
        self.api_key = api_key
        self.openai_api_key = openai_api_key
        self.embedding_model = embedding_model
        self.preprocessing = CVEmbeddingPreprocessor()
        self.model = model
        self.vector_db = vector_db

    SKILL_PATTERNS = load_skill_patterns()
    
    def read_cv(file_path: str) -> str:
        if file_path.lower().endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip()
            
    def generate_cv_info_from_text(self, cv_text: str) -> str:
        date=datetime.now(timezone.utc)
        prompt = f"""
            Summarize this candidate in 3-5 sentences for HR evaluation.

            cv info: {cv_text}

            Focus on:
            - Years of experience (both number of experience and company)
            - Core technical skills
            - Notable projects/roles
            - Education (if mentioned)

            Keep under 200 words. Be concise and professional. 
            Response in JSON format with keys: "candidate_name" "summary", "job_level", "experience (total worked year (form start to {date}))", "skills", "education_level".
            """

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[Summary generation failed: {e}]"
        
    def generate_interview_topics(self, skills: list[str], job_rank: str, experience_years: int) -> list[str]:
        topics = set()
        system_prompt = f"""
            As a techincal interviewer, generate at least 6 interview topics based on candidate skills and experience.
            Skills: {', '.join(skills)}
            Job Rank: {job_rank}
            Years of Experience: {experience_years}

            Focus:
            - Technical depth.
            - Practical applications.
            - Problem-solving related to the skills.
            - Topic only, no subtopics or questions.
            - Each topic should be concise, maximum 5 words.

            Constrain:
            - Keep under 400 words.
            - Response in Json format with a list of topics follow this format:
            {{
                "interview_topics": [
                    "topic 1",
                    "topic 2",
                    "...",
                    "topic n"
                ]
            }}
            """
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": system_prompt}],
                temperature=0.5,
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()
            json_content = json.loads(clean_json_string(content))
            for topic in json_content.get("topics", []):
                topics.add(topic)
        except Exception as e:
            topics.add(f"[Topic generation failed: {e}]")
        return list(topics)

        
    async def analyze_cv(self, cv_file_path: str, candidate_id: str) -> CVAnalysis:
        cv_text = self.read_cv(cv_file_path)
        summary_info = self.generate_cv_info_from_text(cv_text)
        job_rank = json.loads(summary_info).get("job_level", "N/A")
        skills = json.loads(summary_info).get("skills", [])
        experience_years = json.loads(summary_info).get("experience")
        education_level = json.loads(summary_info).get("education_level", "N/A")
        suggested_topics = self.generate_interview_topics(skills, job_rank, experience_years)
        suggested_difficulty = self.generate_interview_difficulty(experience_years)
        metadata = await self.preprocessing.create_metadata_from_summary(summary=summary_info, difficulty=suggested_difficulty)
        embedding = await self.vector_db.get_embedding(cv_text)

        await self.vector_db.store_cv_embedding(
            cv_analysis_id=candidate_id,
            embedding=embedding,
            metadatas=metadata
        )

        return CVAnalysis(
            candidate_id=candidate_id,
            cv_file_path=cv_file_path,
            extracted_text=cv_text,
            skills=skills,
            work_experience_years=experience_years,
            education_level=education_level,
            suggested_topics=suggested_topics,
            suggested_difficulty=suggested_difficulty,
            embedding=embedding,
            summary=json.loads(summary_info).get("summary", ""),
            metadata=metadata,
            created_at=datetime.now().isoformat()   
        )
    