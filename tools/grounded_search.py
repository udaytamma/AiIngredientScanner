"""Grounded search tool using Google AI Studio with Google Search.

Provides real-time ingredient information when vector database
lacks sufficient data, using Gemini with search grounding.

Uses Google Generative AI SDK (google.genai) with Google Search tool.
After successful search, saves results to Qdrant for future lookups.

Note: This module uses google.genai directly (not langchain) because
it requires the GoogleSearch grounding tool which is not available
in langchain-google-genai. LangSmith tracing is added manually.
"""

import os
import time

from google import genai
from google.genai import types
from langsmith import traceable

from config.settings import get_settings
from config.logging_config import get_logger
from config.gemini_logger import get_gemini_logger
from prompts.grounded_search_prompts import INGREDIENT_RESEARCH_PROMPT
from state.schema import AllergyRiskFlag, IngredientData


logger = get_logger(__name__)


def _get_genai_client() -> genai.Client:
    """Get configured Google GenAI client.

    Returns:
        Configured genai.Client instance.

    Raises:
        ValueError: If Google API key is not configured.
    """
    settings = get_settings()
    if not settings.is_configured("genai"):
        raise ValueError("Google AI not configured. Check GOOGLE_API_KEY.")

    return genai.Client(api_key=settings.google_api_key)


def _ensure_langsmith_env() -> None:
    """Ensure LangSmith environment variables are set for tracing."""
    settings = get_settings()
    if settings.langchain_api_key:
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
    if settings.langchain_tracing_v2:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    if settings.langchain_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)


def _safety_rating_to_risk_score(safety_rating: int) -> float:
    """Convert safety rating (1-10, 10=safest) to risk score (0-1, 1=highest risk).

    Args:
        safety_rating: Safety rating from 1-10.

    Returns:
        Risk score from 0.0 to 1.0.
    """
    # Invert: safety 10 -> risk 0, safety 1 -> risk 0.9
    clamped = max(1, min(10, safety_rating))
    return round((10 - clamped) / 10, 2)


@traceable(name="grounded_ingredient_search")
def grounded_ingredient_search(ingredient_name: str) -> IngredientData | None:
    """Search for ingredient information using Google Search grounding.

    Uses Gemini with Google Search to find current safety information
    about an ingredient when not available in the vector database.
    After successful search, saves results to Qdrant for future lookups.

    Args:
        ingredient_name: Name of ingredient to research.

    Returns:
        IngredientData with search results, or None on failure.
    """
    # Ensure LangSmith tracing is configured
    _ensure_langsmith_env()

    try:
        client = _get_genai_client()
        settings = get_settings()
        model_name = settings.gemini_model

        # Configure grounding with Google Search
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        config = types.GenerateContentConfig(
            tools=[grounding_tool]
        )

        # Use centralized prompt template
        prompt = INGREDIENT_RESEARCH_PROMPT.format(ingredient_name=ingredient_name)

        start_time = time.time()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        # response.text can raise ValueError if no text parts exist
        try:
            text = response.text
        except (ValueError, AttributeError):
            text = ""
            # Fallback: extract from response parts
            try:
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            text += part.text
            except Exception:
                pass

        if not text:
            logger.warning(f"Empty response from Gemini for '{ingredient_name}'")
            return None

        elapsed = time.time() - start_time

        # Log to Gemini logger
        gemini_logger = get_gemini_logger()
        gemini_logger.log_interaction(
            operation="grounded_ingredient_search",
            prompt=prompt,
            response=text,
            metadata={
                "model": model_name,
                "latency_seconds": f"{elapsed:.3f}",
                "ingredient": ingredient_name,
                "source": "google_ai_studio_grounded_search",
            },
        )

        logger.info(f"Grounded search for '{ingredient_name}' completed")

        # Parse the response
        ingredient_data = _parse_search_response(ingredient_name, text)

        # Save to Qdrant for future lookups (non-blocking)
        try:
            _save_to_qdrant(ingredient_data)
        except Exception as save_err:
            logger.warning(f"Failed to save '{ingredient_name}' to Qdrant: {save_err}")
            # Continue anyway - we still have the data

        return ingredient_data

    except Exception as e:
        logger.error(f"Grounded search error for '{ingredient_name}': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def _parse_search_response(
    ingredient_name: str,
    response_text: str,
) -> IngredientData:
    """Parse structured response from grounded search.

    Args:
        ingredient_name: Original ingredient name.
        response_text: Raw response from Gemini.

    Returns:
        Parsed IngredientData with new schema fields.
    """
    lines = response_text.strip().split("\n")
    data: dict[str, str] = {}

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            # Normalize key: replace spaces with underscores, uppercase
            normalized_key = key.strip().upper().replace(" ", "_")
            data[normalized_key] = value.strip()

    # Extract new fields with defaults
    # IMPORTANT: Always use the original ingredient_name as the canonical name
    # to prevent duplicates when the LLM returns a different ingredient name
    name = ingredient_name
    purpose = data.get("PURPOSE", "Unknown purpose")
    concerns = data.get("CONCERNS", "No known concerns")
    recommendation = data.get("RECOMMENDATION", "Use as directed")
    allergy_potential = data.get("ALLERGY_POTENTIAL", "Unknown")
    origin = data.get("ORIGIN", "Unknown")
    category = data.get("CATEGORY", "Unknown")
    regulatory_status = data.get("REGULATORY_STATUS", "Unknown")
    regulatory_bans = data.get("REGULATORY_BANS", "No")

    # Parse safety rating (1-10)
    try:
        safety_rating = int(data.get("SAFETY_RATING", "5"))
        safety_rating = max(1, min(10, safety_rating))
    except ValueError:
        safety_rating = 5

    # Parse allergy risk flag
    allergy_flag_str = data.get("ALLERGY_RISK_FLAG", "Low").lower()
    allergy_risk_flag = (
        AllergyRiskFlag.HIGH if allergy_flag_str == "high" else AllergyRiskFlag.LOW
    )

    # Calculate legacy risk_score from safety_rating
    risk_score = _safety_rating_to_risk_score(safety_rating)

    return IngredientData(
        name=name,
        purpose=purpose,
        safety_rating=safety_rating,
        concerns=concerns,
        recommendation=recommendation,
        allergy_risk_flag=allergy_risk_flag,
        allergy_potential=allergy_potential,
        origin=origin,
        category=category,
        regulatory_status=regulatory_status,
        regulatory_bans=regulatory_bans,
        source="google_search",
        confidence=0.8,
        # Legacy fields for backward compatibility
        aliases=[],
        risk_score=risk_score,
        safety_notes=concerns,
    )


def _save_to_qdrant(ingredient_data: IngredientData) -> None:
    """Save ingredient data to Qdrant for future lookups.

    Args:
        ingredient_data: Parsed ingredient data to save.
    """
    try:
        from tools.ingredient_lookup import upsert_ingredient

        success = upsert_ingredient(ingredient_data)

        if success:
            logger.info(
                f"Saved '{ingredient_data['name']}' to Qdrant for future lookups"
            )
        else:
            logger.warning(
                f"Failed to save '{ingredient_data['name']}' to Qdrant"
            )

    except Exception as e:
        logger.error(f"Error saving to Qdrant: {e}")
