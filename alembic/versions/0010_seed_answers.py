"""seed answers

Revision ID: 0010
Revises: 0009
Create Date: 2025-12-11 10:00:00

Creates realistic answers with evaluations for completed and in-progress interviews.
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime


# revision identifiers, used by Alembic.
revision: str = '0010'
down_revision: Union[str, Sequence[str], None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed realistic answers with evaluations for interviews."""

    metadata = MetaData()
    now = datetime.utcnow()

    # Define table schema for bulk insert
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
        Column('embedding', ARRAY(Float)),
        Column('metadata', JSONB),
        Column('similarity_score', Float),
        Column('gaps', JSONB),
        Column('created_at', DateTime),
        Column('evaluated_at', DateTime),
    )

    # Insert realistic answers
    # Interview 1: Alice Chen (Junior) - Completed - 4 answers
    # Interview 2: Michael Rodriguez (Mid-level) - Completed - 5 answers
    # Interview 3: Sarah Williams (Senior) - Completed - 5 answers
    # Interview 4: David Kim (Frontend) - Completed - 4 answers
    # Interview 5: Emily Thompson (DevOps) - In-progress - 2 answers
    # Interview 6: James Anderson (Full stack) - In-progress - 1 answer
    # Interview 7: Lisa Martinez (Backend) - In-progress - 3 answers

    op.bulk_insert(answers_table, [
        # ============================================
        # Interview 1: Alice Chen (Junior) - Completed
        # ============================================
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440001'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440001'),  # var/let/const
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),  # Alice Chen
            'text': 'var is function-scoped and can be redeclared. let and const are block-scoped. const cannot be reassigned after declaration. I use let for variables that change and const for constants.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 45.0,
            'evaluation': {
                'score': 75.0,
                'semantic_similarity': 0.72,
                'completeness': 0.70,
                'relevance': 0.80,
                'sentiment': 'confident',
                'reasoning': 'Good basic understanding of scope differences. Could mention hoisting behavior.',
                'strengths': ['Clear explanation of scope', 'Practical usage mentioned'],
                'weaknesses': ['Missing hoisting details', 'Could explain temporal dead zone'],
                'improvement_suggestions': ['Explain hoisting behavior', 'Mention TDZ for let/const']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 45, 'word_count': 32},
            'similarity_score': 0.72,
            'gaps': {
                'concepts': ['hoisting', 'temporal_dead_zone'],
                'confirmed': True,
                'keywords': ['hoisting', 'TDZ'],
                'entities': []
            },
            'created_at': now - timedelta(days=12, hours=2, minutes=5),
            'evaluated_at': now - timedelta(days=12, hours=2, minutes=6),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440002'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),  # React Hooks
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'text': 'React Hooks let you use state and lifecycle in functional components. I use useState for state, useEffect for side effects, and useContext for sharing data. They make code cleaner than class components.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 60.0,
            'evaluation': {
                'score': 78.0,
                'semantic_similarity': 0.75,
                'completeness': 0.75,
                'relevance': 0.85,
                'sentiment': 'confident',
                'reasoning': 'Solid understanding of common hooks. Could mention more hooks like useMemo, useCallback.',
                'strengths': ['Correct hook examples', 'Practical understanding'],
                'weaknesses': ['Limited to basic hooks', 'Could mention optimization hooks'],
                'improvement_suggestions': ['Learn useMemo and useCallback', 'Understand custom hooks']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 60, 'word_count': 38},
            'similarity_score': 0.75,
            'gaps': {
                'concepts': ['useMemo', 'useCallback', 'custom_hooks'],
                'confirmed': False,
                'keywords': ['optimization', 'performance'],
                'entities': []
            },
            'created_at': now - timedelta(days=12, hours=2, minutes=15),
            'evaluated_at': now - timedelta(days=12, hours=2, minutes=16),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440003'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),  # Testing types
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'text': 'Unit tests test individual functions in isolation. Integration tests test how components work together. E2E tests test the whole application flow. I use Jest for unit tests and Cypress for E2E.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 55.0,
            'evaluation': {
                'score': 82.0,
                'semantic_similarity': 0.80,
                'completeness': 0.80,
                'relevance': 0.90,
                'sentiment': 'confident',
                'reasoning': 'Good understanding of testing pyramid. Practical tool knowledge.',
                'strengths': ['Clear distinction between test types', 'Tool knowledge'],
                'weaknesses': ['Could mention mocking strategies', 'Test coverage concepts'],
                'improvement_suggestions': ['Learn mocking techniques', 'Understand test coverage metrics']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 55, 'word_count': 35},
            'similarity_score': 0.80,
            'gaps': {
                'concepts': ['mocking', 'test_coverage'],
                'confirmed': False,
                'keywords': ['mocking', 'coverage'],
                'entities': []
            },
            'created_at': now - timedelta(days=12, hours=2, minutes=25),
            'evaluated_at': now - timedelta(days=12, hours=2, minutes=26),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440004'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440001'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440017'),  # Learning new tech
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
            'text': 'Last year I had to learn TypeScript for a project. I started with the official docs, built small projects, and asked my team for help. I was productive within two weeks. The type system helped catch bugs early.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 90.0,
            'evaluation': {
                'score': 85.0,
                'semantic_similarity': 0.82,
                'completeness': 0.85,
                'relevance': 0.90,
                'sentiment': 'positive',
                'reasoning': 'Good STAR method usage. Shows initiative and practical learning approach.',
                'strengths': ['Specific example', 'Clear learning process', 'Measurable outcome'],
                'weaknesses': ['Could mention challenges faced', 'More reflection on lessons learned'],
                'improvement_suggestions': ['Include challenges and how overcome', 'Reflect on key learnings']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 90, 'word_count': 48},
            'similarity_score': 0.82,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=12, hours=2, minutes=30),
            'evaluated_at': now - timedelta(days=12, hours=2, minutes=32),
        },
        # ============================================
        # Interview 2: Michael Rodriguez (Mid-level) - Completed
        # ============================================
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440005'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440001'),  # Dependency injection
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),  # Michael Rodriguez
            'text': 'Dependency injection is a design pattern where dependencies are provided to a class rather than created internally. This improves testability because you can inject mocks, reduces coupling by depending on abstractions, and makes code more maintainable. I use constructor injection primarily, which ensures dependencies are available when the object is created. This follows the Dependency Inversion Principle from SOLID.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 75.0,
            'evaluation': {
                'score': 88.0,
                'semantic_similarity': 0.85,
                'completeness': 0.88,
                'relevance': 0.92,
                'sentiment': 'confident',
                'reasoning': 'Excellent understanding of DI principles and practical application. Links to SOLID principles.',
                'strengths': ['Comprehensive explanation', 'Practical experience', 'SOLID connection'],
                'weaknesses': ['Could mention service locator anti-pattern', 'Container frameworks'],
                'improvement_suggestions': ['Learn DI container frameworks', 'Understand anti-patterns to avoid']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 75, 'word_count': 68},
            'similarity_score': 0.85,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=10, hours=3, minutes=5),
            'evaluated_at': now - timedelta(days=10, hours=3, minutes=7),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440006'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440003'),  # Hash tables
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'text': 'Hash tables use a hash function to map keys to array indices. When inserting, the hash function computes an index and stores the value there. Collisions happen when different keys hash to the same index. I know two main strategies: chaining uses linked lists at each bucket, and open addressing finds the next available slot using linear or quadratic probing. Chaining is simpler but uses more memory, while open addressing is more memory-efficient but can degrade with high load factors.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 90.0,
            'evaluation': {
                'score': 90.0,
                'semantic_similarity': 0.88,
                'completeness': 0.90,
                'relevance': 0.95,
                'sentiment': 'confident',
                'reasoning': 'Strong understanding of hash table internals and collision resolution. Good trade-off analysis.',
                'strengths': ['Complete explanation', 'Trade-off understanding', 'Practical knowledge'],
                'weaknesses': ['Could mention double hashing', 'Load factor specifics'],
                'improvement_suggestions': ['Learn double hashing technique', 'Understand optimal load factors']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 90, 'word_count': 85},
            'similarity_score': 0.88,
            'gaps': {
                'concepts': ['double_hashing', 'optimal_load_factor'],
                'confirmed': False,
                'keywords': ['double hashing', 'load factor'],
                'entities': []
            },
            'created_at': now - timedelta(days=10, hours=3, minutes=15),
            'evaluated_at': now - timedelta(days=10, hours=3, minutes=17),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440007'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440004'),  # Auth/Authz
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'text': 'Authentication verifies who the user is, authorization determines what they can do. I implement auth using JWT tokens stored in httpOnly cookies for security. For authorization, I use role-based access control (RBAC) with middleware that checks user roles before allowing access to protected routes. I also hash passwords with bcrypt and use OAuth2 for third-party login.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 95.0,
            'evaluation': {
                'score': 87.0,
                'semantic_similarity': 0.84,
                'completeness': 0.85,
                'relevance': 0.90,
                'sentiment': 'confident',
                'reasoning': 'Good practical implementation knowledge. Clear distinction between auth and authz.',
                'strengths': ['Clear auth/authz distinction', 'Practical implementation', 'Security awareness'],
                'weaknesses': ['Could mention session management', 'Token refresh strategies'],
                'improvement_suggestions': ['Learn token refresh patterns', 'Understand session vs token trade-offs']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 95, 'word_count': 72},
            'similarity_score': 0.84,
            'gaps': {
                'concepts': ['token_refresh', 'session_management'],
                'confirmed': False,
                'keywords': ['refresh token', 'session'],
                'entities': []
            },
            'created_at': now - timedelta(days=10, hours=3, minutes=25),
            'evaluated_at': now - timedelta(days=10, hours=3, minutes=27),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440008'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440010'),  # SOLID principles
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'text': 'SOLID principles guide object-oriented design. Single Responsibility means a class should have one reason to change. Open/Closed means open for extension, closed for modification. Liskov Substitution means derived classes must be substitutable for base classes. Interface Segregation means clients shouldn\'t depend on interfaces they don\'t use. Dependency Inversion means depend on abstractions, not concretions. I apply these in my code reviews and refactoring.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 100.0,
            'evaluation': {
                'score': 92.0,
                'semantic_similarity': 0.90,
                'completeness': 0.92,
                'relevance': 0.95,
                'sentiment': 'confident',
                'reasoning': 'Excellent comprehensive understanding of all SOLID principles. Shows practical application.',
                'strengths': ['Complete coverage', 'Practical application', 'Clear explanations'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 100, 'word_count': 88},
            'similarity_score': 0.90,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=10, hours=3, minutes=35),
            'evaluated_at': now - timedelta(days=10, hours=3, minutes=37),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440009'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440002'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440014'),  # Prioritization
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440002'),
            'text': 'When prioritizing with limited time, I consider business value, user impact, dependencies, and risks. I focus on MVP features first, then iterate. I communicate with stakeholders to understand priorities and break work into smaller tasks. I also consider technical debt and maintenance needs.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 80.0,
            'evaluation': {
                'score': 85.0,
                'semantic_similarity': 0.82,
                'completeness': 0.83,
                'relevance': 0.88,
                'sentiment': 'confident',
                'reasoning': 'Good prioritization framework. Shows stakeholder awareness and practical approach.',
                'strengths': ['Clear framework', 'Stakeholder communication', 'MVP approach'],
                'weaknesses': ['Could mention urgency vs importance', 'More specific examples'],
                'improvement_suggestions': ['Learn Eisenhower matrix', 'Practice with real scenarios']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 80, 'word_count': 58},
            'similarity_score': 0.82,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=10, hours=3, minutes=40),
            'evaluated_at': now - timedelta(days=10, hours=3, minutes=42),
        },
        # ============================================
        # Interview 3: Sarah Williams (Senior) - Completed
        # ============================================
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440010'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440003'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices vs Monolith
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),  # Sarah Williams
            'text': 'Monolithic architecture bundles all components into a single deployable unit, which simplifies initial development, testing, and deployment. However, it becomes harder to scale and maintain at large scale. Microservices split functionality into independent, loosely coupled services that can be developed, deployed, and scaled independently. This offers better fault isolation, technology diversity, and team autonomy, but adds complexity in service communication, distributed tracing, and eventual consistency. I choose monoliths for small teams, simple domains, or when starting a project. I choose microservices when dealing with large teams, complex domains requiring different scaling patterns, or when services have distinct lifecycles. The key is not to over-engineer early.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 120.0,
            'evaluation': {
                'score': 95.0,
                'semantic_similarity': 0.93,
                'completeness': 0.95,
                'relevance': 0.98,
                'sentiment': 'very_confident',
                'reasoning': 'Exceptional understanding of architectural patterns with deep trade-off analysis. Shows senior-level thinking.',
                'strengths': ['Comprehensive trade-off analysis', 'Practical decision criteria', 'Senior-level insights'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 120, 'word_count': 142},
            'similarity_score': 0.93,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=8, hours=1, minutes=5),
            'evaluated_at': now - timedelta(days=8, hours=1, minutes=8),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440011'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440003'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),  # CAP theorem
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'text': 'CAP theorem states that in a distributed system, you can only guarantee two out of three: Consistency (all nodes see same data), Availability (system remains operational), and Partition tolerance (system continues despite network failures). Since partition tolerance is unavoidable in distributed systems, you choose between CP (consistency and partition tolerance) or AP (availability and partition tolerance). CP systems like traditional databases prioritize consistency, while AP systems like DynamoDB prioritize availability. I design systems based on use case: financial transactions need CP, while social media feeds can use AP with eventual consistency.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 110.0,
            'evaluation': {
                'score': 94.0,
                'semantic_similarity': 0.91,
                'completeness': 0.93,
                'relevance': 0.96,
                'sentiment': 'very_confident',
                'reasoning': 'Excellent understanding of CAP theorem with practical application examples. Shows deep distributed systems knowledge.',
                'strengths': ['Complete CAP explanation', 'Practical examples', 'Use case understanding'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 110, 'word_count': 118},
            'similarity_score': 0.91,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=8, hours=1, minutes=20),
            'evaluated_at': now - timedelta(days=8, hours=1, minutes=23),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440012'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440003'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),  # Event loop
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'text': 'The event loop is Node.js\'s core mechanism for handling asynchronous operations. It\'s a single-threaded loop that continuously checks the call stack and callback queue. When the call stack is empty, it moves callbacks from the queue to the stack. The event loop has phases: timers (setTimeout/setInterval), pending callbacks, idle/prepare, poll (I/O), check (setImmediate), and close callbacks. This allows Node.js to handle thousands of concurrent connections efficiently despite being single-threaded. I use worker threads for CPU-intensive tasks to avoid blocking the event loop.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 105.0,
            'evaluation': {
                'score': 93.0,
                'semantic_similarity': 0.90,
                'completeness': 0.92,
                'relevance': 0.95,
                'sentiment': 'very_confident',
                'reasoning': 'Deep understanding of event loop internals with practical optimization knowledge.',
                'strengths': ['Complete phase explanation', 'Practical optimization', 'Worker threads knowledge'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 105, 'word_count': 108},
            'similarity_score': 0.90,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=8, hours=1, minutes=35),
            'evaluated_at': now - timedelta(days=8, hours=1, minutes=38),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440013'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440003'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),  # Caching strategy
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'text': 'I implement multi-layer caching: browser cache for static assets, CDN for global distribution, Redis for application-level caching with TTL, and database query caching. I use cache-aside pattern where the application checks cache first, then database. For invalidation, I use TTL-based expiration and event-driven invalidation when data changes. I also implement cache warming for frequently accessed data and monitor cache hit rates. For distributed systems, I use consistent hashing to distribute cache across nodes.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 115.0,
            'evaluation': {
                'score': 96.0,
                'semantic_similarity': 0.94,
                'completeness': 0.96,
                'relevance': 0.98,
                'sentiment': 'very_confident',
                'reasoning': 'Exceptional comprehensive caching strategy covering all layers and patterns. Shows production experience.',
                'strengths': ['Multi-layer approach', 'Pattern knowledge', 'Monitoring awareness', 'Distributed systems'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 115, 'word_count': 98},
            'similarity_score': 0.94,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=8, hours=1, minutes=45),
            'evaluated_at': now - timedelta(days=8, hours=1, minutes=48),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440014'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440003'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440008'),  # System design 1M req/s
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440003'),
            'text': 'To handle 1M requests per second, I\'d design a horizontally scalable architecture. Load balancers distribute traffic across multiple application servers. I\'d use caching layers (Redis cluster) for frequently accessed data, CDN for static content, and database sharding with read replicas. Message queues (Kafka) handle async processing. I\'d implement rate limiting, circuit breakers, and auto-scaling. Database would use connection pooling and query optimization. I\'d monitor with distributed tracing and metrics. The key is identifying bottlenecks and scaling each layer independently.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 130.0,
            'evaluation': {
                'score': 97.0,
                'semantic_similarity': 0.95,
                'completeness': 0.97,
                'relevance': 0.99,
                'sentiment': 'very_confident',
                'reasoning': 'Outstanding system design thinking covering all critical aspects. Shows expert-level architecture knowledge.',
                'strengths': ['Comprehensive architecture', 'All key components', 'Monitoring and resilience', 'Bottleneck awareness'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 130, 'word_count': 112},
            'similarity_score': 0.95,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=8, hours=1, minutes=50),
            'evaluated_at': now - timedelta(days=8, hours=1, minutes=53),
        },
        # ============================================
        # Interview 4: David Kim (Frontend) - Completed
        # ============================================
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440015'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440007'),  # React Hooks
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),  # David Kim
            'text': 'React Hooks are functions that enable functional components to use state and lifecycle features. I use useState for component state, useEffect for side effects like API calls and subscriptions, useContext for sharing data without prop drilling, useMemo for expensive computations, and useCallback to memoize functions. Custom hooks let me extract reusable logic. Hooks follow rules: only call at top level and only in React functions. They make code more reusable and easier to test than class components.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 95.0,
            'evaluation': {
                'score': 91.0,
                'semantic_similarity': 0.88,
                'completeness': 0.90,
                'relevance': 0.94,
                'sentiment': 'confident',
                'reasoning': 'Excellent comprehensive understanding of React Hooks with optimization hooks and best practices.',
                'strengths': ['Complete hook coverage', 'Optimization hooks', 'Rules of hooks', 'Custom hooks'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 95, 'word_count': 96},
            'similarity_score': 0.88,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=6, hours=2, minutes=30, seconds=5),
            'evaluated_at': now - timedelta(days=6, hours=2, minutes=30, seconds=7),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440016'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),  # Event loop
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'text': 'The event loop handles asynchronous operations in JavaScript. It continuously checks the call stack and callback queue. When the stack is empty, it moves callbacks to the stack. The loop has phases: timers, pending callbacks, poll, check, and close. This allows JavaScript to be non-blocking despite being single-threaded. I use async/await for cleaner async code and avoid blocking the event loop with heavy computations.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 70.0,
            'evaluation': {
                'score': 86.0,
                'semantic_similarity': 0.83,
                'completeness': 0.84,
                'relevance': 0.90,
                'sentiment': 'confident',
                'reasoning': 'Good understanding of event loop basics. Could go deeper into phases and microtasks.',
                'strengths': ['Core concept clear', 'Practical usage', 'Non-blocking understanding'],
                'weaknesses': ['Could detail microtask queue', 'More phase specifics'],
                'improvement_suggestions': ['Learn microtask vs macrotask', 'Study event loop phases in depth']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 70, 'word_count': 68},
            'similarity_score': 0.83,
            'gaps': {
                'concepts': ['microtask_queue', 'macrotask'],
                'confirmed': False,
                'keywords': ['microtask', 'macrotask'],
                'entities': []
            },
            'created_at': now - timedelta(days=6, hours=2, minutes=45),
            'evaluated_at': now - timedelta(days=6, hours=2, minutes=46),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440017'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),  # Testing types
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'text': 'Unit tests test individual functions or components in isolation, typically with mocks. Integration tests verify how multiple components work together. E2E tests simulate real user workflows. I use Jest and React Testing Library for unit and integration tests, and Cypress for E2E. I aim for high unit test coverage, fewer integration tests, and critical path E2E tests. This follows the testing pyramid.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 75.0,
            'evaluation': {
                'score': 89.0,
                'semantic_similarity': 0.86,
                'completeness': 0.87,
                'relevance': 0.92,
                'sentiment': 'confident',
                'reasoning': 'Strong testing knowledge with practical tool usage and pyramid understanding.',
                'strengths': ['Clear test type distinctions', 'Tool knowledge', 'Testing pyramid', 'Coverage strategy'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 75, 'word_count': 71},
            'similarity_score': 0.86,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=6, hours=3, minutes=0),
            'evaluated_at': now - timedelta(days=6, hours=3, minutes=2),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440018'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440004'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440003'),  # Async/await
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440004'),
            'text': 'async/await is syntactic sugar over Promises that makes asynchronous code look synchronous. An async function returns a Promise. await pauses execution until the Promise resolves. I use try/catch for error handling. It\'s cleaner than promise chains and easier to read. Under the hood, it still uses Promises and the event loop. I use it for API calls, file operations, and any async operations.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 65.0,
            'evaluation': {
                'score': 88.0,
                'semantic_similarity': 0.85,
                'completeness': 0.86,
                'relevance': 0.92,
                'sentiment': 'confident',
                'reasoning': 'Good understanding of async/await with practical usage. Could mention parallel execution.',
                'strengths': ['Clear explanation', 'Error handling', 'Practical usage'],
                'weaknesses': ['Could mention Promise.all', 'Parallel execution patterns'],
                'improvement_suggestions': ['Learn Promise.all for parallel execution', 'Understand async iteration']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 65, 'word_count': 66},
            'similarity_score': 0.85,
            'gaps': {
                'concepts': ['Promise.all', 'parallel_execution'],
                'confirmed': False,
                'keywords': ['Promise.all', 'parallel'],
                'entities': []
            },
            'created_at': now - timedelta(days=6, hours=3, minutes=10),
            'evaluated_at': now - timedelta(days=6, hours=3, minutes=12),
        },
        # ============================================
        # Interview 5: Emily Thompson (DevOps) - In-progress
        # ============================================
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440019'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),  # Emily Thompson
            'text': 'Microservices split applications into independent services that can be deployed separately. Each service has its own database and communicates via APIs. This allows teams to work independently and scale services individually. Monoliths are simpler but harder to scale. I\'ve worked with Kubernetes to orchestrate microservices and use service meshes for communication.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 85.0,
            'evaluation': {
                'score': 87.0,
                'semantic_similarity': 0.84,
                'completeness': 0.85,
                'relevance': 0.90,
                'sentiment': 'confident',
                'reasoning': 'Good understanding with practical Kubernetes experience. Could mention more trade-offs.',
                'strengths': ['Clear explanation', 'Kubernetes experience', 'Practical knowledge'],
                'weaknesses': ['Could detail more trade-offs', 'Service mesh specifics'],
                'improvement_suggestions': ['Learn service mesh patterns', 'Understand distributed tracing']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 85, 'word_count': 58},
            'similarity_score': 0.84,
            'gaps': {
                'concepts': ['service_mesh', 'distributed_tracing'],
                'confirmed': False,
                'keywords': ['service mesh', 'tracing'],
                'entities': []
            },
            'created_at': now - timedelta(days=4, hours=1, minutes=5),
            'evaluated_at': now - timedelta(days=4, hours=1, minutes=7),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440020'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440005'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440018'),  # Horizontal vs Vertical scaling
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440005'),
            'text': 'Horizontal scaling adds more servers or instances, while vertical scaling increases resources on existing servers. Horizontal is better for cloud because you can add instances on demand. Vertical has limits based on hardware. I prefer horizontal for microservices because it provides better fault tolerance and can scale individual services. I use auto-scaling groups in AWS to handle traffic spikes.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 90.0,
            'evaluation': {
                'score': 89.0,
                'semantic_similarity': 0.86,
                'completeness': 0.88,
                'relevance': 0.93,
                'sentiment': 'confident',
                'reasoning': 'Excellent understanding with practical cloud experience. Good fault tolerance awareness.',
                'strengths': ['Clear distinction', 'Cloud experience', 'Fault tolerance', 'Practical application'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 90, 'word_count': 72},
            'similarity_score': 0.86,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=4, hours=1, minutes=20),
            'evaluated_at': now - timedelta(days=4, hours=1, minutes=22),
        },
        # ============================================
        # Interview 6: James Anderson (Full stack) - In-progress
        # ============================================
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440021'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440006'),
            'question_id': uuid.UUID('650e8400-e29b-41d4-a716-446655440023'),  # Garbage collection Java
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440006'),  # James Anderson
            'text': 'Garbage collection automatically frees memory by removing unused objects. Java uses generational GC with young generation (Eden, Survivor spaces) and old generation. Objects start in Eden, survive collections move to Survivor, and long-lived objects go to old generation. The GC pauses application execution. I tune GC settings based on application needs and monitor GC logs.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 80.0,
            'evaluation': {
                'score': 83.0,
                'semantic_similarity': 0.80,
                'completeness': 0.81,
                'relevance': 0.88,
                'sentiment': 'confident',
                'reasoning': 'Good understanding of Java GC with generational model. Could mention GC algorithms.',
                'strengths': ['Generational model clear', 'Practical tuning', 'Monitoring awareness'],
                'weaknesses': ['Could mention GC algorithms', 'More on pause times'],
                'improvement_suggestions': ['Learn different GC algorithms', 'Understand GC tuning strategies']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 80, 'word_count': 70},
            'similarity_score': 0.80,
            'gaps': {
                'concepts': ['gc_algorithms', 'pause_time_optimization'],
                'confirmed': True,
                'keywords': ['GC algorithms', 'pause times'],
                'entities': []
            },
            'created_at': now - timedelta(days=2, hours=2, minutes=5),
            'evaluated_at': now - timedelta(days=2, hours=2, minutes=7),
        },
        # ============================================
        # Interview 7: Lisa Martinez (Backend) - In-progress
        # ============================================
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440022'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),  # CAP theorem
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),  # Lisa Martinez
            'text': 'CAP theorem says in distributed systems you can only have two of three: Consistency, Availability, Partition tolerance. Since partitions are inevitable, you choose CP or AP. CP systems prioritize consistency, AP systems prioritize availability. I design based on use case: financial data needs CP, social feeds can use AP with eventual consistency.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 70.0,
            'evaluation': {
                'score': 88.0,
                'semantic_similarity': 0.85,
                'completeness': 0.86,
                'relevance': 0.91,
                'sentiment': 'confident',
                'reasoning': 'Good understanding of CAP theorem with practical application. Could mention more examples.',
                'strengths': ['Clear CAP explanation', 'Practical examples', 'Use case understanding'],
                'weaknesses': ['Could mention more database examples', 'Consistency models'],
                'improvement_suggestions': ['Learn consistency models', 'Study real-world CAP implementations']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 70, 'word_count': 58},
            'similarity_score': 0.85,
            'gaps': {
                'concepts': ['consistency_models', 'real_world_implementations'],
                'confirmed': False,
                'keywords': ['consistency models'],
                'entities': []
            },
            'created_at': now - timedelta(days=1, hours=3, minutes=5),
            'evaluated_at': now - timedelta(days=1, hours=3, minutes=7),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440023'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),  # Python GC
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),
            'text': 'Python uses reference counting and generational garbage collection. Each object has a reference count. When it reaches zero, memory is freed. The cyclic garbage collector handles circular references. The GC has three generations. I can control it with gc module and disable it for performance-critical code.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 65.0,
            'evaluation': {
                'score': 85.0,
                'semantic_similarity': 0.82,
                'completeness': 0.83,
                'relevance': 0.89,
                'sentiment': 'confident',
                'reasoning': 'Good understanding of Python GC mechanisms. Could mention more details on generations.',
                'strengths': ['Reference counting clear', 'Cyclic GC mentioned', 'Practical control'],
                'weaknesses': ['Could detail generation specifics', 'More on performance tuning'],
                'improvement_suggestions': ['Learn GC generation details', 'Understand GC tuning for performance']
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 65, 'word_count': 52},
            'similarity_score': 0.82,
            'gaps': {
                'concepts': ['generation_details', 'gc_tuning'],
                'confirmed': False,
                'keywords': ['generations', 'tuning'],
                'entities': []
            },
            'created_at': now - timedelta(days=1, hours=3, minutes=20),
            'evaluated_at': now - timedelta(days=1, hours=3, minutes=22),
        },
        {
            'id': uuid.UUID('a60e8400-e29b-41d4-a716-446655440024'),
            'interview_id': uuid.UUID('960e8400-e29b-41d4-a716-446655440007'),
            'question_id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),  # Microservices
            'candidate_id': uuid.UUID('660e8400-e29b-41d4-a716-446655440007'),
            'text': 'Microservices architecture splits applications into independent services. Each service has its own database and team. Benefits include independent deployment, technology diversity, and fault isolation. Challenges include service communication, distributed transactions, and monitoring complexity. I use API gateways, service discovery, and distributed tracing. I prefer starting with monolith and extracting services when needed.',
            'is_voice': False,
            'audio_file_path': None,
            'duration_seconds': 95.0,
            'evaluation': {
                'score': 90.0,
                'semantic_similarity': 0.87,
                'completeness': 0.89,
                'relevance': 0.93,
                'sentiment': 'confident',
                'reasoning': 'Excellent understanding with practical patterns and pragmatic approach to adoption.',
                'strengths': ['Complete explanation', 'Practical patterns', 'Pragmatic approach', 'Challenges awareness'],
                'weaknesses': [],
                'improvement_suggestions': []
            },
            'embedding': None,
            'metadata': {'response_time_seconds': 95, 'word_count': 76},
            'similarity_score': 0.87,
            'gaps': {
                'concepts': [],
                'confirmed': False,
                'keywords': [],
                'entities': []
            },
            'created_at': now - timedelta(days=1, hours=3, minutes=35),
            'evaluated_at': now - timedelta(days=1, hours=3, minutes=37),
        },
    ])

    print("[OK] Seeded 24 answers (18 completed, 6 in-progress)")
    print("[OK] Answers include evaluations, similarity scores, and gaps for adaptive follow-ups")


