# Architecture Documentation

## Overview

Elios AI Interview Service follows **Clean Architecture / Ports & Adapters (Hexagonal Architecture)** pattern. This architectural style ensures the system is:
- **Flexible**: Easy to swap external services (LLM providers, databases, etc.)
- **Testable**: Domain logic can be tested in isolation
- **Maintainable**: Clear separation of concerns
- **Scalable**: Multiple teams can work independently on different components

## Architectural Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                     │
│              (Config, Logging, DI Container)                 │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Adapters Layer                          │
│   (LLM, Vector DB, Speech, CV Processing, Persistence)      │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│              (Use Cases, DTOs, Orchestration)                │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│        (Models, Services, Ports - Pure Business Logic)       │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Rule

**Dependencies point inward**: Outer layers depend on inner layers, never the reverse.

- **Domain Layer**: No dependencies on any other layer (pure Python)
- **Application Layer**: Depends only on Domain
- **Adapters Layer**: Implements Domain ports, depends on Domain
- **Infrastructure Layer**: Wires everything together, depends on all layers

## Layer Details

### 1. Domain Layer (`src/domain/`)

The core of the application containing pure business logic with **zero external dependencies**.

#### Models (`src/domain/models/`)

Rich domain entities with behavior, not just data containers.

**Key Entities:**

- **`Candidate`**: Represents a candidate with CV management
  - Methods: `update_cv()`, `has_cv()`

- **`Interview`** (Aggregate Root): Controls interview lifecycle
  - States: `PREPARING`, `READY`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`
  - Methods: `start()`, `complete()`, `cancel()`, `add_question()`, `add_answer()`
  - Business Rules: Can't start without CV analysis, tracks progress, manages Q&A flow

- **`Question`**: Interview question with metadata
  - Types: `TECHNICAL`, `BEHAVIORAL`, `SITUATIONAL`
  - Difficulty: `EASY`, `MEDIUM`, `HARD`
  - Methods: `has_skill()`, `has_tag()`, `is_suitable_for_difficulty()`

- **`Answer`**: Candidate's answer with evaluation
  - Properties: `text`, `is_voice`, `audio_file_path`, `evaluation`
  - Methods: `evaluate()`, `is_evaluated()`, `get_score()`

- **`CVAnalysis`**: Structured CV analysis results
  - Contains: `skills`, `work_experience_years`, `education_level`, `suggested_topics`
  - Methods: `get_technical_skills()`, `has_skill()`, `get_top_skills()`, `is_experienced()`

#### Services (`src/domain/services/`)

Domain services containing business logic that doesn't belong to a single entity.

**Examples to implement:**
- `InterviewOrchestrator`: Controls interview flow logic
- `QuestionSelector`: Selects next question based on context
- `AnswerEvaluator`: Evaluates answer quality
- `FeedbackGenerator`: Generates interview feedback

#### Ports (`src/domain/ports/`)

Abstract interfaces defining contracts for external dependencies. This is the key to flexibility.

**Defined Ports:**

1. **`LLMPort`**: Large Language Model interface
   - `generate_question()`: Create interview questions
   - `evaluate_answer()`: Assess answer quality
   - `generate_feedback_report()`: Create comprehensive feedback
   - `summarize_cv()`: Summarize CV content
   - `extract_skills_from_text()`: Extract skills using NLP

2. **`VectorSearchPort`**: Vector database interface
   - `store_question_embedding()`: Store question vectors
   - `store_cv_embedding()`: Store CV vectors
   - `find_similar_questions()`: Semantic search for questions
   - `find_similar_answers()`: Calculate answer similarity
   - `get_embedding()`: Generate text embeddings

3. **`QuestionRepositoryPort`**: Question persistence interface
   - `save()`, `get_by_id()`, `get_by_ids()`
   - `find_by_skill()`, `find_by_type()`, `find_by_tags()`
   - `update()`, `delete()`, `list_all()`

4. **`CVAnalyzerPort`**: CV analysis interface
   - `analyze_cv()`: Extract structured information from CV
   - `extract_text_from_file()`: Parse document files

5. **`SpeechToTextPort`**: Speech recognition interface
   - `transcribe_audio()`: Convert audio to text
   - `transcribe_stream()`: Real-time transcription
   - `detect_language()`: Identify spoken language

6. **`TextToSpeechPort`**: Speech synthesis interface
   - `synthesize_speech()`: Convert text to audio
   - `save_speech_to_file()`: Save audio to file
   - `list_available_voices()`: Get available voices

7. **`AnalyticsPort`**: Analytics and reporting interface
   - `record_answer_evaluation()`: Store evaluation data
   - `get_interview_statistics()`: Retrieve interview metrics
   - `get_candidate_performance_history()`: Historical data
   - `generate_improvement_recommendations()`: Create suggestions
   - `calculate_skill_scores()`: Per-skill scoring

### 2. Application Layer (`src/application/`)

Orchestrates use cases by coordinating domain objects and ports.

#### Use Cases (`src/application/use_cases/`)

Application-specific business flows that use domain services and ports.

**Implemented Use Cases:**

1. **`AnalyzeCVUseCase`**: CV analysis workflow
   ```python
   async def execute(cv_file_path: str, candidate_id: UUID) -> CVAnalysis:
       1. Extract text from CV
       2. Analyze and extract structured info
       3. Generate embeddings
       4. Store in vector database
   ```

2. **`StartInterviewUseCase`**: Interview initialization workflow
   ```python
   async def execute(candidate_id: UUID, cv_analysis: CVAnalysis, num_questions: int) -> Interview:
       1. Validate CV analysis
       2. Find suitable questions via semantic search
       3. Create interview with selected questions
       4. Mark interview as ready
   ```

**Use Cases to Implement:**

3. **`GetNextQuestionUseCase`**: Retrieve next question during interview
4. **`ProcessAnswerUseCase`**: Handle candidate answer and evaluation
5. **`CompleteInterviewUseCase`**: Finalize interview and generate report
6. **`GenerateFeedbackUseCase`**: Create comprehensive feedback report

#### DTOs (`src/application/dto/`)

Data Transfer Objects for cross-layer communication. Prevents domain models from leaking to API layer.

### 3. Adapters Layer (`src/adapters/`)

Implements domain ports with concrete technologies. This is where external integrations live.

#### LLM Adapters (`src/adapters/llm/`)

**`OpenAIAdapter`** (Implemented):
- Uses OpenAI GPT-4 for question generation and answer evaluation
- Implements structured output with JSON mode
- Configurable model and temperature
- Example output:
  ```json
  {
    "score": 75.0,
    "completeness": 0.8,
    "relevance": 0.9,
    "sentiment": "confident",
    "strengths": ["Clear explanation", "Good examples"],
    "weaknesses": ["Missing edge cases"],
    "improvements": ["Add complexity analysis"]
  }
  ```

**To Implement:**
- `ClaudeAdapter`: Anthropic Claude implementation
- `LlamaAdapter`: Meta Llama implementation

**Swapping LLM Providers:**
```python
# Just change environment variable:
LLM_PROVIDER=claude

