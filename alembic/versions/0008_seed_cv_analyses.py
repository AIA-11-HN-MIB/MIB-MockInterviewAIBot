"""seed cv analyses

Revision ID: 0008
Revises: 0007
Create Date: 2025-12-11 10:00:00

Creates CV analyses for all new candidates with realistic skills and profiles.
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import String, Text, Float, DateTime


# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, Sequence[str], None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed CV analyses for new candidates."""

    metadata = MetaData()
    now = datetime.utcnow()

    # Define table schema for bulk insert
    cv_analyses_table = Table(
        'cv_analyses', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('candidate_id', UUID(as_uuid=True)),
        Column('cv_file_path', String),
        Column('extracted_text', Text),
        Column('skills', JSONB),
        Column('work_experience_years', Float),
        Column('education_level', String),
        Column('suggested_topics', ARRAY(String)),
        Column('suggested_difficulty', String),
        Column('summary', Text),
        Column('metadata', JSONB),
        Column('created_at', DateTime),
    )

    # Insert CV analyses for all 7 new candidates
    op.bulk_insert(cv_analyses_table, [
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),  # Alice Chen
            'cv_file_path': '/uploads/cvs/alice_chen_cv.pdf',
            'extracted_text': 'Alice Chen - Junior Full Stack Developer. 1.5 years experience in React, Node.js, and PostgreSQL. Recent computer science graduate with strong foundation in web development. Experience building responsive web applications and RESTful APIs.',
            'skills': [
                {"skill": "React", "proficiency": "intermediate", "years": 1.5, "category": "technical"},
                {"skill": "Node.js", "proficiency": "intermediate", "years": 1.5, "category": "technical"},
                {"skill": "JavaScript", "proficiency": "intermediate", "years": 1.5, "category": "technical"},
                {"skill": "PostgreSQL", "proficiency": "beginner", "years": 1, "category": "technical"},
                {"skill": "HTML/CSS", "proficiency": "intermediate", "years": 1.5, "category": "technical"},
            ],
            'work_experience_years': 1.5,
            'education_level': "Bachelor's",
            'suggested_topics': ['React Hooks', 'Async/Await', 'REST API Design', 'Database Basics', 'Testing'],
            'suggested_difficulty': 'easy',
            'summary': 'Junior full-stack developer with 1.5 years of experience. Strong in React and Node.js fundamentals. Good foundation but needs experience with advanced concepts and system design.',
            'metadata': {"keywords": ["React", "Node.js", "Junior", "Full Stack"]},
            'created_at': now - timedelta(days=13),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),  # Michael Rodriguez
            'cv_file_path': '/uploads/cvs/michael_rodriguez_cv.pdf',
            'extracted_text': 'Michael Rodriguez - Mid-level Backend Engineer. 4 years experience in Python, Django, PostgreSQL, and AWS. Specialized in building scalable REST APIs and microservices. Experience with Docker, Kubernetes, and CI/CD pipelines.',
            'skills': [
                {"skill": "Python", "proficiency": "advanced", "years": 4, "category": "technical"},
                {"skill": "Django", "proficiency": "advanced", "years": 4, "category": "technical"},
                {"skill": "PostgreSQL", "proficiency": "advanced", "years": 4, "category": "technical"},
                {"skill": "AWS", "proficiency": "intermediate", "years": 2, "category": "technical"},
                {"skill": "Docker", "proficiency": "intermediate", "years": 2, "category": "technical"},
                {"skill": "REST API", "proficiency": "advanced", "years": 4, "category": "technical"},
            ],
            'work_experience_years': 4.0,
            'education_level': "Bachelor's",
            'suggested_topics': ['System Design', 'Database Optimization', 'Microservices', 'API Design', 'SOLID Principles'],
            'suggested_difficulty': 'medium',
            'summary': 'Mid-level backend engineer with 4 years of Python and Django experience. Strong in API design and database optimization. Ready for system design and architecture discussions.',
            'metadata': {"keywords": ["Python", "Backend", "Django", "API"]},
            'created_at': now - timedelta(days=11),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),  # Sarah Williams
            'cv_file_path': '/uploads/cvs/sarah_williams_cv.pdf',
            'extracted_text': 'Sarah Williams - Senior Full Stack Developer. 8 years experience in JavaScript, TypeScript, React, Node.js, and cloud technologies. Led multiple teams and architected large-scale applications. Expert in system design and performance optimization.',
            'skills': [
                {"skill": "JavaScript", "proficiency": "expert", "years": 8, "category": "technical"},
                {"skill": "TypeScript", "proficiency": "expert", "years": 6, "category": "technical"},
                {"skill": "React", "proficiency": "expert", "years": 7, "category": "technical"},
                {"skill": "Node.js", "proficiency": "expert", "years": 8, "category": "technical"},
                {"skill": "System Design", "proficiency": "expert", "years": 5, "category": "technical"},
                {"skill": "AWS", "proficiency": "advanced", "years": 4, "category": "technical"},
                {"skill": "Docker", "proficiency": "advanced", "years": 4, "category": "technical"},
            ],
            'work_experience_years': 8.0,
            'education_level': "Master's",
            'suggested_topics': ['System Design', 'Event Loop', 'Microservices Architecture', 'Performance Optimization', 'Scalability Patterns'],
            'suggested_difficulty': 'hard',
            'summary': 'Senior full-stack developer with 8 years of experience. Expert in JavaScript ecosystem and system design. Strong leadership experience and ability to architect scalable solutions.',
            'metadata': {"keywords": ["Senior", "Full Stack", "System Design", "JavaScript"]},
            'created_at': now - timedelta(days=9),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440004'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),  # David Kim
            'cv_file_path': '/uploads/cvs/david_kim_cv.pdf',
            'extracted_text': 'David Kim - Frontend Specialist. 3 years experience in React, Vue.js, TypeScript, and modern frontend tooling. Strong UI/UX focus with expertise in state management, performance optimization, and responsive design.',
            'skills': [
                {"skill": "React", "proficiency": "advanced", "years": 3, "category": "technical"},
                {"skill": "Vue.js", "proficiency": "advanced", "years": 3, "category": "technical"},
                {"skill": "TypeScript", "proficiency": "advanced", "years": 2.5, "category": "technical"},
                {"skill": "CSS/SCSS", "proficiency": "advanced", "years": 3, "category": "technical"},
                {"skill": "Redux", "proficiency": "intermediate", "years": 2, "category": "technical"},
                {"skill": "Webpack", "proficiency": "intermediate", "years": 2, "category": "technical"},
            ],
            'work_experience_years': 3.0,
            'education_level': "Bachelor's",
            'suggested_topics': ['React Hooks', 'State Management', 'Performance Optimization', 'Frontend Architecture', 'Testing'],
            'suggested_difficulty': 'medium',
            'summary': 'Frontend specialist with 3 years of React and Vue.js experience. Strong focus on UI/UX and frontend performance. Good understanding of modern frontend patterns.',
            'metadata': {"keywords": ["Frontend", "React", "Vue.js", "UI/UX"]},
            'created_at': now - timedelta(days=7),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440005'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),  # Emily Thompson
            'cv_file_path': '/uploads/cvs/emily_thompson_cv.pdf',
            'extracted_text': 'Emily Thompson - DevOps Engineer. 5 years experience in CI/CD, Kubernetes, Docker, AWS, Terraform, and infrastructure automation. Expert in cloud architecture and monitoring solutions.',
            'skills': [
                {"skill": "Kubernetes", "proficiency": "expert", "years": 4, "category": "technical"},
                {"skill": "Docker", "proficiency": "expert", "years": 5, "category": "technical"},
                {"skill": "AWS", "proficiency": "expert", "years": 5, "category": "technical"},
                {"skill": "Terraform", "proficiency": "advanced", "years": 3, "category": "technical"},
                {"skill": "CI/CD", "proficiency": "expert", "years": 5, "category": "technical"},
                {"skill": "Linux", "proficiency": "advanced", "years": 5, "category": "technical"},
                {"skill": "Python", "proficiency": "intermediate", "years": 3, "category": "technical"},
            ],
            'work_experience_years': 5.0,
            'education_level': "Bachelor's",
            'suggested_topics': ['System Design', 'Scalability', 'Infrastructure', 'Cloud Architecture', 'Container Orchestration'],
            'suggested_difficulty': 'hard',
            'summary': 'DevOps engineer with 5 years of experience in cloud infrastructure and automation. Expert in Kubernetes, Docker, and AWS. Strong in infrastructure as code and CI/CD pipelines.',
            'metadata': {"keywords": ["DevOps", "Kubernetes", "AWS", "Infrastructure"]},
            'created_at': now - timedelta(days=5),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440006'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440006'),  # James Anderson
            'cv_file_path': '/uploads/cvs/james_anderson_cv.pdf',
            'extracted_text': 'James Anderson - Full Stack Developer. 2.5 years experience in Java, Spring Boot, React, and PostgreSQL. Experience building enterprise applications and RESTful services.',
            'skills': [
                {"skill": "Java", "proficiency": "intermediate", "years": 2.5, "category": "technical"},
                {"skill": "Spring Boot", "proficiency": "intermediate", "years": 2.5, "category": "technical"},
                {"skill": "React", "proficiency": "intermediate", "years": 2, "category": "technical"},
                {"skill": "PostgreSQL", "proficiency": "intermediate", "years": 2.5, "category": "technical"},
                {"skill": "REST API", "proficiency": "intermediate", "years": 2.5, "category": "technical"},
            ],
            'work_experience_years': 2.5,
            'education_level': "Bachelor's",
            'suggested_topics': ['Java Fundamentals', 'Spring Framework', 'Database Design', 'API Design', 'Testing'],
            'suggested_difficulty': 'easy',
            'summary': 'Full-stack developer with 2.5 years of Java and Spring Boot experience. Good foundation in enterprise development. Still learning advanced concepts.',
            'metadata': {"keywords": ["Java", "Spring Boot", "Full Stack"]},
            'created_at': now - timedelta(days=3),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440007'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),  # Lisa Martinez
            'cv_file_path': '/uploads/cvs/lisa_martinez_cv.pdf',
            'extracted_text': 'Lisa Martinez - Backend Engineer. 6 years experience in Python, FastAPI, PostgreSQL, Redis, and distributed systems. Expert in building high-performance APIs and microservices architecture.',
            'skills': [
                {"skill": "Python", "proficiency": "expert", "years": 6, "category": "technical"},
                {"skill": "FastAPI", "proficiency": "expert", "years": 4, "category": "technical"},
                {"skill": "PostgreSQL", "proficiency": "expert", "years": 6, "category": "technical"},
                {"skill": "Redis", "proficiency": "advanced", "years": 4, "category": "technical"},
                {"skill": "Microservices", "proficiency": "advanced", "years": 3, "category": "technical"},
                {"skill": "Docker", "proficiency": "advanced", "years": 4, "category": "technical"},
            ],
            'work_experience_years': 6.0,
            'education_level': "Master's",
            'suggested_topics': ['System Design', 'Microservices', 'Database Optimization', 'Caching Strategies', 'API Performance'],
            'suggested_difficulty': 'hard',
            'summary': 'Senior backend engineer with 6 years of Python experience. Expert in FastAPI and building scalable microservices. Strong in database optimization and caching strategies.',
            'metadata': {"keywords": ["Python", "Backend", "Microservices", "FastAPI"]},
            'created_at': now - timedelta(days=1),
        },
    ])

    print("[OK] Seeded 7 CV analyses")


def downgrade() -> None:
    """Remove seeded CV analyses."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM cv_analyses WHERE id IN (
            '860e8400-e29b-41d4-a716-446655440001',
            '860e8400-e29b-41d4-a716-446655440002',
            '860e8400-e29b-41d4-a716-446655440003',
            '860e8400-e29b-41d4-a716-446655440004',
            '860e8400-e29b-41d4-a716-446655440005',
            '860e8400-e29b-41d4-a716-446655440006',
            '860e8400-e29b-41d4-a716-446655440007'
        )
    """))

    print("[OK] Removed seeded CV analyses")

