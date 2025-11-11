# Project Overview & Product Development Requirements (PDR)

**Project Name**: Elios AI Interview Service
**Version**: 0.1.0
**Last Updated**: 2025-11-02
**Status**: Active Development
**Repository**: https://github.com/elios/elios-ai-service

## Executive Summary

Elios AI Interview Service is an AI-powered mock interview platform that helps candidates prepare for technical interviews through personalized CV analysis, adaptive question generation, real-time answer evaluation, and comprehensive feedback. The platform leverages Large Language Models (OpenAI GPT-4), vector databases (Pinecone), and advanced NLP techniques to deliver a realistic, intelligent interview experience.

## Project Purpose

### Vision
Transform interview preparation by providing accessible, intelligent, and personalized mock interview experiences that adapt to each candidate's unique skills, experience, and learning needs.

### Mission
Empower candidates to confidently prepare for real interviews by:
- Analyzing their background and generating personalized interview questions
- Providing real-time feedback on their responses
- Identifying strengths and areas for improvement
- Offering actionable recommendations for skill development

### Value Proposition
- **Personalized Experience**: CV analysis drives customized question selection based on candidate's actual skills
- **Intelligent Evaluation**: AI-powered semantic analysis provides nuanced feedback beyond keyword matching
- **Comprehensive Feedback**: Detailed performance reports with specific improvement suggestions
- **Flexible Delivery**: Support for both text and voice-based interviews
- **Scalable Platform**: Clean Architecture enables easy integration of new AI models and services

## Target Users

### Primary Users

#### 1. Job Seekers & Candidates
**Needs**: Practice interviews, receive feedback, build confidence, identify weak areas
**Pain Points**:
- Limited access to mock interview opportunities
- Lack of personalized feedback
- Generic interview prep doesn't match their background
- Expensive interview coaching services

**Solution**: AI interviewer that adapts to their CV, provides instant feedback, and offers unlimited practice sessions

#### 2. Students & Recent Graduates
**Needs**: Prepare for first job interviews, understand interview expectations, practice answering technical questions
**Pain Points**:
- No professional interview experience
- Unsure what employers look for
- Limited access to mentors for interview prep
- High stakes with limited opportunities

**Solution**: Safe practice environment with constructive feedback and learning resources

#### 3. Career Changers
**Needs**: Bridge skill gaps, demonstrate transferable skills, prepare for industry-specific questions
**Pain Points**:
- Unclear how to present career transition
- Difficulty articulating transferable skills
- Industry-specific terminology and practices
- Competing with candidates with direct experience

**Solution**: CV analysis highlights transferable skills and generates relevant questions for target role

### Secondary Users

#### 4. Recruiters & HR Professionals
**Needs**: Pre-screen candidates, assess technical competency, standardize evaluation
**Pain Points**:
- Time-consuming manual screening
- Inconsistent evaluation criteria
- Difficulty assessing soft skills remotely
- Need for objective candidate comparisons

**Solution**: Standardized interview format with consistent evaluation metrics

#### 5. Educational Institutions
**Needs**: Provide career services, prepare students for job market, measure program effectiveness
**Pain Points**:
- Limited career counseling resources
- Difficult to scale 1-on-1 interview prep
- Tracking student preparation progress
- Demonstrating program outcomes

**Solution**: Scalable platform for student interview preparation with progress tracking

## Key Features & Capabilities

### 1. Intelligent CV Analysis

**Core Functionality**:
- Extract text from multiple formats (PDF, DOC, DOCX)
- Identify technical and soft skills using NLP
- Determine experience level and education
- Generate semantic embeddings for matching
- Suggest appropriate difficulty levels
- Recommend interview topics

**Implementation Status**: ✅ Domain models complete, 🔄 Adapters pending

**Technical Approach**:
- spaCy for NLP processing
- OpenAI GPT-4 for skill extraction and summarization
- OpenAI Embeddings (1536 dimensions) for semantic matching
- Pinecone for vector storage and similarity search

### 2. Adaptive Question Generation