# DI container handles the rest automatically
```

#### Vector Database Adapters (`src/adapters/vector_db/`)

**`PineconeAdapter`** (Implemented):
- Serverless vector storage with 1536 dimensions (OpenAI embeddings)
- Cosine similarity search
- Metadata filtering support
- Auto-creates index if missing

**To Implement:**
- `WeaviateAdapter`: Weaviate implementation
- `ChromaAdapter`: ChromaDB for local development

**Swapping Vector DBs:**
```python
VECTOR_DB_PROVIDER=weaviate
```

#### Speech Adapters (`src/adapters/speech/`)

**To Implement:**
- `AzureSTTAdapter`: Azure Speech-to-Text
- `EdgeTTSAdapter`: Microsoft Edge TTS
- `GoogleSpeechAdapter`: Google Speech services (alternative)

#### CV Processing Adapters (`src/adapters/cv_processing/`)

**To Implement:**
- `SpacyCVAnalyzer`: spaCy-based CV parser
- `LangChainCVAnalyzer`: LangChain-based analyzer

#### Persistence Adapters (`src/adapters/persistence/`)

**To Implement:**
- `PostgresQuestionRepository`: PostgreSQL implementation for questions
- `PostgresInterviewRepository`: Interview persistence
- `InMemoryRepository`: For testing

#### API Adapters (`src/adapters/api/`)

**To Implement:**

**REST API** (`src/adapters/api/rest/`):
- `interview_routes.py`: Interview CRUD and control
- `cv_routes.py`: CV upload and analysis
- `analytics_routes.py`: Performance and feedback
- `question_routes.py`: Question management

**WebSocket** (`src/adapters/api/websocket/`):
- `chat_handler.py`: Real-time interview chat

### 4. Infrastructure Layer (`src/infrastructure/`)

Cross-cutting concerns and application bootstrap.

#### Configuration (`src/infrastructure/config/`)

**`Settings`**: Pydantic-based configuration
- Environment variable loading from `.env`
- Type validation
- Default values
- Computed properties (e.g., `database_url`)

**Key Settings Groups:**
- Application (name, version, environment)
- API (host, port, CORS)
- LLM Provider selection and credentials
- Vector DB configuration
- Database connection
- Speech services
- File storage paths
- Interview parameters
- Logging configuration

#### Dependency Injection (`src/infrastructure/dependency_injection/`)

**`Container`**: Central DI container that wires all dependencies.

**Pattern:**
```python
class Container:
    def llm_port(self) -> LLMPort:
        if settings.llm_provider == "openai":
            return OpenAIAdapter(...)
        elif settings.llm_provider == "claude":
            return ClaudeAdapter(...)

    def vector_search_port(self) -> VectorSearchPort:
        if settings.vector_db_provider == "pinecone":
            return PineconeAdapter(...)
        elif settings.vector_db_provider == "weaviate":
            return WeaviateAdapter(...)
