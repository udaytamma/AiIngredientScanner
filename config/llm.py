"""Centralized LLM configuration with LangSmith tracing.

Uses langchain-google-genai for Gemini API access, which automatically
integrates with LangSmith tracing when LANGCHAIN_TRACING_V2=true.
"""

import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import get_settings
from config.logging_config import get_logger


logger = get_logger(__name__)


def _ensure_langsmith_env() -> None:
    """Ensure LangSmith environment variables are set from settings.

    LangChain reads these from environment, so we need to set them
    if they're loaded via pydantic settings.
    """
    settings = get_settings()

    if settings.langchain_api_key:
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)

    if settings.langchain_tracing_v2:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

    if settings.langchain_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)


@lru_cache
def get_llm() -> ChatGoogleGenerativeAI:
    """Get configured LLM instance with LangSmith tracing.

    Uses ChatGoogleGenerativeAI which integrates with LangChain's
    tracing infrastructure, enabling LangSmith observability.

    Returns:
        ChatGoogleGenerativeAI instance.

    Raises:
        ValueError: If Google API key is not configured.
    """
    settings = get_settings()

    if not settings.google_api_key:
        raise ValueError("Google API key not configured. Check GOOGLE_API_KEY.")

    # Ensure LangSmith env vars are set
    _ensure_langsmith_env()

    logger.info(
        f"Initializing LLM: model={settings.gemini_model}, "
        f"langsmith_enabled={settings.langchain_tracing_v2}"
    )

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.1,  # Low temperature for consistent analysis
    )


def invoke_llm(prompt: str, run_name: str = "llm_call") -> str:
    """Invoke LLM with a prompt and return the response text.

    This is a convenience wrapper that handles the LangChain message format
    and extracts the text response.

    Args:
        prompt: The prompt text to send to the LLM.
        run_name: Name for the LangSmith trace run.

    Returns:
        The LLM response text.
    """
    llm = get_llm()

    # LangChain uses message format
    from langchain_core.messages import HumanMessage

    response = llm.invoke(
        [HumanMessage(content=prompt)],
        config={"run_name": run_name}
    )

    # response.content can be a str or a list of content parts
    # (multipart response from Gemini). Normalize to str.
    content = response.content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        content = "\n".join(parts)

    return content
