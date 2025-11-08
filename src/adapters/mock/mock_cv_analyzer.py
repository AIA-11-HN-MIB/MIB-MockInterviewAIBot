"""Mock CV Analyzer adapter for development and testing."""

import random
from pathlib import Path
from uuid import UUID, uuid4

from ...domain.models.cv_analysis import CVAnalysis, ExtractedSkill
from ...domain.ports.cv_analyzer_port import CVAnalyzerPort


class MockCVAnalyzerAdapter(CVAnalyzerPort):
    """Mock CV analyzer that returns realistic but simulated analysis.

    This adapter simulates CV parsing and skill extraction without
    requiring actual document processing or LLM API calls.

    The mock provides deterministic results based on filename patterns:
    - Files with "junior" → 2-3 skills, 1-2 years exp, EASY difficulty
    - Files with "senior" → 5-6 skills, 6-10 years exp, HARD difficulty
    - Default (mid-level) → 4-5 skills, 3-5 years exp, MEDIUM difficulty
    """

    # Skill database organized by experience level
    JUNIOR_SKILLS = [
        ExtractedSkill(skill="Python", category="technical", proficiency="intermediate", years=1.5),
        ExtractedSkill(skill="Git", category="technical", proficiency="beginner", years=1.0),
        ExtractedSkill(skill="SQL", category="technical", proficiency="beginner", years=0.5),
        ExtractedSkill(skill="Communication", category="soft", proficiency="intermediate"),
        ExtractedSkill(skill="Team Collaboration", category="soft", proficiency="beginner"),
    ]

    MID_SKILLS = [
        ExtractedSkill(skill="Python", category="technical", proficiency="advanced", years=3.5),
        ExtractedSkill(skill="FastAPI", category="technical", proficiency="intermediate", years=2.0),
        ExtractedSkill(skill="PostgreSQL", category="technical", proficiency="intermediate", years=2.5),
        ExtractedSkill(skill="Docker", category="technical", proficiency="intermediate", years=1.5),
        ExtractedSkill(skill="REST APIs", category="technical", proficiency="advanced", years=3.0),
        ExtractedSkill(skill="Problem Solving", category="soft", proficiency="advanced"),
        ExtractedSkill(skill="Leadership", category="soft", proficiency="intermediate"),
    ]

    SENIOR_SKILLS = [
        ExtractedSkill(skill="Python", category="technical", proficiency="expert", years=7.0),
        ExtractedSkill(skill="System Design", category="technical", proficiency="expert", years=5.0),
        ExtractedSkill(skill="Microservices", category="technical", proficiency="advanced", years=4.0),
        ExtractedSkill(skill="PostgreSQL", category="technical", proficiency="expert", years=6.0),
        ExtractedSkill(skill="AWS", category="technical", proficiency="advanced", years=4.5),
        ExtractedSkill(skill="Architecture", category="technical", proficiency="expert", years=5.5),
        ExtractedSkill(skill="Leadership", category="soft", proficiency="expert"),
        ExtractedSkill(skill="Mentoring", category="soft", proficiency="advanced"),
    ]

    SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx"}

    async def extract_text_from_file(self, file_path: str) -> str:
        """Extract mock text from file.

        Args:
            file_path: Path to CV file

        Returns:
            Mock CV text content

        Raises:
            ValueError: If file extension not supported
        """
        path = Path(file_path)
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Return realistic mock CV text
        return """
        John Doe
        Software Engineer
        Email: john.doe@example.com
        Phone: +1-555-0100

        PROFESSIONAL SUMMARY
        Experienced software engineer with strong background in backend development,
        API design, and cloud infrastructure. Passionate about clean code and scalable
        systems.

        EXPERIENCE
        Senior Software Engineer at Tech Corp (2020-Present)
        - Designed and implemented microservices architecture serving 1M+ users
        - Led team of 5 engineers in migrating monolith to event-driven architecture
        - Reduced API latency by 40% through optimization and caching strategies
        - Mentored junior developers and conducted code reviews

        Software Engineer at StartupXYZ (2018-2020)
        - Developed REST APIs using Python and FastAPI
        - Implemented PostgreSQL database schema and query optimization
        - Built CI/CD pipelines with Docker and GitHub Actions
        - Collaborated with frontend team on API integration

        TECHNICAL SKILLS
        Languages: Python, SQL, JavaScript
        Frameworks: FastAPI, Django, Flask
        Databases: PostgreSQL, Redis, MongoDB
        Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
        Tools: Git, GitHub Actions, Terraform

        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology, 2018

        CERTIFICATIONS
        - AWS Certified Solutions Architect
        - Python Professional Certification
        """

    async def analyze_cv(
        self,
        cv_file_path: str,
        candidate_id: str,
    ) -> CVAnalysis:
        """Analyze CV and extract structured information.

        Args:
            cv_file_path: Path to CV file
            candidate_id: UUID of the candidate

        Returns:
            CVAnalysis with extracted skills and metadata
        """
        # Extract text from file
        extracted_text = await self.extract_text_from_file(cv_file_path)

        # Detect experience level from filename
        filename = Path(cv_file_path).stem.lower()
        if "junior" in filename:
            experience_level = "junior"
            skills = self.JUNIOR_SKILLS[:3]  # 2-3 skills
            years = random.uniform(1.0, 2.0)
            difficulty = "easy"
            education = "Bachelor's"
        elif "senior" in filename:
            experience_level = "senior"
            skills = self.SENIOR_SKILLS[:6]  # 5-6 skills
            years = random.uniform(6.0, 10.0)
            difficulty = "hard"
            education = "Master's"
        else:
            experience_level = "mid"
            skills = self.MID_SKILLS[:5]  # 4-5 skills
            years = random.uniform(3.0, 5.0)
            difficulty = "medium"
            education = "Bachelor's"

        # Generate suggested topics from skills
        technical_skills = [s for s in skills if s.category == "technical"]
        suggested_topics = [skill.name for skill in technical_skills]

        # Add some topic variations
        if any(s.name in ["Python", "FastAPI"] for s in skills):
            suggested_topics.append("Backend Development")
        if any(s.name in ["PostgreSQL", "SQL"] for s in skills):
            suggested_topics.append("Database Design")
        if any(s.name in ["System Design", "Architecture"] for s in skills):
            suggested_topics.append("System Architecture")

        # Create CV analysis
        return CVAnalysis(
            id=uuid4(),
            candidate_id=UUID(candidate_id),
            cv_file_path=cv_file_path,
            extracted_text=extracted_text,
            skills=skills,
            work_experience_years=round(years, 1),
            education_level=education,
            suggested_topics=suggested_topics[:5],  # Limit to 5 topics
            suggested_difficulty=difficulty,
            embedding=None,  # Mock doesn't generate embeddings
            summary=f"Mock CV analysis: {experience_level.title()}-level candidate with {years:.1f} years of experience",
            metadata={
                "experience_level": experience_level,
                "file_name": Path(cv_file_path).name,
                "mock_adapter": True,
            },
        )