```

**Benefits:**
- Single source of truth for dependencies
- Easy to mock for testing
- Configuration-driven implementation selection

#### Logging (`src/infrastructure/logging/`)

**To Implement:**
- Structured logging (JSON format for production)
- Context injection (interview_id, candidate_id)
- Log levels based on environment
- Integration with monitoring tools

## Design Patterns & Principles

### 1. Dependency Inversion Principle (DIP)

High-level modules don't depend on low-level modules. Both depend on abstractions (ports).

**Example:**
```python
# ❌ BAD: Direct dependency on concrete implementation
class InterviewService:
    def __init__(self):
        self.openai = OpenAI(api_key="...")  # Tightly coupled!

# ✅ GOOD: Dependency on abstraction
class InterviewService:
    def __init__(self, llm: LLMPort):  # Flexible!
        self.llm = llm
```

### 2. Single Responsibility Principle (SRP)

Each class has one reason to change.

- **Domain Models**: Business state and rules
- **Domain Services**: Business logic across entities
- **Use Cases**: Application workflows
- **Adapters**: External service integration
- **Ports**: Contracts/interfaces

### 3. Open/Closed Principle (OCP)

Open for extension, closed for modification.

**Example: Adding new LLM provider**
```python
# No existing code needs to change!
# Just add new adapter:
class GeminiAdapter(LLMPort):
    async def generate_question(self, ...):
        # Implementation

# Register in container:
elif settings.llm_provider == "gemini":
    return GeminiAdapter(...)
```

### 4. Interface Segregation Principle (ISP)

Ports are focused and specific. No "god interfaces".

- `LLMPort`: Only LLM operations
- `VectorSearchPort`: Only vector operations
- `SpeechToTextPort`: Only STT operations

### 5. Repository Pattern

Abstract data access behind repository interfaces.

```python
# Domain doesn't know about SQL, just asks repository
questions = await question_repo.find_by_skill("Python")
```

### 6. Strategy Pattern

Ports enable runtime selection of algorithms/implementations.

```python
# Same interface, different implementations
llm = container.llm_port()  # Could be OpenAI, Claude, or Llama
```

## Data Flow Examples

### CV Analysis Flow

```
1. API Layer receives CV upload
   ↓
2. AnalyzeCVUseCase.execute()
   ↓
3. CVAnalyzerPort.analyze_cv()  ← Adapter extracts text & skills
   ↓
4. VectorSearchPort.get_embedding()  ← Generate CV embedding
   ↓
5. VectorSearchPort.store_cv_embedding()  ← Store for later matching
   ↓
6. Return CVAnalysis to API Layer
```

### Interview Question Flow

```
1. StartInterviewUseCase.execute()
   ↓
2. VectorSearchPort.find_similar_questions(cv_embedding)
   ↓
3. QuestionRepositoryPort.get_by_ids()
   ↓
4. Interview.add_question() for each  ← Domain logic
   ↓
5. Interview.mark_ready()
   ↓
6. Return Interview to API Layer
```

### Answer Evaluation Flow

```
1. Candidate submits answer via API/WebSocket
   ↓
2. ProcessAnswerUseCase.execute()
   ↓
3. LLMPort.evaluate_answer()  ← Get AI evaluation
   ↓
4. VectorSearchPort.find_similar_answers()  ← Semantic similarity
   ↓
5. Answer.evaluate(AnswerEvaluation)  ← Domain model update
   ↓
6. AnalyticsPort.record_answer_evaluation()  ← Store analytics
   ↓
7. Return evaluated Answer
```

## Testing Strategy

### Unit Tests (`tests/unit/`)

Test domain logic in isolation with mocked ports.

```python
def test_interview_start():
    interview = Interview(candidate_id=uuid4())
    interview.mark_ready(cv_analysis_id=uuid4())

    interview.start()

    assert interview.status == InterviewStatus.IN_PROGRESS
    assert interview.started_at is not None
