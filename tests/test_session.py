"""Tests for session management service."""

from unittest.mock import patch, MagicMock
import json

import pytest

from state.schema import ExpertiseLevel, SkinType, UserProfile
from services.session import (
    generate_session_id,
    save_user_profile,
    load_user_profile,
    get_redis_client,
)


class TestSessionId:
    """Tests for session ID generation."""

    def test_generate_session_id_unique(self) -> None:
        """Test session IDs are unique."""
        id1 = generate_session_id()
        id2 = generate_session_id()
        assert id1 != id2

    def test_generate_session_id_format(self) -> None:
        """Test session ID is UUID format."""
        session_id = generate_session_id()
        assert len(session_id) == 36
        assert session_id.count("-") == 4


class TestRedisClient:
    """Tests for Redis client."""

    @patch("services.session.get_settings")
    def test_get_client_not_configured(
        self, mock_settings: MagicMock
    ) -> None:
        """Test returns None when not configured."""
        mock_settings.return_value.is_configured.return_value = False
        client = get_redis_client()
        assert client is None


class TestUserProfile:
    """Tests for user profile operations."""

    @pytest.fixture
    def sample_profile(self) -> UserProfile:
        """Create sample profile."""
        return UserProfile(
            allergies=["peanut", "fragrance"],
            skin_type=SkinType.SENSITIVE,
            expertise=ExpertiseLevel.BEGINNER,
        )

    @patch("services.session.get_redis_client")
    def test_save_profile_no_redis(
        self,
        mock_client: MagicMock,
        sample_profile: UserProfile,
    ) -> None:
        """Test save returns False when Redis unavailable."""
        mock_client.return_value = None
        result = save_user_profile("test-session", sample_profile)
        assert result is False

    @patch("services.session.get_redis_client")
    def test_save_profile_success(
        self,
        mock_client: MagicMock,
        sample_profile: UserProfile,
    ) -> None:
        """Test successful profile save."""
        mock_redis = MagicMock()
        mock_client.return_value = mock_redis

        result = save_user_profile("test-session", sample_profile)

        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "session:test-session:profile" in call_args[0]

    @patch("services.session.get_redis_client")
    def test_load_profile_no_redis(self, mock_client: MagicMock) -> None:
        """Test load returns None when Redis unavailable."""
        mock_client.return_value = None
        result = load_user_profile("test-session")
        assert result is None

    @patch("services.session.get_redis_client")
    def test_load_profile_not_found(self, mock_client: MagicMock) -> None:
        """Test load returns None when profile not found."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_client.return_value = mock_redis

        result = load_user_profile("test-session")
        assert result is None

    @patch("services.session.get_redis_client")
    def test_load_profile_success(self, mock_client: MagicMock) -> None:
        """Test successful profile load."""
        mock_redis = MagicMock()
        stored_data = json.dumps({
            "allergies": ["milk"],
            "skin_type": "dry",
            "expertise": "expert",
        })
        mock_redis.get.return_value = stored_data
        mock_client.return_value = mock_redis

        result = load_user_profile("test-session")

        assert result is not None
        assert result["allergies"] == ["milk"]
        assert result["skin_type"] == SkinType.DRY
        assert result["expertise"] == ExpertiseLevel.EXPERT
