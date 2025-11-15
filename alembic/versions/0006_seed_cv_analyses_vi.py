"""Seed CV analyses in Vietnamese

Revision ID: 0006
Revises: 0005
Create Date: 2025-01-15 00:00:00
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed CV analyses in Vietnamese."""

    metadata = MetaData()
    now = datetime.utcnow()

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

    # =============================================
    # SEED DATA - CV ANALYSES (Vietnamese)
    # =============================================
    op.bulk_insert(cv_analyses_table, [
        {
            'id': uuid.UUID('750e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'cv_file_path': '/uploads/cvs/nguyen_van_a_cv.pdf',
            'extracted_text': 'Nguyễn Văn A - Senior Full Stack Developer. Hơn 5 năm kinh nghiệm với React, Node.js, PostgreSQL.',
            'skills': [
                {"skill": "React", "proficiency": "expert", "years": 5},
                {"skill": "Node.js", "proficiency": "expert", "years": 5},
            ],
            'work_experience_years': 5.5,
            'education_level': 'Bachelor',
            'suggested_topics': ['Microservices', 'React Hooks', 'Database Design'],
            'suggested_difficulty': 'MEDIUM',
            'summary': 'Full-stack developer giàu kinh nghiệm với kỹ năng mạnh về React và Node.js.',
            'metadata': {"keywords": ["React", "Node.js"]},
            'created_at': now - timedelta(days=29),
        },
        {
            'id': uuid.UUID('750e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'cv_file_path': '/uploads/cvs/tran_thi_b_cv.pdf',
            'extracted_text': 'Trần Thị B - Backend Engineer. Hơn 3 năm kinh nghiệm với Python, Java, SQL, REST APIs và kiến trúc microservices.',
            'skills': [
                {"skill": "Python", "proficiency": "advanced", "years": 3},
                {"skill": "Java", "proficiency": "advanced", "years": 3},
                {"skill": "SQL", "proficiency": "intermediate", "years": 2},
                {"skill": "REST API", "proficiency": "advanced", "years": 3},
            ],
            'work_experience_years': 3.5,
            'education_level': 'Master',
            'suggested_topics': ['System Design', 'SOLID Principles', 'Database Optimization', 'API Design'],
            'suggested_difficulty': 'MEDIUM',
            'summary': 'Backend engineer với kỹ năng mạnh về Python và Java, có kinh nghiệm xây dựng API có khả năng mở rộng.',
            'metadata': {"keywords": ["Python", "Java", "Backend", "API"]},
            'created_at': now - timedelta(days=24),
        },
        {
            'id': uuid.UUID('750e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'cv_file_path': '/uploads/cvs/le_van_c_cv.pdf',
            'extracted_text': 'Lê Văn C - Full Stack Developer. Hơn 7 năm kinh nghiệm với JavaScript, React, Node.js, Docker và công nghệ cloud.',
            'skills': [
                {"skill": "JavaScript", "proficiency": "expert", "years": 7},
                {"skill": "React", "proficiency": "expert", "years": 6},
                {"skill": "Node.js", "proficiency": "expert", "years": 6},
                {"skill": "Docker", "proficiency": "advanced", "years": 4},
            ],
            'work_experience_years': 7.5,
            'education_level': 'Bachelor',
            'suggested_topics': ['Event Loop', 'System Design', 'Microservices', 'Async Programming'],
            'suggested_difficulty': 'HARD',
            'summary': 'Senior full-stack developer với chuyên môn sâu về hệ sinh thái JavaScript và kinh nghiệm thiết kế hệ thống.',
            'metadata': {"keywords": ["JavaScript", "React", "Node.js", "System Design"]},
            'created_at': now - timedelta(days=19),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'cv_file_path': '/uploads/cvs/pham_thi_d_cv.pdf',
            'extracted_text': 'Phạm Thị D - Junior Full Stack Developer. 1.5 năm kinh nghiệm với React, Node.js và PostgreSQL. Tốt nghiệp khoa học máy tính gần đây với nền tảng vững chắc về phát triển web. Có kinh nghiệm xây dựng ứng dụng web responsive và RESTful APIs.',
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
            'suggested_difficulty': 'EASY',
            'summary': 'Junior full-stack developer với 1.5 năm kinh nghiệm. Mạnh về React và Node.js cơ bản. Nền tảng tốt nhưng cần kinh nghiệm với các khái niệm nâng cao và thiết kế hệ thống.',
            'metadata': {"keywords": ["React", "Node.js", "Junior", "Full Stack"]},
            'created_at': now - timedelta(days=13),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'cv_file_path': '/uploads/cvs/hoang_van_e_cv.pdf',
            'extracted_text': 'Hoàng Văn E - Mid-level Backend Engineer. 4 năm kinh nghiệm với Python, Django, PostgreSQL và AWS. Chuyên về xây dựng REST APIs có khả năng mở rộng và microservices. Có kinh nghiệm với Docker, Kubernetes và CI/CD pipelines.',
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
            'suggested_difficulty': 'MEDIUM',
            'summary': 'Mid-level backend engineer với 4 năm kinh nghiệm Python và Django. Mạnh về thiết kế API và tối ưu hóa database. Sẵn sàng cho các cuộc thảo luận về thiết kế hệ thống và kiến trúc.',
            'metadata': {"keywords": ["Python", "Backend", "Django", "API"]},
            'created_at': now - timedelta(days=11),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'cv_file_path': '/uploads/cvs/vu_thi_f_cv.pdf',
            'extracted_text': 'Vũ Thị F - Senior Full Stack Developer. 8 năm kinh nghiệm với JavaScript, TypeScript, React, Node.js và công nghệ cloud. Đã dẫn dắt nhiều team và thiết kế các ứng dụng quy mô lớn. Chuyên gia về thiết kế hệ thống và tối ưu hóa hiệu suất.',
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
            'suggested_difficulty': 'HARD',
            'summary': 'Senior full-stack developer với 8 năm kinh nghiệm. Chuyên gia về hệ sinh thái JavaScript và thiết kế hệ thống. Có kinh nghiệm lãnh đạo mạnh và khả năng thiết kế các giải pháp có khả năng mở rộng.',
            'metadata': {"keywords": ["Senior", "Full Stack", "System Design", "JavaScript"]},
            'created_at': now - timedelta(days=9),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440004'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'cv_file_path': '/uploads/cvs/do_van_g_cv.pdf',
            'extracted_text': 'Đỗ Văn G - Frontend Specialist. 3 năm kinh nghiệm với React, Vue.js, TypeScript và công cụ frontend hiện đại. Tập trung mạnh vào UI/UX với chuyên môn về quản lý state, tối ưu hóa hiệu suất và thiết kế responsive.',
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
            'suggested_difficulty': 'MEDIUM',
            'summary': 'Frontend specialist với 3 năm kinh nghiệm React và Vue.js. Tập trung mạnh vào UI/UX và hiệu suất frontend. Hiểu biết tốt về các pattern frontend hiện đại.',
            'metadata': {"keywords": ["Frontend", "React", "Vue.js", "UI/UX"]},
            'created_at': now - timedelta(days=7),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440005'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),
            'cv_file_path': '/uploads/cvs/bui_thi_h_cv.pdf',
            'extracted_text': 'Bùi Thị H - DevOps Engineer. 5 năm kinh nghiệm với CI/CD, Kubernetes, Docker, AWS, Terraform và tự động hóa hạ tầng. Chuyên gia về kiến trúc cloud và giải pháp monitoring.',
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
            'suggested_difficulty': 'HARD',
            'summary': 'DevOps engineer với 5 năm kinh nghiệm về hạ tầng cloud và tự động hóa. Chuyên gia về Kubernetes, Docker và AWS. Mạnh về infrastructure as code và CI/CD pipelines.',
            'metadata': {"keywords": ["DevOps", "Kubernetes", "AWS", "Infrastructure"]},
            'created_at': now - timedelta(days=5),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440006'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440006'),
            'cv_file_path': '/uploads/cvs/ngo_van_i_cv.pdf',
            'extracted_text': 'Ngô Văn I - Full Stack Developer. 2.5 năm kinh nghiệm với Java, Spring Boot, React và PostgreSQL. Có kinh nghiệm xây dựng ứng dụng doanh nghiệp và RESTful services.',
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
            'suggested_difficulty': 'EASY',
            'summary': 'Full-stack developer với 2.5 năm kinh nghiệm Java và Spring Boot. Nền tảng tốt về phát triển doanh nghiệp. Vẫn đang học các khái niệm nâng cao.',
            'metadata': {"keywords": ["Java", "Spring Boot", "Full Stack"]},
            'created_at': now - timedelta(days=3),
        },
        {
            'id': uuid.UUID('860e8400-e29b-41d4-a716-446655440007'),
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),
            'cv_file_path': '/uploads/cvs/dang_thi_k_cv.pdf',
            'extracted_text': 'Đặng Thị K - Backend Engineer. 6 năm kinh nghiệm với Python, FastAPI, PostgreSQL, Redis và hệ thống phân tán. Chuyên gia về xây dựng API hiệu suất cao và kiến trúc microservices.',
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
            'suggested_difficulty': 'HARD',
            'summary': 'Senior backend engineer với 6 năm kinh nghiệm Python. Chuyên gia về FastAPI và xây dựng microservices có khả năng mở rộng. Mạnh về tối ưu hóa database và chiến lược caching.',
            'metadata': {"keywords": ["Python", "Backend", "Microservices", "FastAPI"]},
            'created_at': now - timedelta(days=1),
        },
    ])

    print("[OK] Seeded 10 CV analyses (Vietnamese)")


def downgrade() -> None:
    """Downgrade - delete seeded CV analyses."""
    conn = op.get_bind()

    print("[INFO] Removing seeded CV analyses...")
    conn.execute(sa.text("DELETE FROM cv_analyses"))

    print("[OK] CV analyses removed")

