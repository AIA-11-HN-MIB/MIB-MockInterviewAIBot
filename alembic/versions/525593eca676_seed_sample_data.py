"""seed_sample_data

Revision ID: 525593eca676
Revises: a4047ce5a909
Create Date: 2025-10-31 23:46:29.587545

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
revision: str = '525593eca676'
down_revision: Union[str, Sequence[str], None] = 'a4047ce5a909'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed sample data for development and testing."""

    # Get connection
    conn = op.get_bind()
    metadata = MetaData()
    now = datetime.utcnow()

    # Define table schemas for bulk insert
    candidates_table = Table(
        'candidates', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('name', String),
        Column('email', String),
        Column('cv_file_path', String),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

    questions_table = Table(
        'questions', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('text', Text),
        Column('question_type', String),
        Column('difficulty', String),
        Column('skills', ARRAY(String)),
        Column('tags', ARRAY(String)),
        Column('reference_answer', Text),
        Column('evaluation_criteria', Text),
        Column('version', Integer),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

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

    interviews_table = Table(
        'interviews', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('candidate_id', UUID(as_uuid=True)),
        Column('status', String),
        Column('cv_analysis_id', UUID(as_uuid=True)),
        Column('question_ids', ARRAY(UUID(as_uuid=True))),
        Column('answer_ids', ARRAY(UUID(as_uuid=True))),
        Column('current_question_index', Integer),
        Column('started_at', DateTime),
        Column('completed_at', DateTime),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

    answers_table = Table(
        'answers', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('interview_id', UUID(as_uuid=True)),
        Column('question_id', UUID(as_uuid=True)),
        Column('candidate_id', UUID(as_uuid=True)),
        Column('text', Text),
        Column('is_voice', Boolean),
        Column('audio_file_path', String),
        Column('duration_seconds', Float),
        Column('evaluation', JSONB),
        Column('metadata', JSONB),
        Column('created_at', DateTime),
        Column('evaluated_at', DateTime),
    )

    # =============================================
    # SEED DATA
    # =============================================

    # 1. Candidates
    op.bulk_insert(candidates_table, [
        {
            'id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'cv_file_path': '/uploads/cvs/john_doe_cv.pdf',
            'created_at': now - timedelta(days=30),
            'updated_at': now - timedelta(days=30),
        },
        {
            'id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'cv_file_path': '/uploads/cvs/jane_smith_cv.pdf',
            'created_at': now - timedelta(days=25),
            'updated_at': now - timedelta(days=25),
        },
        {
            'id': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'name': 'Bob Johnson',
            'email': 'bob.johnson@example.com',
            'cv_file_path': '/uploads/cvs/bob_johnson_cv.pdf',
            'created_at': now - timedelta(days=20),
            'updated_at': now - timedelta(days=20),
        },
    ])

    # 2. Questions
    op.bulk_insert(questions_table, [
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),
            'text': 'What is the difference between var, let, and const in JavaScript?',
            'question_type': 'TECHNICAL',
            'difficulty': 'EASY',
            'skills': ['JavaScript', 'ES6', 'Variables'],
            'tags': ['javascript', 'basics', 'es6'],
            'reference_answer': 'var is function-scoped and can be redeclared, let is block-scoped and cannot be redeclared, const is block-scoped and cannot be reassigned.',
            'evaluation_criteria': 'Check understanding of scope, hoisting, and immutability concepts',
            'version': 1,
            'created_at': now - timedelta(days=60),
            'updated_at': now - timedelta(days=60),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440002'),
            'text': 'Explain what REST API is and its main HTTP methods.',
            'question_type': 'TECHNICAL',
            'difficulty': 'EASY',
            'skills': ['API', 'REST', 'HTTP'],
            'tags': ['api', 'rest', 'http'],
            'reference_answer': 'REST is an architectural style for APIs using standard HTTP methods: GET (retrieve), POST (create), PUT/PATCH (update), DELETE (remove).',
            'evaluation_criteria': 'Evaluate understanding of RESTful principles and HTTP verbs',
            'version': 1,
            'created_at': now - timedelta(days=60),
            'updated_at': now - timedelta(days=60),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),
            'text': 'How does async/await work in JavaScript? Compare it with Promises.',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['JavaScript', 'Async', 'Promises'],
            'tags': ['javascript', 'async', 'promises'],
            'reference_answer': 'async/await is syntactic sugar over Promises, making asynchronous code look synchronous.',
            'evaluation_criteria': 'Assess understanding of asynchronous programming',
            'version': 1,
            'created_at': now - timedelta(days=55),
            'updated_at': now - timedelta(days=55),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440004'),
            'text': 'What is a closure in Python? Provide an example.',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['Python', 'Closures', 'Functional Programming'],
            'tags': ['python', 'closures', 'functional'],
            'reference_answer': 'A closure is a nested function that remembers values from its enclosing scope even after the outer function has finished execution.',
            'evaluation_criteria': 'Check understanding of lexical scoping and closure mechanics',
            'version': 1,
            'created_at': now - timedelta(days=58),
            'updated_at': now - timedelta(days=58),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440005'),
            'text': 'Describe the difference between list comprehension and generator expressions in Python.',
            'question_type': 'TECHNICAL',
            'difficulty': 'EASY',
            'skills': ['Python', 'List Comprehension', 'Generators'],
            'tags': ['python', 'list-comprehension', 'generators'],
            'reference_answer': 'List comprehensions create lists in memory, while generator expressions create iterators that yield values on demand, saving memory.',
            'evaluation_criteria': 'Evaluate understanding of memory efficiency and iteration patterns',
            'version': 1,
            'created_at': now - timedelta(days=57),
            'updated_at': now - timedelta(days=57),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440006'),
            'text': 'What is the difference between SQL JOIN types: INNER, LEFT, RIGHT, and FULL OUTER?',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['SQL', 'Database', 'JOIN'],
            'tags': ['sql', 'database', 'join'],
            'reference_answer': 'INNER returns matching rows, LEFT returns all left table rows, RIGHT returns all right table rows, FULL OUTER returns all rows from both tables.',
            'evaluation_criteria': 'Assess knowledge of SQL JOIN operations and their use cases',
            'version': 1,
            'created_at': now - timedelta(days=56),
            'updated_at': now - timedelta(days=56),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),
            'text': 'Explain what is a React Hook and name three common hooks you have used.',
            'question_type': 'TECHNICAL',
            'difficulty': 'EASY',
            'skills': ['React', 'Hooks', 'Frontend'],
            'tags': ['react', 'hooks', 'frontend'],
            'reference_answer': 'React Hooks are functions that let you use state and lifecycle features in functional components. Common hooks: useState, useEffect, useContext.',
            'evaluation_criteria': 'Evaluate understanding of React Hooks and their practical application',
            'version': 1,
            'created_at': now - timedelta(days=54),
            'updated_at': now - timedelta(days=54),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440008'),
            'text': 'How would you design a system to handle 1 million requests per second?',
            'question_type': 'TECHNICAL',
            'difficulty': 'HARD',
            'skills': ['System Design', 'Scalability', 'Architecture'],
            'tags': ['system-design', 'scalability', 'architecture'],
            'reference_answer': 'Use load balancers, horizontal scaling, caching layers, database sharding, CDN, message queues, and microservices architecture.',
            'evaluation_criteria': 'Assess system design thinking, scalability patterns, and trade-off considerations',
            'version': 1,
            'created_at': now - timedelta(days=52),
            'updated_at': now - timedelta(days=52),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440009'),
            'text': 'What is the difference between process and thread? When would you use each?',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['Operating Systems', 'Concurrency', 'Threading'],
            'tags': ['operating-systems', 'concurrency', 'threading'],
            'reference_answer': 'Processes have separate memory spaces, threads share memory. Use processes for isolation, threads for shared state and performance.',
            'evaluation_criteria': 'Evaluate understanding of concurrency models and their trade-offs',
            'version': 1,
            'created_at': now - timedelta(days=51),
            'updated_at': now - timedelta(days=51),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),
            'text': 'Explain the SOLID principles in object-oriented programming.',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['OOP', 'Design Patterns', 'SOLID'],
            'tags': ['oop', 'design-patterns', 'solid'],
            'reference_answer': 'SOLID: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. These principles guide good OOP design.',
            'evaluation_criteria': 'Check understanding of OOP principles and their practical application',
            'version': 1,
            'created_at': now - timedelta(days=50),
            'updated_at': now - timedelta(days=50),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440011'),
            'text': 'What is Docker and how does it differ from a virtual machine?',
            'question_type': 'TECHNICAL',
            'difficulty': 'EASY',
            'skills': ['Docker', 'Containers', 'DevOps'],
            'tags': ['docker', 'containers', 'devops'],
            'reference_answer': 'Docker uses containerization to package applications with dependencies. VMs virtualize hardware, containers virtualize the OS, making containers lighter and faster.',
            'evaluation_criteria': 'Assess understanding of containerization vs virtualization',
            'version': 1,
            'created_at': now - timedelta(days=49),
            'updated_at': now - timedelta(days=49),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440012'),
            'text': 'Explain the difference between time complexity and space complexity with examples.',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['Algorithms', 'Big O', 'Complexity Analysis'],
            'tags': ['algorithms', 'big-o', 'complexity'],
            'reference_answer': 'Time complexity measures execution time growth, space complexity measures memory usage growth. Both use Big O notation (O(n), O(log n), etc.).',
            'evaluation_criteria': 'Evaluate algorithmic thinking and complexity analysis skills',
            'version': 1,
            'created_at': now - timedelta(days=48),
            'updated_at': now - timedelta(days=48),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440013'),
            'text': 'What is the difference between REST and GraphQL? When would you choose one over the other?',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['API', 'REST', 'GraphQL'],
            'tags': ['api', 'rest', 'graphql'],
            'reference_answer': 'REST uses multiple endpoints with fixed responses, GraphQL uses a single endpoint with flexible queries. Choose GraphQL for complex queries, REST for simplicity.',
            'evaluation_criteria': 'Assess understanding of API design patterns and trade-offs',
            'version': 1,
            'created_at': now - timedelta(days=47),
            'updated_at': now - timedelta(days=47),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440014'),
            'text': 'Describe how Node.js handles asynchronous operations. What is the event loop?',
            'question_type': 'TECHNICAL',
            'difficulty': 'HARD',
            'skills': ['Node.js', 'Event Loop', 'Asynchronous'],
            'tags': ['nodejs', 'event-loop', 'async'],
            'reference_answer': 'Node.js uses an event loop with a single-threaded event-driven architecture. The event loop processes callbacks, timers, and I/O operations in phases.',
            'evaluation_criteria': 'Evaluate deep understanding of Node.js internals and asynchronous execution',
            'version': 1,
            'created_at': now - timedelta(days=46),
            'updated_at': now - timedelta(days=46),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440015'),
            'text': 'What is unit testing and why is it important? Name a testing framework you have used.',
            'question_type': 'TECHNICAL',
            'difficulty': 'EASY',
            'skills': ['Testing', 'Unit Testing', 'QA'],
            'tags': ['testing', 'unit-testing', 'qa'],
            'reference_answer': 'Unit testing tests individual components in isolation. It ensures code quality, catches bugs early, and enables refactoring confidence. Examples: Jest, pytest, JUnit.',
            'evaluation_criteria': 'Check understanding of testing principles and practical experience',
            'version': 1,
            'created_at': now - timedelta(days=45),
            'updated_at': now - timedelta(days=45),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440016'),
            'text': 'Tell me about a time when you had to work under pressure to meet a deadline.',
            'question_type': 'BEHAVIORAL',
            'difficulty': 'MEDIUM',
            'skills': ['Time Management', 'Stress Management', 'Communication'],
            'tags': ['behavioral', 'deadlines', 'pressure'],
            'reference_answer': 'Candidate should describe a specific situation, explain the challenge, detail actions taken, and reflect on outcomes using STAR method.',
            'evaluation_criteria': 'Assess ability to handle pressure, prioritize tasks, and communicate effectively under stress',
            'version': 1,
            'created_at': now - timedelta(days=44),
            'updated_at': now - timedelta(days=44),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440017'),
            'text': 'Describe a situation where you had to learn a new technology quickly for a project.',
            'question_type': 'BEHAVIORAL',
            'difficulty': 'EASY',
            'skills': ['Learning', 'Adaptability', 'Problem Solving'],
            'tags': ['behavioral', 'learning', 'adaptability'],
            'reference_answer': 'Candidate should demonstrate self-directed learning, resource utilization, and ability to apply new knowledge effectively.',
            'evaluation_criteria': 'Evaluate learning agility, initiative, and ability to adapt to new technologies',
            'version': 1,
            'created_at': now - timedelta(days=43),
            'updated_at': now - timedelta(days=43),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440018'),
            'text': 'Give an example of a time when you disagreed with a team member. How did you resolve it?',
            'question_type': 'BEHAVIORAL',
            'difficulty': 'MEDIUM',
            'skills': ['Conflict Resolution', 'Teamwork', 'Communication'],
            'tags': ['behavioral', 'conflict', 'teamwork'],
            'reference_answer': 'Candidate should show emotional intelligence, active listening, and collaborative problem-solving approach.',
            'evaluation_criteria': 'Assess conflict resolution skills and ability to work collaboratively',
            'version': 1,
            'created_at': now - timedelta(days=42),
            'updated_at': now - timedelta(days=42),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440019'),
            'text': 'What is your biggest weakness as a developer, and how are you working to improve it?',
            'question_type': 'BEHAVIORAL',
            'difficulty': 'MEDIUM',
            'skills': ['Self-Awareness', 'Growth Mindset', 'Honesty'],
            'tags': ['behavioral', 'self-reflection', 'growth'],
            'reference_answer': 'Candidate should be honest, show self-awareness, and demonstrate proactive steps toward improvement.',
            'evaluation_criteria': 'Evaluate self-awareness, growth mindset, and honesty',
            'version': 1,
            'created_at': now - timedelta(days=41),
            'updated_at': now - timedelta(days=41),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440020'),
            'text': 'If you discovered a critical bug in production right before a major release, what would you do?',
            'question_type': 'SITUATIONAL',
            'difficulty': 'MEDIUM',
            'skills': ['Problem Solving', 'Risk Management', 'Decision Making'],
            'tags': ['situational', 'bug', 'production'],
            'reference_answer': 'Assess severity, inform stakeholders, evaluate options (hotfix vs delay), prioritize user impact, and document the decision process.',
            'evaluation_criteria': 'Check ability to make decisions under pressure while considering business and technical implications',
            'version': 1,
            'created_at': now - timedelta(days=40),
            'updated_at': now - timedelta(days=40),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440021'),
            'text': 'You have limited time to complete a feature. How do you decide what to prioritize?',
            'question_type': 'SITUATIONAL',
            'difficulty': 'EASY',
            'skills': ['Prioritization', 'Time Management', 'Analytical Thinking'],
            'tags': ['situational', 'prioritization', 'time-management'],
            'reference_answer': 'Evaluate business value, user impact, dependencies, and risks. Focus on MVP first, then iterate.',
            'evaluation_criteria': 'Assess prioritization skills and ability to make trade-off decisions',
            'version': 1,
            'created_at': now - timedelta(days=39),
            'updated_at': now - timedelta(days=39),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440022'),
            'text': 'How would you handle a situation where a client requests a feature that conflicts with your technical recommendations?',
            'question_type': 'SITUATIONAL',
            'difficulty': 'HARD',
            'skills': ['Client Communication', 'Technical Leadership', 'Negotiation'],
            'tags': ['situational', 'client-management', 'leadership'],
            'reference_answer': 'Listen to client needs, explain technical concerns clearly, propose alternatives, and find a collaborative solution that balances requirements.',
            'evaluation_criteria': 'Evaluate communication skills, technical credibility, and ability to navigate stakeholder relationships',
            'version': 1,
            'created_at': now - timedelta(days=38),
            'updated_at': now - timedelta(days=38),
        },
        {
            'id': uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),
            'text': 'Explain what is garbage collection in Java and how it works.',
            'question_type': 'TECHNICAL',
            'difficulty': 'MEDIUM',
            'skills': ['Java', 'Memory Management', 'JVM'],
            'tags': ['java', 'memory-management', 'jvm'],
            'reference_answer': 'Garbage collection automatically reclaims memory by identifying and removing unused objects. JVM uses generational GC with Eden, Survivor, and Old Generation spaces.',
            'evaluation_criteria': 'Assess understanding of memory management and JVM internals',
            'version': 1,
            'created_at': now - timedelta(days=37),
            'updated_at': now - timedelta(days=37),
        },
    ])

    # 3. CV Analyses
    op.bulk_insert(cv_analyses_table, [
        {
            'id': uuid.UUID('750e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'cv_file_path': '/uploads/cvs/john_doe_cv.pdf',
            'extracted_text': 'John Doe - Senior Full Stack Developer. 5+ years experience in React, Node.js, PostgreSQL.',
            'skills': [
                {"skill": "React", "proficiency": "expert", "years": 5},
                {"skill": "Node.js", "proficiency": "expert", "years": 5},
            ],
            'work_experience_years': 5.5,
            'education_level': 'Bachelor',
            'suggested_topics': ['Microservices', 'React Hooks', 'Database Design'],
            'suggested_difficulty': 'MEDIUM',
            'summary': 'Experienced full-stack developer with strong React and Node.js skills.',
            'metadata': {"keywords": ["React", "Node.js"]},
            'created_at': now - timedelta(days=29),
        },
        {
            'id': uuid.UUID('750e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'cv_file_path': '/uploads/cvs/jane_smith_cv.pdf',
            'extracted_text': 'Jane Smith - Backend Engineer. 3+ years experience in Python, Java, SQL, REST APIs, and microservices architecture.',
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
            'summary': 'Backend engineer with strong Python and Java skills, experienced in building scalable APIs.',
            'metadata': {"keywords": ["Python", "Java", "Backend", "API"]},
            'created_at': now - timedelta(days=24),
        },
        {
            'id': uuid.UUID('750e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'cv_file_path': '/uploads/cvs/bob_johnson_cv.pdf',
            'extracted_text': 'Bob Johnson - Full Stack Developer. 7+ years experience in JavaScript, React, Node.js, Docker, and cloud technologies.',
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
            'summary': 'Senior full-stack developer with extensive JavaScript ecosystem expertise and system design experience.',
            'metadata': {"keywords": ["JavaScript", "React", "Node.js", "System Design"]},
            'created_at': now - timedelta(days=19),
        },
    ])

    # 4. Interviews
    op.bulk_insert(interviews_table, [
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'status': 'COMPLETED',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440001'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),
            ],
            'answer_ids': [
                uuid.UUID('950e8400-e29b-41d4-a716-446655440001'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440002'),
            ],
            'current_question_index': 2,
            'started_at': now - timedelta(days=28),
            'completed_at': now - timedelta(days=28) + timedelta(minutes=30),
            'created_at': now - timedelta(days=28),
            'updated_at': now - timedelta(days=28) + timedelta(minutes=30),
        },
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440002'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'status': 'COMPLETED',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440004'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440006'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440016'),
            ],
            'answer_ids': [
                uuid.UUID('950e8400-e29b-41d4-a716-446655440003'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440004'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440005'),
                uuid.UUID('950e8400-e29b-41d4-a716-446655440006'),
            ],
            'current_question_index': 4,
            'started_at': now - timedelta(days=23),
            'completed_at': now - timedelta(days=23) + timedelta(minutes=45),
            'created_at': now - timedelta(days=23),
            'updated_at': now - timedelta(days=23) + timedelta(minutes=45),
        },
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'status': 'IN_PROGRESS',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440003'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440008'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440014'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440018'),
            ],
            'answer_ids': [
                uuid.UUID('950e8400-e29b-41d4-a716-446655440007'),
            ],
            'current_question_index': 1,
            'started_at': now - timedelta(days=18),
            'completed_at': None,
            'created_at': now - timedelta(days=18),
            'updated_at': now - timedelta(days=18) + timedelta(minutes=20),
        },
        {
            'id': uuid.UUID('850e8400-e29b-41d4-a716-446655440004'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'status': 'READY',
            'cv_analysis_id': uuid.UUID('750e8400-e29b-41d4-a716-446655440002'),
            'question_ids': [
                uuid.UUID('650e8400-e29b-41d4-a716-446655440005'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440009'),
                uuid.UUID('650e8400-e29b-41d4-a716-446655440013'),
            ],
            'answer_ids': [],
            'current_question_index': 0,
            'started_at': None,
            'completed_at': None,
            'created_at': now - timedelta(days=15),
            'updated_at': now - timedelta(days=15),
        },
    ])

    # 5. Answers
    op.bulk_insert(answers_table, [
        {
            'id': uuid.UUID('950e8400-e29b-41d4-a716-446655440001'),
            'interview_id': uuid.UUID('850e8400-e29b-41d4-a716-446655440001'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'text': 'var is function-scoped, let and const are block-scoped. const cannot be reassigned.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': None,
            'evaluation': {
                "score": 85,
                "feedback": "Good understanding of scope and hoisting.",
                "strengths": ["Clear explanation"],
            },
            'metadata': {"response_time_seconds": 45},
            'created_at': now - timedelta(days=28),
            'evaluated_at': now - timedelta(days=28) + timedelta(minutes=5),
        },
        {
            'id': uuid.UUID('950e8400-e29b-41d4-a716-446655440002'),
            'interview_id': uuid.UUID('850e8400-e29b-41d4-a716-446655440001'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'text': 'async/await makes async code more readable. It is built on top of Promises.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': None,
            'evaluation': {
                "score": 80,
                "feedback": "Solid understanding.",
            },
            'metadata': {"response_time_seconds": 60},
            'created_at': now - timedelta(days=28) + timedelta(minutes=15),
            'evaluated_at': now - timedelta(days=28) + timedelta(minutes=20),
        },
        {
            'id': uuid.UUID('950e8400-e29b-41d4-a716-446655440003'),
            'interview_id': uuid.UUID('850e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440004'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'text': 'A closure in Python is a nested function that captures variables from its enclosing scope. For example, a counter function can maintain state between calls.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': None,
            'evaluation': {
                "score": 88,
                "feedback": "Good understanding of closures with practical example.",
                "strengths": ["Clear explanation", "Provided example"],
            },
            'metadata': {"response_time_seconds": 50},
            'created_at': now - timedelta(days=23) + timedelta(minutes=5),
            'evaluated_at': now - timedelta(days=23) + timedelta(minutes=8),
        },
        {
            'id': uuid.UUID('950e8400-e29b-41d4-a716-446655440004'),
            'interview_id': uuid.UUID('850e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440006'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'text': 'INNER JOIN returns matching rows from both tables. LEFT JOIN returns all rows from left table. RIGHT JOIN returns all rows from right table. FULL OUTER JOIN returns all rows from both tables.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': None,
            'evaluation': {
                "score": 92,
                "feedback": "Excellent understanding of SQL JOIN operations.",
                "strengths": ["Complete coverage of all JOIN types", "Clear explanation"],
            },
            'metadata': {"response_time_seconds": 55},
            'created_at': now - timedelta(days=23) + timedelta(minutes=15),
            'evaluated_at': now - timedelta(days=23) + timedelta(minutes=18),
        },
        {
            'id': uuid.UUID('950e8400-e29b-41d4-a716-446655440005'),
            'interview_id': uuid.UUID('850e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'text': 'SOLID principles are: Single Responsibility - one reason to change, Open/Closed - open for extension, Liskov Substitution - derived classes must be substitutable, Interface Segregation - no forced implementation, Dependency Inversion - depend on abstractions.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': None,
            'evaluation': {
                "score": 85,
                "feedback": "Solid grasp of SOLID principles with clear explanations.",
                "strengths": ["Covered all principles", "Practical understanding"],
            },
            'metadata': {"response_time_seconds": 75},
            'created_at': now - timedelta(days=23) + timedelta(minutes=25),
            'evaluated_at': now - timedelta(days=23) + timedelta(minutes=30),
        },
        {
            'id': uuid.UUID('950e8400-e29b-41d4-a716-446655440006'),
            'interview_id': uuid.UUID('850e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440016'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'text': 'Last month I had to deliver a feature under tight deadline. I broke it down into smaller tasks, communicated blockers early, and worked extra hours when needed. We delivered on time by prioritizing the MVP.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': None,
            'evaluation': {
                "score": 78,
                "feedback": "Good example showing problem-solving under pressure.",
                "strengths": ["Clear situation", "Practical approach"],
                "areas_for_improvement": ["Could elaborate more on communication strategies"],
            },
            'metadata': {"response_time_seconds": 90},
            'created_at': now - timedelta(days=23) + timedelta(minutes=35),
            'evaluated_at': now - timedelta(days=23) + timedelta(minutes=40),
        },
        {
            'id': uuid.UUID('950e8400-e29b-41d4-a716-446655440007'),
            'interview_id': uuid.UUID('850e8400-e29b-41d4-a716-446655440003'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440008'),
            'candidate_id': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'text': 'To handle 1M requests per second, I would use horizontal scaling with load balancers, implement caching at multiple layers (CDN, Redis), use database replication and sharding, implement message queues for async processing, and design with microservices for independent scaling.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': None,
            'evaluation': {
                "score": 90,
                "feedback": "Excellent system design thinking covering key scalability patterns.",
                "strengths": ["Comprehensive approach", "Mentioned key technologies", "Thought about multiple layers"],
            },
            'metadata': {"response_time_seconds": 120},
            'created_at': now - timedelta(days=18) + timedelta(minutes=5),
            'evaluated_at': now - timedelta(days=18) + timedelta(minutes=12),
        },
    ])

    print("[OK] Seeded 3 candidates")
    print("[OK] Seeded 23 questions")
    print("[OK] Seeded 3 CV analyses")
    print("[OK] Seeded 4 interviews")
    print("[OK] Seeded 7 answers")


def downgrade() -> None:
    """Remove seeded data."""
    conn = op.get_bind()

    # Delete in reverse order of dependencies
    # Answers
    conn.execute(sa.text("""
        DELETE FROM answers WHERE id IN (
            '950e8400-e29b-41d4-a716-446655440001',
            '950e8400-e29b-41d4-a716-446655440002',
            '950e8400-e29b-41d4-a716-446655440003',
            '950e8400-e29b-41d4-a716-446655440004',
            '950e8400-e29b-41d4-a716-446655440005',
            '950e8400-e29b-41d4-a716-446655440006',
            '950e8400-e29b-41d4-a716-446655440007'
        )
    """))

    # Interviews
    conn.execute(sa.text("""
        DELETE FROM interviews WHERE id IN (
            '850e8400-e29b-41d4-a716-446655440001',
            '850e8400-e29b-41d4-a716-446655440002',
            '850e8400-e29b-41d4-a716-446655440003',
            '850e8400-e29b-41d4-a716-446655440004'
        )
    """))

    # CV Analyses
    conn.execute(sa.text("""
        DELETE FROM cv_analyses WHERE id IN (
            '750e8400-e29b-41d4-a716-446655440001',
            '750e8400-e29b-41d4-a716-446655440002',
            '750e8400-e29b-41d4-a716-446655440003'
        )
    """))

    # Questions
    conn.execute(sa.text("""
        DELETE FROM questions WHERE id IN (
            '650e8400-e29b-41d4-a716-446655440001',
            '650e8400-e29b-41d4-a716-446655440002',
            '650e8400-e29b-41d4-a716-446655440003',
            '650e8400-e29b-41d4-a716-446655440004',
            '650e8400-e29b-41d4-a716-446655440005',
            '650e8400-e29b-41d4-a716-446655440006',
            '650e8400-e29b-41d4-a716-446655440007',
            '650e8400-e29b-41d4-a716-446655440008',
            '650e8400-e29b-41d4-a716-446655440009',
            '650e8400-e29b-41d4-a716-446655440010',
            '650e8400-e29b-41d4-a716-446655440011',
            '650e8400-e29b-41d4-a716-446655440012',
            '650e8400-e29b-41d4-a716-446655440013',
            '650e8400-e29b-41d4-a716-446655440014',
            '650e8400-e29b-41d4-a716-446655440015',
            '650e8400-e29b-41d4-a716-446655440016',
            '650e8400-e29b-41d4-a716-446655440017',
            '650e8400-e29b-41d4-a716-446655440018',
            '650e8400-e29b-41d4-a716-446655440019',
            '650e8400-e29b-41d4-a716-446655440020',
            '650e8400-e29b-41d4-a716-446655440021',
            '650e8400-e29b-41d4-a716-446655440022',
            '650e8400-e29b-41d4-a716-446655440023'
        )
    """))

    # Candidates
    conn.execute(sa.text("""
        DELETE FROM candidates WHERE id IN (
            '550e8400-e29b-41d4-a716-446655440001',
            '550e8400-e29b-41d4-a716-446655440002',
            '550e8400-e29b-41d4-a716-446655440003'
        )
    """))

    print("[OK] Removed seed data")