```

**Characteristics:**
- Fast (milliseconds)
- No external dependencies
- High coverage of business logic

### Integration Tests (`tests/integration/`)

Test adapters with real external services.

```python
@pytest.mark.asyncio
async def test_openai_adapter_generates_question(openai_adapter):
    context = {"cv_summary": "5 years Python experience"}

    question = await openai_adapter.generate_question(
        context=context,
        skill="Python",
        difficulty="medium"
    )

    assert question
    assert len(question) > 10
```

**Characteristics:**
- Slower (seconds)
- Real API calls (use test environments)
- Validates adapter implementations

### E2E Tests (`tests/e2e/`)

Test complete user flows through API.

```python
@pytest.mark.asyncio
async def test_complete_interview_flow(api_client):
    # Upload CV
    cv_response = await api_client.post("/api/v1/cv/upload", ...)

    # Start interview
    interview_response = await api_client.post("/api/v1/interviews/start", ...)

    # Answer questions
    for i in range(5):
        answer_response = await api_client.post(f"/api/v1/interviews/{id}/answer", ...)

    # Get feedback
    feedback_response = await api_client.get(f"/api/v1/interviews/{id}/feedback")

    assert feedback_response.status_code == 200
```

**Characteristics:**
- Slowest (seconds to minutes)
- Full system integration
- Validates user experiences

## Performance Considerations

### 1. Vector Search Caching

Cache frequently accessed embeddings to reduce latency.

```python
@lru_cache(maxsize=1000)
async def get_question_embedding(question_id: UUID) -> List[float]:
    return await vector_search.get_embedding(...)
```

### 2. LLM Call Optimization

- Use streaming for real-time responses
- Implement rate limiting and retry logic
- Cache similar prompts

### 3. Database Connection Pooling

Use SQLAlchemy async connection pooling:
```python
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=10,
)
```

### 4. WebSocket for Real-time

Use WebSocket instead of polling for live interview updates.

## Security Considerations

### 1. API Keys

- Never commit to repository
- Use environment variables
- Rotate regularly
- Use secrets management in production (AWS Secrets Manager, Azure Key Vault)

### 2. Candidate Data (PII)

- Encrypt at rest
- Minimal data collection
- Clear retention policies
- GDPR compliance

### 3. Authentication & Authorization

Implement in API layer:
- JWT tokens
- Role-based access control (RBAC)
- Rate limiting per user

### 4. Input Validation

- Pydantic models for all inputs
- File upload size limits
- Sanitize CV text before processing

## Deployment Architecture

### Development

```
Developer Machine
├── Python App (src/)
├── PostgreSQL (Docker)
├── Pinecone (Cloud)
└── OpenAI (Cloud)
```

### Production

```
Load Balancer
    ↓
API Servers (Kubernetes)
    ↓
├── PostgreSQL (AWS RDS)
├── Pinecone (Cloud)
├── OpenAI (Cloud)
└── Azure Speech (Cloud)
```

**Recommendations:**
- Containerize with Docker
- Orchestrate with Kubernetes
- Use managed services for databases
- Implement health checks
- Set up monitoring (Prometheus, Grafana)
- Configure auto-scaling

## Migration Strategies

### Changing LLM Provider

1. Implement new adapter
2. Add configuration option
3. A/B test both providers
4. Gradual rollout
5. Monitor performance
6. Full switch or fallback

### Changing Vector Database

1. Implement new adapter
2. Run data migration script
3. Dual-write to both databases
4. Verify data consistency
5. Switch read traffic
6. Decomission old database

## Troubleshooting

### Common Issues

1. **Import Errors**: Check Python path and virtual environment
2. **Port Not Available**: Verify no other service using port 8000
3. **Database Connection**: Check PostgreSQL is running and credentials are correct
4. **API Key Invalid**: Verify environment variables are loaded
5. **Vector DB Empty**: Run data seeding script to populate questions

## Future Enhancements

### Planned Features

1. **Multi-language Support**: Interview in Vietnamese, English, etc.
2. **Video Interviews**: Face analysis and body language feedback
3. **Mock Pairing Interviews**: Collaborative coding scenarios
4. **Interview Marketplace**: Public question bank contributions
5. **ML-based Scoring**: Custom models for specific industries
6. **Interview Coaching Mode**: Practice mode with hints

### Architectural Improvements

1. **Event Sourcing**: Track all interview events for replay
2. **CQRS**: Separate read/write models for better scaling
3. **Service Mesh**: For microservices communication
4. **GraphQL API**: Alternative to REST for flexible queries
5. **Real-time Collaboration**: Multiple interviewers

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
