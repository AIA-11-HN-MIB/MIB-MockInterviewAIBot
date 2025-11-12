"""seed additional questions

Revision ID: 0007
Revises: 0006
Create Date: 2025-12-11 10:00:00

Adds 18 new realistic questions with ideal_answer and rationale for interview simulation.
"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import String, Text, Integer, DateTime


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed additional questions with ideal answers and rationale."""

    metadata = MetaData()
    now = datetime.utcnow()

    # Define table schema for bulk insert
    questions_table = Table(
        'questions', metadata,
        Column('id', UUID(as_uuid=True)),
        Column('text', Text),
        Column('question_type', String),
        Column('difficulty', String),
        Column('skills', ARRAY(String)),
        Column('tags', ARRAY(String)),
        Column('evaluation_criteria', Text),
        Column('ideal_answer', Text),
        Column('rationale', Text),
        Column('version', Integer),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )

    # Insert 18 new realistic questions
    op.bulk_insert(questions_table, [
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440001'),
            'text': 'Explain the concept of dependency injection and its benefits in software design.',
            'question_type': 'technical',
            'difficulty': 'medium',
            'skills': ['Design Patterns', 'OOP', 'Software Architecture'],
            'tags': ['dependency-injection', 'design-patterns', 'architecture'],
            'evaluation_criteria': 'Assess understanding of DI principles, inversion of control, and practical benefits like testability and loose coupling.',
            'ideal_answer': 'Dependency injection is a design pattern where objects receive their dependencies from external sources rather than creating them internally. Benefits include: improved testability (easy to mock dependencies), loose coupling (components depend on abstractions), better separation of concerns, and easier maintenance. Common implementations include constructor injection, setter injection, and interface injection. This pattern follows the Dependency Inversion Principle from SOLID principles.',
            'rationale': 'Tests understanding of fundamental design patterns and their practical application in building maintainable software systems.',
            'version': 1,
            'created_at': now - timedelta(days=40),
            'updated_at': now - timedelta(days=40),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440002'),
            'text': 'What is the difference between microservices and monolithic architecture? When would you choose each?',
            'question_type': 'technical',
            'difficulty': 'hard',
            'skills': ['System Design', 'Architecture', 'Microservices'],
            'tags': ['microservices', 'architecture', 'system-design'],
            'evaluation_criteria': 'Evaluate understanding of architectural patterns, trade-offs, and decision-making criteria.',
            'ideal_answer': 'Monolithic architecture has all components in a single deployable unit, while microservices split functionality into independent, loosely coupled services. Monoliths are simpler to develop, test, and deploy initially, but harder to scale and maintain at large scale. Microservices offer independent scaling, technology diversity, and fault isolation, but add complexity in deployment, monitoring, and inter-service communication. Choose monolith for small teams, simple applications, or when starting. Choose microservices for large teams, complex domains, or when you need independent scaling of components.',
            'rationale': 'Assesses system design thinking and ability to make architectural decisions based on context and requirements.',
            'version': 1,
            'created_at': now - timedelta(days=38),
            'updated_at': now - timedelta(days=38),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440003'),
            'text': 'How does a hash table work internally? Explain collision resolution strategies.',
            'question_type': 'technical',
            'difficulty': 'medium',
            'skills': ['Data Structures', 'Algorithms', 'Hash Tables'],
            'tags': ['data-structures', 'hash-tables', 'algorithms'],
            'evaluation_criteria': 'Check understanding of hash table internals, hash functions, and collision handling mechanisms.',
            'ideal_answer': 'A hash table uses a hash function to map keys to array indices. When inserting, the hash function computes an index, and the value is stored at that position. Collisions occur when different keys hash to the same index. Resolution strategies include: 1) Chaining - store multiple items in a linked list at each bucket, 2) Open addressing - find next available slot using linear probing, quadratic probing, or double hashing. Chaining is simpler but uses extra memory. Open addressing is more memory-efficient but can degrade performance with high load factors.',
            'rationale': 'Tests fundamental data structure knowledge essential for understanding performance characteristics and algorithm design.',
            'version': 1,
            'created_at': now - timedelta(days=36),
            'updated_at': now - timedelta(days=36),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440004'),
            'text': 'Describe how you would implement authentication and authorization in a web application.',
            'question_type': 'technical',
            'difficulty': 'medium',
            'skills': ['Security', 'Authentication', 'Authorization', 'Web Development'],
            'tags': ['security', 'authentication', 'authorization', 'web'],
            'evaluation_criteria': 'Assess knowledge of security best practices, token-based authentication, and authorization patterns.',
            'ideal_answer': 'Authentication verifies user identity (who you are), while authorization determines permissions (what you can do). Implementation: 1) User registration/login with password hashing (bcrypt/argon2), 2) JWT tokens or session-based auth, 3) Store tokens securely (httpOnly cookies or localStorage with CSRF protection), 4) Implement role-based access control (RBAC) or attribute-based (ABAC), 5) Use middleware to protect routes, 6) Implement refresh tokens for security, 7) Add rate limiting and account lockout. Best practices: never store passwords in plain text, use HTTPS, implement proper session management, and follow OWASP guidelines.',
            'rationale': 'Evaluates critical security knowledge essential for building secure applications.',
            'version': 1,
            'created_at': now - timedelta(days=34),
            'updated_at': now - timedelta(days=34),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440005'),
            'text': 'What is the CAP theorem? Explain each component and provide examples.',
            'question_type': 'technical',
            'difficulty': 'hard',
            'skills': ['Distributed Systems', 'Database', 'System Design'],
            'tags': ['cap-theorem', 'distributed-systems', 'database'],
            'evaluation_criteria': 'Evaluate understanding of distributed system trade-offs and real-world system characteristics.',
            'ideal_answer': 'CAP theorem states that in a distributed system, you can only guarantee two out of three: Consistency (all nodes see same data simultaneously), Availability (system remains operational), Partition tolerance (system continues despite network failures). Examples: CP systems (like MongoDB, HBase) prioritize consistency and partition tolerance, sacrificing availability during partitions. AP systems (like Cassandra, DynamoDB) prioritize availability and partition tolerance, allowing eventual consistency. CA systems (traditional RDBMS) prioritize consistency and availability but don\'t handle network partitions well. In practice, partition tolerance is unavoidable in distributed systems, so the choice is between C and A.',
            'rationale': 'Tests understanding of fundamental distributed systems principles and their practical implications.',
            'version': 1,
            'created_at': now - timedelta(days=32),
            'updated_at': now - timedelta(days=32),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440006'),
            'text': 'Explain the difference between SQL and NoSQL databases. When would you use each?',
            'question_type': 'technical',
            'difficulty': 'medium',
            'skills': ['Database', 'SQL', 'NoSQL', 'Data Modeling'],
            'tags': ['database', 'sql', 'nosql', 'data-modeling'],
            'evaluation_criteria': 'Assess understanding of database types, their characteristics, and appropriate use cases.',
            'ideal_answer': 'SQL databases are relational, use structured schemas, support ACID transactions, and use SQL for queries. They excel at complex queries, data integrity, and structured data. Examples: PostgreSQL, MySQL. NoSQL databases are non-relational, schema-flexible, often prioritize performance and scalability, and use various data models (document, key-value, column, graph). They excel at horizontal scaling, unstructured data, and high write throughput. Examples: MongoDB, Redis, Cassandra. Use SQL for: complex queries, transactions, structured data, data integrity requirements. Use NoSQL for: high scalability needs, flexible schemas, large volumes of unstructured data, rapid development.',
            'rationale': 'Evaluates database selection knowledge crucial for making appropriate technology choices.',
            'version': 1,
            'created_at': now - timedelta(days=30),
            'updated_at': now - timedelta(days=30),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440007'),
            'text': 'What is the difference between unit testing, integration testing, and end-to-end testing?',
            'question_type': 'technical',
            'difficulty': 'easy',
            'skills': ['Testing', 'QA', 'Software Engineering'],
            'tags': ['testing', 'unit-testing', 'integration-testing', 'e2e'],
            'evaluation_criteria': 'Check understanding of testing pyramid and different testing levels.',
            'ideal_answer': 'Unit testing tests individual components in isolation (functions, classes) with mocked dependencies. Fast, numerous, catch bugs early. Integration testing verifies interactions between components (database, APIs, services). Slower, fewer tests, catch integration issues. End-to-end testing tests complete user workflows through the entire system. Slowest, fewest tests, catch system-level issues. The testing pyramid suggests many unit tests, fewer integration tests, and minimal E2E tests. Each level serves different purposes and catches different types of bugs.',
            'rationale': 'Assesses testing knowledge essential for building reliable software.',
            'version': 1,
            'created_at': now - timedelta(days=28),
            'updated_at': now - timedelta(days=28),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440008'),
            'text': 'How does garbage collection work in Python? Explain the reference counting and generational GC.',
            'question_type': 'technical',
            'difficulty': 'medium',
            'skills': ['Python', 'Memory Management', 'Garbage Collection'],
            'tags': ['python', 'memory-management', 'garbage-collection'],
            'evaluation_criteria': 'Evaluate understanding of Python internals and memory management.',
            'ideal_answer': 'Python uses a combination of reference counting and generational garbage collection. Reference counting immediately deallocates objects when reference count reaches zero, but cannot handle circular references. Generational GC (gc module) handles circular references by tracking objects in generations (0, 1, 2). New objects start in generation 0. Objects that survive GC move to older generations. GC runs more frequently on younger generations. This approach optimizes for the fact that most objects die young. The gc.collect() can manually trigger collection, but Python handles it automatically.',
            'rationale': 'Tests understanding of language internals important for performance optimization and debugging.',
            'version': 1,
            'created_at': now - timedelta(days=26),
            'updated_at': now - timedelta(days=26),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440009'),
            'text': 'What is the event loop in JavaScript? How does it handle asynchronous operations?',
            'question_type': 'technical',
            'difficulty': 'hard',
            'skills': ['JavaScript', 'Event Loop', 'Asynchronous Programming'],
            'tags': ['javascript', 'event-loop', 'async', 'nodejs'],
            'evaluation_criteria': 'Assess deep understanding of JavaScript runtime and asynchronous execution model.',
            'ideal_answer': 'The event loop is JavaScript\'s mechanism for handling asynchronous operations. It continuously checks the call stack and task queues. When the call stack is empty, it moves tasks from queues to the stack. Queues include: Callback Queue (for setTimeout, DOM events), Microtask Queue (for Promises, queueMicrotask), and Job Queue (for async/await). Microtasks have higher priority than regular callbacks. The event loop processes all microtasks before moving to the next callback. This single-threaded model allows non-blocking I/O operations. Understanding this is crucial for debugging async code and avoiding common pitfalls.',
            'rationale': 'Evaluates critical JavaScript knowledge for understanding async behavior and performance.',
            'version': 1,
            'created_at': now - timedelta(days=24),
            'updated_at': now - timedelta(days=24),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440010'),
            'text': 'Explain the concept of database indexing. How does it improve query performance?',
            'question_type': 'technical',
            'difficulty': 'medium',
            'skills': ['Database', 'SQL', 'Performance Optimization'],
            'tags': ['database', 'indexing', 'performance', 'sql'],
            'evaluation_criteria': 'Check understanding of indexing mechanisms and their impact on database performance.',
            'ideal_answer': 'Database indexing creates data structures (like B-trees) that allow faster data retrieval. Instead of scanning entire tables (full table scan), indexes provide direct access paths to data. Benefits: faster SELECT queries, faster JOINs, faster WHERE clause filtering, faster ORDER BY operations. Trade-offs: indexes consume storage space, slow down INSERT/UPDATE/DELETE operations (indexes must be maintained), and require maintenance. Common index types: B-tree (default, good for range queries), Hash (exact matches), Bitmap (low cardinality). Best practices: index frequently queried columns, foreign keys, columns in WHERE clauses, but avoid over-indexing.',
            'rationale': 'Tests database optimization knowledge essential for building performant applications.',
            'version': 1,
            'created_at': now - timedelta(days=22),
            'updated_at': now - timedelta(days=22),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440011'),
            'text': 'Tell me about a time when you had to learn a new technology or framework quickly for a project. How did you approach it?',
            'question_type': 'behavioral',
            'difficulty': 'easy',
            'skills': ['Learning', 'Adaptability', 'Problem Solving'],
            'tags': ['behavioral', 'learning', 'adaptability'],
            'evaluation_criteria': 'Assess learning agility, resource utilization, and ability to apply new knowledge effectively.',
            'ideal_answer': 'Use STAR method: Situation - describe the project context and technology needed. Task - explain what needed to be learned and why. Action - detail learning approach: official documentation, tutorials, hands-on practice, code examples, community resources, pair programming. Result - describe successful implementation, time taken, and lessons learned. Show self-directed learning, systematic approach, and ability to apply knowledge quickly.',
            'rationale': 'Evaluates learning agility and adaptability, crucial traits for software developers in a rapidly evolving field.',
            'version': 1,
            'created_at': now - timedelta(days=20),
            'updated_at': now - timedelta(days=20),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440012'),
            'text': 'Describe a situation where you had to work with a difficult team member. How did you handle it?',
            'question_type': 'behavioral',
            'difficulty': 'medium',
            'skills': ['Communication', 'Teamwork', 'Conflict Resolution'],
            'tags': ['behavioral', 'teamwork', 'conflict'],
            'evaluation_criteria': 'Evaluate emotional intelligence, communication skills, and collaborative problem-solving approach.',
            'ideal_answer': 'Use STAR method. Situation: describe the conflict objectively. Task: explain the challenge and impact on team/project. Action: detail approach - active listening, understanding their perspective, clear communication, finding common ground, involving manager if needed, focusing on solutions not blame. Result: resolution achieved, relationship improved, project success. Show empathy, professionalism, and focus on team success.',
            'rationale': 'Assesses interpersonal skills and ability to navigate workplace conflicts constructively.',
            'version': 1,
            'created_at': now - timedelta(days=18),
            'updated_at': now - timedelta(days=18),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440013'),
            'text': 'Give an example of a time when you made a mistake in your code that caused a production issue. How did you handle it?',
            'question_type': 'behavioral',
            'difficulty': 'medium',
            'skills': ['Accountability', 'Problem Solving', 'Learning from Mistakes'],
            'tags': ['behavioral', 'mistakes', 'accountability'],
            'evaluation_criteria': 'Check honesty, accountability, problem-solving under pressure, and learning from mistakes.',
            'ideal_answer': 'Use STAR method. Situation: describe the mistake and its impact honestly. Task: explain the urgency and what needed to be fixed. Action: immediate response (acknowledge mistake, assess impact, communicate to team, fix the issue, deploy hotfix, monitor), post-mortem analysis, implement preventive measures (tests, code review, monitoring). Result: issue resolved, lessons learned, process improvements. Show accountability, quick problem-solving, and focus on prevention.',
            'rationale': 'Evaluates accountability, crisis management, and ability to learn from failures.',
            'version': 1,
            'created_at': now - timedelta(days=16),
            'updated_at': now - timedelta(days=16),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440014'),
            'text': 'How do you prioritize tasks when you have multiple urgent deadlines?',
            'question_type': 'situational',
            'difficulty': 'easy',
            'skills': ['Prioritization', 'Time Management', 'Decision Making'],
            'tags': ['situational', 'prioritization', 'time-management'],
            'evaluation_criteria': 'Assess prioritization skills and ability to make trade-off decisions under pressure.',
            'ideal_answer': 'Evaluate factors: business impact, dependencies, urgency vs importance, stakeholder needs, resource availability. Use frameworks like Eisenhower Matrix (urgent/important), communicate with stakeholders about priorities, negotiate deadlines if needed, break down tasks, focus on high-value work first. Be transparent about trade-offs and seek help when overwhelmed. Show systematic thinking and stakeholder management.',
            'rationale': 'Tests decision-making and time management skills essential for handling competing priorities.',
            'version': 1,
            'created_at': now - timedelta(days=14),
            'updated_at': now - timedelta(days=14),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440015'),
            'text': 'If you discovered a security vulnerability in production, what steps would you take?',
            'question_type': 'situational',
            'difficulty': 'medium',
            'skills': ['Security', 'Risk Management', 'Incident Response'],
            'tags': ['situational', 'security', 'incident-response'],
            'evaluation_criteria': 'Check security awareness, incident response procedures, and risk assessment capabilities.',
            'ideal_answer': 'Immediate steps: 1) Assess severity and potential impact, 2) Document the vulnerability, 3) Notify security team/manager immediately, 4) Do not publicly disclose until fixed, 5) Work with team to develop patch, 6) Test fix thoroughly, 7) Deploy fix following security protocols, 8) Monitor for exploitation, 9) Conduct post-incident review, 10) Update security practices. Show understanding of responsible disclosure and security-first mindset.',
            'rationale': 'Evaluates security awareness and proper incident response procedures.',
            'version': 1,
            'created_at': now - timedelta(days=12),
            'updated_at': now - timedelta(days=12),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440016'),
            'text': 'You need to refactor a large legacy codebase with no tests. How would you approach it?',
            'question_type': 'situational',
            'difficulty': 'hard',
            'skills': ['Refactoring', 'Legacy Code', 'Testing', 'Risk Management'],
            'tags': ['situational', 'refactoring', 'legacy-code'],
            'evaluation_criteria': 'Assess refactoring strategy, risk management, and systematic approach to technical debt.',
            'ideal_answer': 'Approach: 1) Understand the codebase (documentation, code analysis, team knowledge), 2) Add tests incrementally (start with critical paths, use characterization tests), 3) Identify refactoring priorities (high-risk, high-value areas first), 4) Refactor in small, incremental changes, 5) Maintain backward compatibility, 6) Use feature flags for risky changes, 7) Monitor for regressions, 8) Document changes. Show systematic approach, risk awareness, and focus on incremental improvement rather than big-bang rewrites.',
            'rationale': 'Tests ability to handle technical debt and refactoring challenges systematically.',
            'version': 1,
            'created_at': now - timedelta(days=10),
            'updated_at': now - timedelta(days=10),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440017'),
            'text': 'Explain how you would design a caching strategy for a high-traffic web application.',
            'question_type': 'technical',
            'difficulty': 'hard',
            'skills': ['System Design', 'Caching', 'Performance', 'Architecture'],
            'tags': ['system-design', 'caching', 'performance'],
            'evaluation_criteria': 'Evaluate system design thinking and understanding of caching patterns and trade-offs.',
            'ideal_answer': 'Multi-layer caching strategy: 1) Browser cache (static assets, long TTL), 2) CDN (geographic distribution, static content), 3) Application cache (Redis/Memcached for frequently accessed data, session data), 4) Database query cache. Considerations: cache invalidation strategy (TTL, event-based, manual), cache warming for critical data, cache-aside vs write-through patterns, handling cache misses, cache key design, monitoring hit rates. Choose cache locations based on data access patterns, update frequency, and consistency requirements. Balance between performance gains and complexity.',
            'rationale': 'Assesses system design skills and understanding of performance optimization techniques.',
            'version': 1,
            'created_at': now - timedelta(days=8),
            'updated_at': now - timedelta(days=8),
        },
        {
            'id': uuid.UUID('760e8400-e29b-41d4-a716-446655440018'),
            'text': 'What is the difference between horizontal and vertical scaling? When would you use each?',
            'question_type': 'technical',
            'difficulty': 'medium',
            'skills': ['System Design', 'Scalability', 'Infrastructure'],
            'tags': ['scalability', 'system-design', 'infrastructure'],
            'evaluation_criteria': 'Check understanding of scaling strategies and their trade-offs.',
            'ideal_answer': 'Vertical scaling (scale up) increases resources of existing server (more CPU, RAM, storage). Pros: simpler, no code changes needed, better for single-threaded apps. Cons: limited by hardware, expensive, single point of failure. Horizontal scaling (scale out) adds more servers. Pros: nearly unlimited scaling, cost-effective, better fault tolerance. Cons: requires stateless design, load balancing, distributed system complexity. Use vertical scaling for: small to medium apps, stateful applications, quick fixes. Use horizontal scaling for: large-scale systems, cloud-native apps, high availability requirements.',
            'rationale': 'Tests fundamental scalability knowledge essential for designing scalable systems.',
            'version': 1,
            'created_at': now - timedelta(days=6),
            'updated_at': now - timedelta(days=6),
        },
    ])

    print("[OK] Seeded 18 additional questions")


def downgrade() -> None:
    """Remove seeded questions."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM questions WHERE id IN (
            '760e8400-e29b-41d4-a716-446655440001',
            '760e8400-e29b-41d4-a716-446655440002',
            '760e8400-e29b-41d4-a716-446655440003',
            '760e8400-e29b-41d4-a716-446655440004',
            '760e8400-e29b-41d4-a716-446655440005',
            '760e8400-e29b-41d4-a716-446655440006',
            '760e8400-e29b-41d4-a716-446655440007',
            '760e8400-e29b-41d4-a716-446655440008',
            '760e8400-e29b-41d4-a716-446655440009',
            '760e8400-e29b-41d4-a716-446655440010',
            '760e8400-e29b-41d4-a716-446655440011',
            '760e8400-e29b-41d4-a716-446655440012',
            '760e8400-e29b-41d4-a716-446655440013',
            '760e8400-e29b-41d4-a716-446655440014',
            '760e8400-e29b-41d4-a716-446655440015',
            '760e8400-e29b-41d4-a716-446655440016',
            '760e8400-e29b-41d4-a716-446655440017',
            '760e8400-e29b-41d4-a716-446655440018'
        )
    """))

    print("[OK] Removed seeded questions")