**Core Functionality**:
- Exemplar-based question generation using vector search
- Dynamic question creation with similar question inspiration
- Difficulty progression throughout interview
- Coverage of multiple skills and topics
- Follow-up questions based on previous answers

**Implementation Status**: ✅ Domain models complete, ✅ Use cases implemented, ✅ Vector search integrated

**Technical Approach**:
- PostgreSQL question bank with metadata
- Vector similarity search retrieves 3 exemplar questions
- Exemplars filtered by question_type, difficulty (similarity >0.5)
- LLM generates NEW questions inspired by exemplars
- Questions stored with embeddings for future exemplar searches
- Graceful fallback: Generate without exemplars if search fails

### 3. Real-Time Answer Evaluation

**Core Functionality**:
- Semantic similarity scoring
- Completeness and relevance assessment
- Confidence and sentiment analysis
- Strength and weakness identification
- Improvement suggestions
- Multi-dimensional scoring (0-100 scale)

**Implementation Status**: ✅ Domain models complete, ✅ LLM adapter implemented

**Technical Approach**:
- OpenAI GPT-4 for answer evaluation
- Structured JSON output for consistent scoring
- Vector embeddings for semantic similarity
- Multi-factor evaluation criteria

### 4. Comprehensive Feedback Generation

**Core Functionality**:
- Overall performance summary
- Skill-specific breakdown
- Question-by-question analysis
- Actionable improvement recommendations
- Performance trends over multiple interviews
- Strengths and growth areas

**Implementation Status**: ✅ Domain models complete, 🔄 Analytics adapters pending

**Technical Approach**:
- Aggregated scoring across interview
- LLM-generated narrative feedback
- Historical performance tracking
- Visualization-ready metrics

### 5. Voice Interview Support (Planned)

**Core Functionality**:
- Speech-to-text for candidate answers
- Text-to-speech for question delivery
- Multi-language support (EN, VI)
- Natural conversation flow
- Audio quality handling

**Implementation Status**: 🔄 Ports defined, ⏳ Adapters pending

**Technical Approach**:
- Azure Speech-to-Text API
- Microsoft Edge TTS
- Real-time audio streaming
- Transcript storage

### 6. Multi-Channel Interview Delivery

**Core Functionality**:
- REST API for CRUD operations
- WebSocket for real-time chat
- Async operations for responsiveness
- Session management
- Progress tracking

**Implementation Status**: 🔄 Health check only, ⏳ Full API pending

**Technical Approach**:
- FastAPI framework
- WebSocket protocol
- Async/await patterns
- JWT authentication (planned)

## Technical Requirements

### Functional Requirements

**FR1: CV Upload and Analysis**
- Support PDF, DOC, and DOCX file formats
- Extract structured information (skills, experience, education)
- Generate semantic embeddings
- Store analysis results in database
- Link analysis to candidate profile

**FR2: Interview Session Management**
- Create interview sessions linked to CV analysis
- Select appropriate questions based on CV
- Track interview progress and state
- Support interview pause/resume
- Store complete interview history

**FR3: Question Presentation**
- Retrieve questions from database
- Apply semantic matching for relevance
- Present questions with metadata
- Support text and voice delivery
- Track question order and timing

**FR4: Answer Collection and Evaluation**
- Accept text and voice answers
- Perform real-time evaluation
- Calculate multi-dimensional scores
- Store answers with evaluations
- Link answers to questions

**FR5: Feedback Generation**
- Aggregate interview results
- Generate comprehensive reports
- Provide actionable recommendations
- Calculate skill-specific scores
- Compare against benchmarks

**FR6: Data Persistence**
- Store candidates, interviews, questions, answers
- Maintain CV analysis results
- Track evaluation history
- Support efficient querying
- Ensure data integrity

**FR7: External Service Integration**
- Connect to LLM providers (OpenAI, Claude, Llama)
- Integrate vector databases (Pinecone, Weaviate, ChromaDB)
- Utilize speech services (Azure STT, Edge TTS)
- Support service provider switching

### Non-Functional Requirements

