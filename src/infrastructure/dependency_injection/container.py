"""Dependency injection container.

This module wires up all dependencies and provides them to the application.
It's the only place that knows about concrete implementations.
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

# Import adapters
from ...adapters.llm.openai_adapter import OpenAIAdapter

# Import mock adapters
from ...adapters.mock import (
    MockAnalyticsAdapter,
    MockCVAnalyzerAdapter,
    MockLLMAdapter,
    MockSTTAdapter,
    MockTTSAdapter,
    MockVectorSearchAdapter,
)

# Import persistence adapters
from ...adapters.persistence import (
    PostgreSQLAnswerRepository,
    PostgreSQLCandidateRepository,
    PostgreSQLCVAnalysisRepository,
    PostgreSQLInterviewRepository,
    PostgreSQLQuestionRepository,
)
from ...adapters.vector_db.pinecone_adapter import PineconeAdapter
from ...domain.ports import (
    AnalyticsPort,
    AnswerRepositoryPort,
    CandidateRepositoryPort,
    CVAnalysisRepositoryPort,
    CVAnalyzerPort,
    InterviewRepositoryPort,
    LLMPort,
    QuestionRepositoryPort,
    SpeechToTextPort,
    TextToSpeechPort,
    VectorSearchPort,
)
from ...infrastructure.config.settings import Settings, get_settings


class Container:
    """Dependency injection container.

    This class is responsible for creating and managing all dependencies.
    It follows the dependency inversion principle by depending on ports
    (interfaces) while providing concrete implementations.
    """

    def __init__(self, settings: Settings):
        """Initialize container with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._llm_port: LLMPort | None = None
        self._vector_search_port: VectorSearchPort | None = None
        self._stt_port: SpeechToTextPort | None = None
        self._tts_port: TextToSpeechPort | None = None

    def llm_port(self) -> LLMPort:
        """Get LLM port implementation.

        Returns:
            Configured LLM port based on settings

        Raises:
            ValueError: If LLM provider is not supported or not configured
        """
        if self._llm_port is None:
            # Use mock adapter if configured
            if self.settings.use_mock_adapters:
                self._llm_port = MockLLMAdapter()
            elif self.settings.llm_provider == "openai":
                if not self.settings.openai_api_key:
                    raise ValueError("OpenAI API key not configured")

                self._llm_port = OpenAIAdapter(
                    api_key=self.settings.openai_api_key,
                    model=self.settings.openai_model,
                    temperature=self.settings.openai_temperature,
                )
            elif self.settings.llm_provider == "claude":
                if not self.settings.anthropic_api_key:
                    raise ValueError("Anthropic API key not configured")

                # Import Claude adapter when implemented
                # from ...adapters.llm.claude_adapter import ClaudeAdapter
                # self._llm_port = ClaudeAdapter(
                #     api_key=self.settings.anthropic_api_key,
                #     model=self.settings.anthropic_model,
                # )
                raise NotImplementedError("Claude adapter not yet implemented")
            else:
                raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")

        return self._llm_port

    def vector_search_port(self) -> VectorSearchPort:
        """Get vector search port implementation.

        Returns:
            Configured vector search port based on settings

        Raises:
            ValueError: If vector DB provider is not supported or not configured
        """
        if self._vector_search_port is None:
            # Use mock adapter if configured
            if self.settings.use_mock_adapters:
                self._vector_search_port = MockVectorSearchAdapter()
            elif self.settings.vector_db_provider == "pinecone":
                if not self.settings.pinecone_api_key:
                    raise ValueError("Pinecone API key not configured")
                if not self.settings.openai_api_key:
                    raise ValueError("OpenAI API key required for embeddings")

                self._vector_search_port = PineconeAdapter(
                    api_key=self.settings.pinecone_api_key,
                    environment=self.settings.pinecone_environment,
                    index_name=self.settings.pinecone_index_name,
                    openai_api_key=self.settings.openai_api_key,
                )
            elif self.settings.vector_db_provider == "weaviate":
                # Import Weaviate adapter when implemented
                # from ...adapters.vector_db.weaviate_adapter import WeaviateAdapter
                # self._vector_search_port = WeaviateAdapter(...)
                raise NotImplementedError("Weaviate adapter not yet implemented")
            elif self.settings.vector_db_provider == "chroma":
                # Import ChromaDB adapter when implemented
                # from ...adapters.vector_db.chroma_adapter import ChromaAdapter
                # self._vector_search_port = ChromaAdapter(...)
                raise NotImplementedError("ChromaDB adapter not yet implemented")
            else:
                raise ValueError(
                    f"Unsupported vector DB provider: {self.settings.vector_db_provider}"
                )

        return self._vector_search_port

    def question_repository_port(self, session: AsyncSession) -> QuestionRepositoryPort:
        """Get question repository port implementation.

        Args:
            session: Async database session

        Returns:
            Configured question repository
        """
        return PostgreSQLQuestionRepository(session)

    def candidate_repository_port(self, session: AsyncSession) -> CandidateRepositoryPort:
        """Get candidate repository port implementation.

        Args:
            session: Async database session

        Returns:
            Configured candidate repository
        """
        return PostgreSQLCandidateRepository(session)

    def interview_repository_port(self, session: AsyncSession) -> InterviewRepositoryPort:
        """Get interview repository port implementation.

        Args:
            session: Async database session

        Returns:
            Configured interview repository
        """
        return PostgreSQLInterviewRepository(session)

    def answer_repository_port(self, session: AsyncSession) -> AnswerRepositoryPort:
        """Get answer repository port implementation.

        Args:
            session: Async database session

        Returns:
            Configured answer repository
        """
        return PostgreSQLAnswerRepository(session)

    def cv_analysis_repository_port(
        self, session: AsyncSession
    ) -> CVAnalysisRepositoryPort:
        """Get CV analysis repository port implementation.

        Args:
            session: Async database session

        Returns:
            Configured CV analysis repository
        """
        return PostgreSQLCVAnalysisRepository(session)

    def cv_analyzer_port(self) -> CVAnalyzerPort:
        """Get CV analyzer port implementation.

        Returns:
            Configured CV analyzer

        Raises:
            NotImplementedError: Real implementation pending
        """
        if self.settings.use_mock_adapters:
            return MockCVAnalyzerAdapter()
        else:
            # TODO: Implement real CV analyzer
            # from ...adapters.cv_processing.spacy_cv_analyzer import SpacyCVAnalyzer
            # return SpacyCVAnalyzer(llm_port=self.llm_port())
            raise NotImplementedError("Real CV analyzer not yet implemented")

    def speech_to_text_port(self) -> SpeechToTextPort:
        """Get speech-to-text port implementation.

        Returns:
            Configured STT service

        Raises:
            NotImplementedError: Implementation pending
        """
        if self._stt_port is None:
            # Use mock adapter if configured
            if self.settings.use_mock_adapters:
                self._stt_port = MockSTTAdapter()
            else:
                # TODO: Implement Azure STT adapter
                # from ...adapters.speech.azure_stt_adapter import AzureSTTAdapter
                # self._stt_port = AzureSTTAdapter(
                #     api_key=self.settings.azure_speech_key,
                #     region=self.settings.azure_speech_region,
                # )
                raise NotImplementedError("Speech-to-text adapter not yet implemented")

        return self._stt_port

    def text_to_speech_port(self) -> TextToSpeechPort:
        """Get text-to-speech port implementation.

        Returns:
            Configured TTS service

        Raises:
            NotImplementedError: Implementation pending
        """
        if self._tts_port is None:
            # Use mock adapter if configured
            if self.settings.use_mock_adapters:
                self._tts_port = MockTTSAdapter()
            else:
                # TODO: Implement Edge TTS adapter
                # from ...adapters.speech.edge_tts_adapter import EdgeTTSAdapter
                # self._tts_port = EdgeTTSAdapter()
                raise NotImplementedError("Text-to-speech adapter not yet implemented")

        return self._tts_port

    def analytics_port(self) -> AnalyticsPort:
        """Get analytics port implementation.

        Returns:
            Configured analytics service

        Raises:
            NotImplementedError: Real implementation pending
        """
        if self.settings.use_mock_adapters:
            return MockAnalyticsAdapter()
        else:
            # TODO: Implement real analytics service
            # from ...adapters.analytics.analytics_adapter import AnalyticsAdapter
            # return AnalyticsAdapter(database_url=self.settings.database_url)
            raise NotImplementedError("Real analytics adapter not yet implemented")


@lru_cache
def get_container() -> Container:
    """Get cached container instance.

    Returns:
        Container instance with all dependencies configured
    """
    settings = get_settings()
    return Container(settings)
