"""Application settings with environment variable loading."""

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        google_cloud_project: GCP project ID for Vertex AI.
        google_application_credentials: Path to service account JSON.
        qdrant_url: Qdrant Cloud cluster URL.
        qdrant_api_key: Qdrant API key.
        redis_url: Redis connection string.
        langchain_api_key: LangSmith API key.
        langchain_tracing_v2: Enable LangSmith tracing.
        langchain_project: LangSmith project name.
        log_level: Logging level.
        max_retries: Max retry attempts for critic loop.
    """

    # Google Generative AI (Gemini API - same approach as EmailAssistant)
    google_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.0-flash")

    # Google Cloud / Vertex AI (preserved for future use)
    google_cloud_project: str = Field(default="")
    google_application_credentials: Optional[str] = Field(default=None)

    # Qdrant
    qdrant_url: str = Field(default="")
    qdrant_api_key: str = Field(default="")

    # Redis
    redis_url: str = Field(default="")

    # LangSmith
    langchain_api_key: str = Field(default="")
    langchain_tracing_v2: bool = Field(default=True)
    langchain_project: str = Field(default="ingredient-analyzer")

    # App settings
    log_level: str = Field(default="INFO")
    max_retries: int = Field(default=2)

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def is_configured(self, service: str) -> bool:
        """Check if a service has required configuration.

        Args:
            service: Service name (qdrant, redis, vertexai, langsmith).

        Returns:
            True if service is configured, False otherwise.
        """
        checks = {
            "qdrant": bool(self.qdrant_url and self.qdrant_api_key),
            "redis": bool(self.redis_url),
            "genai": bool(self.google_api_key),  # Google Generative AI (current)
            "vertexai": bool(self.google_cloud_project),  # Vertex AI (preserved for future)
            "langsmith": bool(self.langchain_api_key),
        }
        return checks.get(service.lower(), False)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance with loaded configuration.
    """
    return Settings()
