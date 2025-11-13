"""Application settings using Pydantic."""

import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
# env_path = find_dotenv()
# print(f"✅ .env file found: {env_path if env_path else 'None'}")
#
# load_dotenv(env_path)


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
    api_prefix: str = "/api"

    # LLM Provider Selection
    llm_provider: str = "openai"  # openai, claude, llama

    # OpenAI Configuration
    openai_api_key: str | None = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7

    # Azure OpenAI Configuration (alternative to standard OpenAI)
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None  # e.g., "https://your-resource.openai.azure.com/"
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment_name: str | None = None  # Deployment name, not model name
    use_azure_openai: bool = False  # Flag to enable Azure OpenAI

    # Anthropic Claude Configuration (alternative)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Vector Database Selection
    vector_db_provider: str = "pinecone"  # pinecone, weaviate, chroma

    # Pinecone Configuration
    pinecone_api_key: str | None = None
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "elios-interviews"

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "elios"
    postgres_password: str = ""
    postgres_db: str = "elios_interviews"
    database_url: str | None = None  # Full DATABASE_URL from environment

    @property
    def async_database_url(self) -> str:
        """Generate async PostgreSQL connection URL.

        Converts postgresql:// to postgresql+asyncpg:// for async support.
        Strips out sslmode and channel_binding parameters (not supported by asyncpg).
        If DATABASE_URL is set in environment, use that; otherwise construct from parts.

        Note: For Neon and other cloud PostgreSQL providers, asyncpg handles SSL
        automatically - no explicit SSL parameters needed.
        """
        # First check if DATABASE_URL is provided directly
        db_url = self.database_url or os.getenv("DATABASE_URL")

        if db_url:
            # Convert postgresql:// to postgresql+asyncpg://
            db_url = re.sub(r'^postgresql:', 'postgresql+asyncpg:', db_url)

            # Strip out SSL parameters that asyncpg doesn't support in URL format
            # asyncpg handles SSL automatically for cloud providers like Neon
            db_url = re.sub(r'\?sslmode=[^&]*', '', db_url)  # Remove sslmode param
            db_url = re.sub(r'&sslmode=[^&]*', '', db_url)   # Remove if not first param
            db_url = re.sub(r'\?channel_binding=[^&]*', '', db_url)  # Remove channel_binding
            db_url = re.sub(r'&channel_binding=[^&]*', '', db_url)   # Remove if not first param
            db_url = re.sub(r'\?&', '?', db_url)  # Clean up malformed query string
            db_url = re.sub(r'\?$', '', db_url)   # Remove trailing ?

            return db_url

        # Otherwise construct from individual parts
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Speech Services (Azure Speech SDK)
    azure_speech_key: str | None = None
    azure_speech_region: str = "eastus"
    azure_speech_language: str = "en-US"
    azure_speech_voice: str = "en-US-AriaNeural"
    azure_speech_cache_size: int = 128  # LRU cache size for TTS

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

    # WebSocket Configuration
    ws_host: str = "localhost"
    ws_port: int = 8000
    ws_base_url: str = "ws://localhost:8000"

    # Mock Adapters (for development/testing)
    # Individual flags for each adapter - set to False to use real implementations
    use_mock_llm: bool = True
    use_mock_vector_search: bool = True
    use_mock_cv_analyzer: bool = True
    use_mock_stt: bool = True
    use_mock_tts: bool = True
    use_mock_analytics: bool = True

    model_config = SettingsConfigDict(
        env_file=("../.env.local", "../.env", ".env"),  # Try .env.local first, fallback to .env
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def print_loaded_env_file(self):
        for env_file in self.model_config["env_file"]:
            if Path(env_file).exists():
                print(f"Found {env_file} (will be used if values not already set)")
        print(f"Active environment: {self.environment}")

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

    settings = Settings()
    settings.print_loaded_env_file()

    return settings
