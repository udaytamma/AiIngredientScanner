"""Ingredient lookup tool using Qdrant vector search.

Provides semantic search for ingredients in the vector database,
returning safety metadata and confidence scores.

Uses Google Generative AI SDK (google.genai) for embeddings.
"""

from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config.settings import get_settings
from config.logging_config import get_logger
from state.schema import AllergyRiskFlag, IngredientData


logger = get_logger(__name__)

COLLECTION_NAME = "ingredients"
VECTOR_SIZE = 768  # gemini-embedding-001 with output_dimensionality=768
EMBEDDING_MODEL = "gemini-embedding-001"


def get_qdrant_client() -> QdrantClient:
    """Get configured Qdrant client.

    Returns:
        QdrantClient instance.

    Raises:
        ValueError: If Qdrant is not configured.
    """
    settings = get_settings()
    if not settings.is_configured("qdrant"):
        raise ValueError("Qdrant not configured. Check QDRANT_URL and QDRANT_API_KEY.")

    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )


def ensure_collection_exists(client: QdrantClient) -> None:
    """Ensure the ingredients collection exists.

    Args:
        client: Qdrant client instance.
    """
    collections = client.get_collections()
    exists = any(c.name == COLLECTION_NAME for c in collections.collections)

    if not exists:
        logger.info(f"Creating collection: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )


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


def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text using Google AI Studio.

    Args:
        text: Text to embed.

    Returns:
        Embedding vector (768 dimensions).
    """
    client = _get_genai_client()

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=VECTOR_SIZE,
        ),
    )

    return result.embeddings[0].values


def lookup_ingredient(ingredient_name: str) -> IngredientData | None:
    """Look up ingredient in Qdrant vector database.

    Performs semantic search to find matching ingredients
    and returns safety metadata if confidence is sufficient.

    Args:
        ingredient_name: Name of ingredient to look up.

    Returns:
        IngredientData if found with sufficient confidence, None otherwise.
    """
    try:
        client = get_qdrant_client()
        ensure_collection_exists(client)

        # Get embedding for the ingredient name
        embedding = get_embedding(ingredient_name.lower().strip())

        # Search for similar ingredients (using query_points for newer qdrant-client)
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=1,
        )

        if not results.points:
            logger.info(f"No match found for: {ingredient_name}")
            return None

        top_result = results.points[0]
        confidence = top_result.score

        logger.info(
            f"Found match for '{ingredient_name}': "
            f"score={confidence:.3f}"
        )

        # Extract payload data
        payload = top_result.payload or {}

        # Parse allergy risk flag
        allergy_flag_str = payload.get("allergy_risk_flag", "low").lower()
        allergy_risk_flag = (
            AllergyRiskFlag.HIGH if allergy_flag_str == "high" else AllergyRiskFlag.LOW
        )

        return IngredientData(
            name=payload.get("name", ingredient_name),
            purpose=payload.get("purpose", "Unknown purpose"),
            safety_rating=payload.get("safety_rating", 5),
            concerns=payload.get("concerns", "No known concerns"),
            recommendation=payload.get("recommendation", "Use as directed"),
            allergy_risk_flag=allergy_risk_flag,
            allergy_potential=payload.get("allergy_potential", "Unknown"),
            origin=payload.get("origin", "Unknown"),
            category=payload.get("category", "Unknown"),
            regulatory_status=payload.get("regulatory_status", "Unknown"),
            regulatory_bans=payload.get("regulatory_bans", "No"),
            source="qdrant",
            confidence=confidence,
            # Legacy fields
            aliases=payload.get("aliases", []),
            risk_score=payload.get("risk_score", 0.5),
            safety_notes=payload.get("safety_notes", payload.get("concerns", "")),
        )

    except Exception as e:
        logger.error(f"Error looking up ingredient '{ingredient_name}': {e}")
        return None


def upsert_ingredient(ingredient_data: IngredientData) -> bool:
    """Add or update an ingredient in the database.

    Args:
        ingredient_data: IngredientData to store in Qdrant.

    Returns:
        True if successful, False otherwise.
    """
    try:
        client = get_qdrant_client()
        ensure_collection_exists(client)

        name = ingredient_data["name"]

        # Create embedding from name
        embedding = get_embedding(name.lower())

        # Convert allergy risk flag to string for storage
        allergy_flag = ingredient_data.get("allergy_risk_flag", AllergyRiskFlag.LOW)
        if isinstance(allergy_flag, AllergyRiskFlag):
            allergy_flag_str = allergy_flag.value
        else:
            allergy_flag_str = str(allergy_flag).lower()

        # Create point with all new fields
        point = PointStruct(
            id=hash(name.lower()) % (2**63),  # Convert to int ID based on name
            vector=embedding,
            payload={
                "name": name,
                "purpose": ingredient_data.get("purpose", "Unknown purpose"),
                "safety_rating": ingredient_data.get("safety_rating", 5),
                "concerns": ingredient_data.get("concerns", "No known concerns"),
                "recommendation": ingredient_data.get("recommendation", "Use as directed"),
                "allergy_risk_flag": allergy_flag_str,
                "allergy_potential": ingredient_data.get("allergy_potential", "Unknown"),
                "origin": ingredient_data.get("origin", "Unknown"),
                "category": ingredient_data.get("category", "Unknown"),
                "regulatory_status": ingredient_data.get("regulatory_status", "Unknown"),
                "regulatory_bans": ingredient_data.get("regulatory_bans", "No"),
                # Legacy fields
                "aliases": ingredient_data.get("aliases", []),
                "risk_score": ingredient_data.get("risk_score", 0.5),
                "safety_notes": ingredient_data.get("safety_notes", ""),
            },
        )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point],
        )

        logger.info(f"Upserted ingredient: {name}")
        return True

    except Exception as e:
        logger.error(f"Error upserting ingredient: {e}")
        return False