def downgrade() -> None:
    """Remove seeded answers."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM answers WHERE id IN (
            'a60e8400-e29b-41d4-a716-446655440001',
            'a60e8400-e29b-41d4-a716-446655440002',
            'a60e8400-e29b-41d4-a716-446655440003',
            'a60e8400-e29b-41d4-a716-446655440004',
            'a60e8400-e29b-41d4-a716-446655440005',
            'a60e8400-e29b-41d4-a716-446655440006',
            'a60e8400-e29b-41d4-a716-446655440007',
            'a60e8400-e29b-41d4-a716-446655440008',
            'a60e8400-e29b-41d4-a716-446655440009',
            'a60e8400-e29b-41d4-a716-446655440010',
            'a60e8400-e29b-41d4-a716-446655440011',
            'a60e8400-e29b-41d4-a716-446655440012',
            'a60e8400-e29b-41d4-a716-446655440013',
            'a60e8400-e29b-41d4-a716-446655440014',
            'a60e8400-e29b-41d4-a716-446655440015',
            'a60e8400-e29b-41d4-a716-446655440016',
            'a60e8400-e29b-41d4-a716-446655440017',
            'a60e8400-e29b-41d4-a716-446655440018',
            'a60e8400-e29b-41d4-a716-446655440019',
            'a60e8400-e29b-41d4-a716-446655440020',
            'a60e8400-e29b-41d4-a716-446655440021',
            'a60e8400-e29b-41d4-a716-446655440022',
            'a60e8400-e29b-41d4-a716-446655440023',
            'a60e8400-e29b-41d4-a716-446655440024'
        )
    """))

    print("[OK] Removed seeded answers")

