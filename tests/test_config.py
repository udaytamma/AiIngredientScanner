"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from config.settings import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self) -> None:
        """Test that defaults are applied when env vars missing."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.log_level == "INFO"
            assert settings.max_retries == 2
            assert settings.langchain_tracing_v2 is True

    def test_is_configured_qdrant_false(self) -> None:
        """Test Qdrant not configured when missing credentials."""
        settings = Settings(qdrant_url="", qdrant_api_key="")
        assert settings.is_configured("qdrant") is False

    def test_is_configured_qdrant_true(self) -> None:
        """Test Qdrant configured when credentials present."""
        settings = Settings(
            qdrant_url="https://test.qdrant.io",
            qdrant_api_key="test-key",
        )
        assert settings.is_configured("qdrant") is True

    def test_is_configured_redis_false(self) -> None:
        """Test Redis not configured when URL missing."""
        settings = Settings(redis_url="")
        assert settings.is_configured("redis") is False

    def test_is_configured_redis_true(self) -> None:
        """Test Redis configured when URL present."""
        settings = Settings(redis_url="redis://localhost:6379")
        assert settings.is_configured("redis") is True

    def test_is_configured_vertexai_false(self) -> None:
        """Test Vertex AI not configured when project missing."""
        settings = Settings(google_cloud_project="")
        assert settings.is_configured("vertexai") is False

    def test_is_configured_vertexai_true(self) -> None:
        """Test Vertex AI configured when project present."""
        settings = Settings(google_cloud_project="my-project")
        assert settings.is_configured("vertexai") is True

    def test_is_configured_langsmith_false(self) -> None:
        """Test LangSmith not configured when API key missing."""
        settings = Settings(langchain_api_key="")
        assert settings.is_configured("langsmith") is False

    def test_is_configured_langsmith_true(self) -> None:
        """Test LangSmith configured when API key present."""
        settings = Settings(langchain_api_key="lsv2_test_key")
        assert settings.is_configured("langsmith") is True

    def test_is_configured_unknown_service(self) -> None:
        """Test unknown service returns False."""
        settings = Settings()
        assert settings.is_configured("unknown") is False

    def test_env_loading(self) -> None:
        """Test settings load from environment variables."""
        env_vars = {
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "QDRANT_URL": "https://test.qdrant.io",
            "QDRANT_API_KEY": "qdrant-key",
            "REDIS_URL": "redis://localhost:6379",
            "LANGCHAIN_API_KEY": "langsmith-key",
            "LOG_LEVEL": "DEBUG",
            "MAX_RETRIES": "5",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.google_cloud_project == "test-project"
            assert settings.qdrant_url == "https://test.qdrant.io"
            assert settings.log_level == "DEBUG"
            assert settings.max_retries == 5


class TestGetSettings:
    """Test get_settings function."""

    def test_returns_settings_instance(self) -> None:
        """Test that get_settings returns a Settings object."""
        # Clear cache to ensure fresh instance
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_caching(self) -> None:
        """Test that get_settings returns cached instance."""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
