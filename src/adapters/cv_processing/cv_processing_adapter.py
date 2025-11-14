from uuid import uuid4
import spacy
import os
import json
import pdfplumber
from uuid import UUID
from langchain_openai import OpenAIEmbeddings
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List
from datetime import datetime, timezone

from langchain_text_splitters import RecursiveCharacterTextSplitter
from ...domain.ports.cv_analyzer_port import CVAnalyzerPort
from ...domain.ports.vector_search_port import VectorSearchPort
from ...domain.ports.candidate_repository_port import CandidateRepositoryPort

from ...domain.models.cv_analysis import CVAnalysis
from ...domain.models.cv_analysis import ExtractedSkill
from ...domain.models.candidate import Candidate

from ...infrastructure.config import Settings
_nlp_models = {}

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
setting = Settings()

openai_client = AsyncOpenAI(base_url=setting.azure_openai_endpoint, api_key=setting.azure_openai_api_key)

# embeddings_client = OpenAIEmbeddings(model=setting.openai_embedding_api_key, api_key=setting.openai_embedding_api_key)

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
    def create_metadata_from_summary(summary: str, difficulty: str) -> Dict[str, Any]:
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
            "difficulty": difficulty,
            "saved_at": savetime
        }
        return metadata

class CVProcessingAdapter(CVAnalyzerPort):
    
    def __init__(
            self,
            embedding_model:str="text-embedding-3-small",
            model:str="gpt-4o-mini",
            candidate_repository_port: CandidateRepositoryPort = None):

        self.settings  = Settings()
        self.embedding_model = embedding_model or self.settings.openai_embedding_model or "text-embedding-3-small"
        self.preprocessing = CVEmbeddingPreprocessor()
        self.model = model
        self.candidate_repository_port = candidate_repository_port

    SKILL_PATTERNS = load_skill_patterns()
    @staticmethod
    def read_cv(file_path: str) -> str:
        if file_path.lower().endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip()
            
    async def generate_cv_info_from_text(self, cv_text: str) -> str:
        date=datetime.now(timezone.utc)
        prompt = f"""
            Summarize this candidate in 3-5 sentences for HR evaluation.

            cv info: {cv_text}

            FOCUS:
            - Years of experience (both number of experience and company)
            - Core technical skills
            - Notable projects/roles
            - Education (if mentioned)

            RESPONSE VALUEs:
            Response format (as a valid JSON object with these exact keys):
            {{
            "candidate_name": "string",
            "email": "string",
            "summary": "string",
            "job_level": "string",
            "experience": "experience (total worked year (form start to {date}))" (float number only),
            "skills": ["string"],
            "education_level": "string"
            }}

            IMPORTANT: 
            Return a valid JSON object without any markdown formatting (no ```json or ``` markers).
            The response must be a single, parseable JSON object.
            Keep under 200 words. Be concise and professional. 
        """

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[Summary generation failed: {e}]"
        
    async def generate_interview_topics(self, skills: list[str], job_rank: str, experience_years: int) -> list[str]:
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
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": system_prompt}],
                temperature=0.5,
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()
            json_content = json.loads(clean_json_string(content))
            for topic in json_content.get("interview_topics", []):
                topics.add(topic)
        except Exception as e:
            topics.add(f"[Topic generation failed: {e}]")
            print("Error generating topics: ", e)
        return list(topics)

    def generate_interview_difficulty(self, experience_years: float) -> str:
        if experience_years >= 10:
            return "expert"
        elif experience_years >= 5:
            return "advanced"
        elif experience_years >= 2:
            return "medium"
        else:
            return "beginner"

    async def generate_candidate_from_summary(
        self,
        extracted_info: str,
        cv_file_path: str,
        candidate_id: UUID
    ) -> Candidate:
        """
        Generate a Candidate object from CV extracted information using GPT-4o-mini.

        Args:
        extracted_info: JSON string containing CV extracted information
        cv_file_path: Path to the candidate's CV file
        
        Returns:
            Candidate: Populated Candidate object
        """
        try:
            # Prepare the prompt for GPT-4o-mini
            prompt = f"""
            Extract candidate information from the following CV extracted_info:
            {extracted_info}
            
            Return a JSON object with the following structure:
            {{
                "name": "Full Name",
                "email": "email@example.com"
                // Only include these two fields
            }}
        
            Rules:
            - If name is not found, use "Unknown Candidate"
            - If email is not found, use "no-email@example.com"
            - Only include the JSON object in your response
            """
        
            # Call GPT-4o-mini
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts candidate information from CV summaries."},
                    {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2  # Keep it deterministic
            )
            # Parse the response
            candidate_data = json.loads(response.choices[0].message.content.strip())
            # Create and return the Candidate object
            return Candidate(
                id=candidate_id,
                name=candidate_data.get("name", "Unknown Candidate"),
                email=candidate_data.get("email", "no-email@example.com"),
                cv_file_path=cv_file_path
            )
        
        except Exception as e:
            print(f"Error generating candidate from summary: {e}")
            # Return a default candidate with the CV file path

        return Candidate(
            id=uuid4(),
            name="Unknown Candidate",
            email="no-email@example.com",
            cv_file_path=cv_file_path
        )
    
    async def analyze_cv(self, cv_file_path: str, candidate_id: UUID) -> CVAnalysis:
        cv_text = self.read_cv(cv_file_path)
        try:
            summary_info = await self.generate_cv_info_from_text(cv_text)
            # print(summary_info)
        except Exception as e:
            print("Error generating summary: ", e)
        
        job_rank = json.loads(summary_info).get("job_level", "N/A")
        # print(job_rank)
        skills_name = json.loads(summary_info).get("skills", [])
        print("Extracted skills:", skills_name)
        skills = [
            ExtractedSkill(skill=skill, category="technical")
            for skill in skills_name
        ]
        # print(skills)
        experience_years = json.loads(summary_info).get("experience")
        # print(experience_years)
        education_level = json.loads(summary_info).get("education_level", "N/A")
        # print(education_level)

        try:
            suggested_topics = await self.generate_interview_topics(
                skills_name, 
                job_rank, 
                experience_years)
            # print("suggested_topics: ", suggested_topics)
        except Exception as e:
            print("Error generating topics: ", e)
        
        try:
            suggested_difficulty = self.generate_interview_difficulty(experience_years)
            # print(suggested_difficulty)
        except Exception as e:
            print("Error generating difficulty: ", e)

        try:
            metadata = self.preprocessing.create_metadata_from_summary(
                summary=summary_info, 
                difficulty=suggested_difficulty)
            # print(metadata)
        except Exception as e:
            print("Error creating metadata: ", e)
        
        return CVAnalysis(
            candidate_id=candidate_id,
            cv_file_path=cv_file_path,
            extracted_text=cv_text,
            skills=skills,
            work_experience_years=experience_years,
            education_level=education_level,
            suggested_topics=suggested_topics,
            suggested_difficulty=suggested_difficulty,
            embedding=None,
            summary=json.loads(summary_info).get("summary", ""),
            metadata=metadata,
            created_at=datetime.now().isoformat()   
        )
    