**NFR1: Performance**
- CV analysis completion < 30 seconds
- Question generation < 3 seconds
- Answer evaluation < 5 seconds
- Support 100+ concurrent interviews
- Database query response < 100ms

**NFR2: Scalability**
- Horizontal scaling for API servers
- Async processing for I/O operations
- Efficient vector search (< 50ms)
- Connection pooling for databases
- Stateless interview sessions

**NFR3: Reliability**
- 99.5% uptime target
- Graceful degradation if services fail
- Data backup and recovery
- Transaction integrity
- Error logging and monitoring

**NFR4: Security**
- Secure API key management
- PII data encryption at rest
- HTTPS for all communications
- Input validation and sanitization
- SQL injection prevention
- Rate limiting

**NFR5: Maintainability**
- Clean Architecture for loose coupling
- Comprehensive documentation
- Type hints throughout codebase
- Unit test coverage > 80%
- Code follows PEP 8 standards

**NFR6: Usability**
- Intuitive API design
- Clear error messages
- Comprehensive API documentation
- Interactive Swagger UI
- Reasonable response times

**NFR7: Flexibility**
- Swappable LLM providers
- Swappable vector databases
- Configurable via environment variables
- Support for multiple languages
- Extensible architecture

## Architecture Overview

### Pattern: Clean Architecture (Hexagonal/Ports & Adapters)

```
┌─────────────────────────────────────────────────────┐
│           Infrastructure Layer                       │
│     (Config, Database, Logging, DI Container)       │
└─────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────┐
│             Adapters Layer                           │
│  (LLM, VectorDB, Speech, CV Processing, API, DB)   │
└─────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────┐
│           Application Layer                          │
│          (Use Cases, DTOs, Orchestration)           │
└─────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────┐
│             Domain Layer                             │
│   (Models, Services, Ports - Pure Business Logic)  │
└─────────────────────────────────────────────────────┘
```

**Key Benefits**:
- ✅ **Technology Independence**: Domain logic unaffected by framework/tool changes
- ✅ **Testability**: Domain can be tested in complete isolation
- ✅ **Flexibility**: Easy to swap external services (OpenAI → Claude → Llama)
- ✅ **Maintainability**: Clear separation of concerns and responsibilities
- ✅ **Team Scalability**: Teams can work on different layers independently

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI (REST API & WebSocket)
- **Async Runtime**: asyncio for non-blocking I/O
- **Validation**: Pydantic 2.x for data models and settings
- **Type Checking**: mypy for static type analysis

### Domain Layer (Minimal Dependencies)
- Pure Python standard library
- Pydantic for data validation
- Python type hints

### External Services (via Adapters)

**LLM Providers**:
- OpenAI GPT-4 (primary) ✅
- Anthropic Claude (planned) ⏳
- Meta Llama 3 (planned) ⏳

**Vector Databases**:
- Pinecone (primary) ✅
- Weaviate (alternative) ⏳
- ChromaDB (local dev) ⏳

**Speech Services**:
- Azure Speech-to-Text ⏳
- Microsoft Edge TTS ⏳
- Google Speech (alternative) ⏳

**Database**:
- PostgreSQL 14+ with async support ✅
- SQLAlchemy 2.0+ (async) ✅
- Alembic for migrations ✅
- asyncpg driver ✅

**NLP & Document Processing**:
- spaCy for text processing ⏳
- LangChain for workflow orchestration ⏳
- PyPDF2 for PDF parsing ⏳
- python-docx for DOCX parsing ⏳

### Development Tools
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: ruff (fast Python linter)
- **Formatting**: black (code formatter)
- **Type Checking**: mypy
- **Database Migrations**: Alembic

### Infrastructure
- **Configuration**: Pydantic Settings with .env files
- **Dependency Injection**: Custom container
- **Logging**: Structured logging (planned)
- **Deployment**: Docker containers (planned)

## Success Metrics

### User Engagement Metrics
- Number of active candidates
- Interviews completed per week
- Average interview duration
- User retention rate (30-day)
- Repeat interview sessions

