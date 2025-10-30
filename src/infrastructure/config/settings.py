"""Application settings using Pydantic."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    This uses Pydantic for validation and type safety.
    """

    # Application
    app_name: str = "Elios AI Interview Service"
    app_version: str = "0.1.0"
    environment: str = "development"  # development, staging, production
    debug: bool = True

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # LLM Provider Selection
    llm_provider: str = "openai"  # openai, claude, llama

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7

    # Anthropic Claude Configuration (alternative)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Vector Database Selection
    vector_db_provider: str = "pinecone"  # pinecone, weaviate, chroma

    # Pinecone Configuration
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "elios-interviews"

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "elios"
    postgres_password: str = ""
    postgres_db: str = "elios_interviews"

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Speech Services
    azure_speech_key: Optional[str] = None
    azure_speech_region: str = "eastus"

    # File Storage
    upload_dir: str = "./uploads"
    cv_dir: str = "./uploads/cvs"
    audio_dir: str = "./uploads/audio"

    # Interview Configuration
    max_questions_per_interview: int = 10
    min_passing_score: float = 60.0
    question_timeout_seconds: int = 300  # 5 minutes per question

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()
