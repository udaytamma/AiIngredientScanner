"""Session management service using Redis.

Provides session storage for user profiles and analysis history.
"""

import json
import uuid
from typing import Any

import redis

from config.settings import get_settings
from config.logging_config import get_logger
from state.schema import UserProfile, SkinType, ExpertiseLevel


logger = get_logger(__name__)


def get_redis_client() -> redis.Redis | None:
    """Get Redis client if configured.

    Returns:
        Redis client or None if not configured.
    """
    settings = get_settings()

    if not settings.is_configured("redis"):
        logger.warning("Redis not configured, sessions will not persist")
        return None

    try:
        client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5,
        )
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def generate_session_id() -> str:
    """Generate a unique session ID.

    Returns:
        UUID-based session ID.
    """
    return str(uuid.uuid4())


def save_user_profile(session_id: str, profile: UserProfile) -> bool:
    """Save user profile to Redis.

    Args:
        session_id: Session identifier.
        profile: User profile to save.

    Returns:
        True if saved successfully.
    """
    client = get_redis_client()
    if not client:
        return False

    try:
        key = f"session:{session_id}:profile"
        data = {
            "allergies": profile["allergies"],
            "skin_type": profile["skin_type"].value,
            "expertise": profile["expertise"].value,
        }
        client.setex(key, 86400, json.dumps(data))  # 24 hour expiry
        logger.info(f"Saved profile for session {session_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save profile: {e}")
        return False


def load_user_profile(session_id: str) -> UserProfile | None:
    """Load user profile from Redis.

    Args:
        session_id: Session identifier.

    Returns:
        UserProfile if found, None otherwise.
    """
    client = get_redis_client()
    if not client:
        return None

    try:
        key = f"session:{session_id}:profile"
        data = client.get(key)

        if not data:
            return None

        parsed = json.loads(data)
        return UserProfile(
            allergies=parsed["allergies"],
            skin_type=SkinType(parsed["skin_type"]),
            expertise=ExpertiseLevel(parsed["expertise"]),
        )
    except Exception as e:
        logger.error(f"Failed to load profile: {e}")
        return None


def save_analysis_result(
    session_id: str,
    product_name: str,
    result: dict[str, Any],
) -> bool:
    """Save analysis result to history.

    Args:
        session_id: Session identifier.
        product_name: Product that was analyzed.
        result: Analysis result data.

    Returns:
        True if saved successfully.
    """
    client = get_redis_client()
    if not client:
        return False

    try:
        key = f"session:{session_id}:history"
        entry = json.dumps({
            "product_name": product_name,
            "timestamp": str(uuid.uuid1().time),
            "result_summary": result.get("summary", ""),
        })
        client.lpush(key, entry)
        client.ltrim(key, 0, 9)  # Keep last 10 analyses
        client.expire(key, 86400)
        return True
    except Exception as e:
        logger.error(f"Failed to save analysis result: {e}")
        return False


def get_analysis_history(session_id: str) -> list[dict]:
    """Get analysis history for a session.

    Args:
        session_id: Session identifier.

    Returns:
        List of past analysis summaries.
    """
    client = get_redis_client()
    if not client:
        return []

    try:
        key = f"session:{session_id}:history"
        entries = client.lrange(key, 0, 9)
        return [json.loads(e) for e in entries]
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return []