### Performance Metrics
- CV analysis accuracy (skill extraction)
- Question relevance score (user feedback)
- Answer evaluation accuracy (vs human raters)
- Platform response times
- API availability (uptime %)

### Quality Metrics
- User satisfaction score (CSAT)
- Net Promoter Score (NPS)
- Feedback usefulness rating
- Candidate improvement over time
- Interview preparation confidence increase

### Technical Metrics
- Test coverage > 80%
- API response time < 200ms (p95)
- Database query time < 100ms (p95)
- LLM API success rate > 99%
- System uptime > 99.5%

### Business Metrics
- User acquisition cost
- Conversion rate (free → paid)
- Revenue per user
- Churn rate
- Customer lifetime value

## Project Roadmap

### Phase 1: Foundation (Current - v0.1.0)
**Status**: ✅ Near Complete (95%)
**Timeline**: 2 months

**Completed**:
- ✅ Domain models (Candidate, Interview, Question, Answer, CVAnalysis)
- ✅ Repository ports (5 interfaces)
- ✅ PostgreSQL persistence layer (5 repositories)
- ✅ OpenAI LLM adapter
- ✅ Pinecone vector database adapter
- ✅ Mock adapters (LLM, STT, TTS for development)
- ✅ Database migrations with Alembic
- ✅ Use cases (AnalyzeCV, StartInterview, GetNextQuestion, ProcessAnswer, CompleteInterview)
- ✅ DTOs (interview, answer, websocket)
- ✅ Configuration management
- ✅ Dependency injection container
- ✅ REST API (health + interview endpoints)
- ✅ WebSocket handler (real-time interview sessions)

**In Progress**:
- 🔄 CV processing adapters (spaCy, document parsing)
- 🔄 Analytics service
- 🔄 Feedback generation use case

**Remaining**:
- ⏳ Authentication & authorization
- ⏳ Rate limiting
- ⏳ Comprehensive testing
- ⏳ API documentation (Swagger)
- ⏳ Deployment scripts

### Phase 2: Core Features (v0.2.0 - v0.5.0)
**Timeline**: 3-4 months

**Features**:
- Voice interview support (Azure STT, Edge TTS)
- Advanced question generation
- Interview history and analytics
- Performance benchmarks
- Multiple difficulty levels
- Frontend integration

### Phase 3: Intelligence Enhancement (v0.6.0 - v0.8.0)
**Timeline**: 3-4 months

**Features**:
- Multi-LLM support (Claude, Llama)
- Behavioral question analysis
- Personality insights
- Interview strategy recommendations
- Skill gap analysis
- Learning resource recommendations

### Phase 4: Scale & Polish (v0.9.0 - v1.0.0)
**Timeline**: 2-3 months

**Features**:
- Multi-language support (Vietnamese, English)
- Team/organization features
- Advanced analytics dashboard
- Mobile app support
- Performance optimization
- Production deployment

## Risk Management

### Technical Risks

**Risk 1: LLM API Availability**
- **Impact**: High (service unavailable)
- **Likelihood**: Low
- **Mitigation**: Multi-provider support, fallback mechanisms, caching, retry logic

**Risk 2: Vector Database Performance**
- **Impact**: Medium (slow question matching)
- **Likelihood**: Medium
- **Mitigation**: Caching, query optimization, indexing strategies, alternative providers

**Risk 3: Data Privacy & Security**
- **Impact**: Critical (legal liability)
- **Likelihood**: Low
- **Mitigation**: Encryption, access controls, GDPR compliance, security audits

**Risk 4: Evaluation Accuracy**
- **Impact**: High (poor user experience)
- **Likelihood**: Medium
- **Mitigation**: Multiple evaluation methods, human validation, continuous improvement, user feedback loops

### Business Risks

**Risk 5: User Adoption**
- **Impact**: High (product viability)
- **Likelihood**: Medium
- **Mitigation**: User research, beta testing, iterative improvements, marketing strategy

**Risk 6: Competition**
- **Impact**: Medium (market share)
- **Likelihood**: Medium
- **Mitigation**: Unique value proposition, quality focus, rapid innovation

## Constraints & Assumptions

### Technical Constraints
- Python 3.11+ required
- PostgreSQL 14+ required
- API keys for OpenAI and Pinecone
- Internet connectivity for external services
- Async-compatible libraries only

### Operational Constraints
- API rate limits (OpenAI, Pinecone)
- Cloud service costs
- Data storage limits
- Processing time for CV analysis

### Design Constraints
- Clean Architecture pattern (no exceptions)
- Domain layer has zero external dependencies
- All external services behind ports
- Async-first design
- RESTful API conventions

### Assumptions
- Users have CV in standard formats
- Interview answers are text-based initially
- Users speak English or Vietnamese
- Internet connectivity is stable
- External APIs are generally available

## Compliance & Standards

### Data Protection
- GDPR compliance for EU users
- Data retention policies
- Right to deletion
- Data export capability
- Consent management

### Code Standards
- PEP 8 Python style guide
- Type hints throughout
- Docstrings for all public APIs
- Clean Architecture principles
- SOLID principles
- DRY (Don't Repeat Yourself)

### Testing Standards
- Unit test coverage > 80%
- Integration tests for external services
- E2E tests for critical flows
- Performance benchmarks
- Security testing

### Documentation Standards
- Comprehensive README
- API documentation (OpenAPI/Swagger)
- Architecture documentation
- Code examples
- Setup guides

## Glossary

- **CV Analysis**: Structured extraction of skills, experience, and education from candidate resumes
- **Vector Embedding**: Numerical representation of text in high-dimensional space for semantic similarity
- **Semantic Search**: Finding relevant content based on meaning rather than keywords
- **Port**: Abstract interface defining contract for external dependencies (Hexagonal Architecture)
- **Adapter**: Concrete implementation of a port for specific technology
- **Domain Model**: Business entity with behavior (not just data)
- **Use Case**: Application-specific business flow orchestrating domain objects
- **Aggregate Root**: Entity that controls access to related entities (Interview)
- **Repository**: Pattern for abstracting data access
- **LLM**: Large Language Model (GPT-4, Claude, etc.)
- **STT**: Speech-to-Text conversion
- **TTS**: Text-to-Speech synthesis
- **PII**: Personally Identifiable Information

## References

### Internal Documentation
- [System Architecture](./system-architecture.md)
- [Codebase Summary](./codebase-summary.md)
- [Code Standards](./code-standards.md)
- [API Documentation](./system-architecture.md#api-architecture)
- [Database Setup Guide](../DATABASE_SETUP.md)

### External Resources
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Pinecone Documentation](https://docs.pinecone.io/)

## Appendices

### Appendix A: Database Schema Summary
- 5 main tables: candidates, interviews, questions, answers, cv_analyses
- Foreign key relationships for data integrity
- Indexes on frequently queried columns
- JSONB columns for flexible metadata

### Appendix B: API Endpoint Summary
- `/health` - Health check
- `/api/cv/upload` - Upload and analyze CV
- `/api/interviews` - Interview CRUD
- `/api/questions` - Question management
- `/api/ws/interviews/{id}` - WebSocket chat

### Appendix C: Development Setup Summary
1. Install Python 3.11+
2. Create virtual environment
3. Install dependencies: `pip install -e ".[dev]"`
4. Configure .env file with API keys
5. Run database migrations: `alembic upgrade head`
6. Start server: `python src/main.py`

## Unresolved Questions

1. **Pricing Model**: Freemium vs subscription vs usage-based?
2. **Interview Length**: Optimal number of questions per session?
3. **Evaluation Calibration**: How to ensure consistent scoring across different LLMs?
4. **Multi-Language Priority**: Which languages to support first after English?
5. **Mobile Strategy**: Native apps vs responsive web?
6. **Team Features**: B2B offering for companies and schools?
7. **Certification**: Provide certificates of completion or proficiency?

---

**Document Status**: Living document, updated with each milestone
**Next Review**: After Phase 1 completion
**Maintainers**: Elios Development Team
