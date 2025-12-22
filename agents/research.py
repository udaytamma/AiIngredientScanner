"""Research Agent for ingredient data retrieval.

Fetches ingredient safety data from Qdrant vector database,
falling back to Google Search grounding when confidence is low.

Supports parallel research when ingredient count exceeds BATCH_SIZE.
Each research batch handles up to 3 ingredients sequentially.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.logging_config import get_logger
from state.schema import AllergyRiskFlag, IngredientData, StageTiming, WorkflowState
from tools.ingredient_lookup import lookup_ingredient
from tools.grounded_search import grounded_ingredient_search


logger = get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.7
BATCH_SIZE = 3  # Number of ingredients per research worker


def research_ingredients(state: WorkflowState) -> dict:
    """Research agent node function.

    Fetches data for all ingredients in the raw list.
    Uses parallel processing for large ingredient lists (>3 items).
    Each worker handles up to 3 ingredients sequentially.

    Args:
        state: Current workflow state.

    Returns:
        State update with ingredient_data, routing_history, and stage_timings.
    """
    start_time = time.time()

    raw_ingredients = state["raw_ingredients"]
    ingredient_count = len(raw_ingredients)
    logger.info(f"Researching {ingredient_count} ingredients: {raw_ingredients}")

    routing_history = state.get("routing_history", []).copy()
    routing_history.append("research")

    # Determine if parallel processing is needed
    if ingredient_count <= BATCH_SIZE:
        # Sequential processing for small lists
        ingredient_data = _research_sequential(raw_ingredients)
    else:
        # Parallel processing for larger lists
        ingredient_data = _research_parallel(raw_ingredients)

    elapsed = time.time() - start_time
    logger.info(
        f"Research complete: {len(ingredient_data)} ingredients processed in {elapsed:.2f}s"
    )
    # Debug: Log all ingredient names in ingredient_data
    ingredient_names = [ing.get("name", "UNNAMED") for ing in ingredient_data]
    logger.info(f"Ingredient data contains: {ingredient_names}")

    # Update stage timings
    stage_timings = state.get("stage_timings") or StageTiming(
        research_time=0.0,
        analysis_time=0.0,
        critic_time=0.0,
    )
    stage_timings["research_time"] = elapsed

    return {
        "ingredient_data": ingredient_data,
        "routing_history": routing_history,
        "stage_timings": stage_timings,
    }


def _research_sequential(ingredients: list[str]) -> list[IngredientData]:
    """Research ingredients sequentially.

    Args:
        ingredients: List of ingredient names.

    Returns:
        List of IngredientData for all ingredients.
    """
    results = []
    for ingredient_name in ingredients:
        data = _research_single_ingredient(ingredient_name)
        if data:
            results.append(data)
        else:
            results.append(_create_unknown_ingredient(ingredient_name))
    return results


def _research_parallel(ingredients: list[str]) -> list[IngredientData]:
    """Research ingredients in parallel batches.

    Splits ingredients into batches of BATCH_SIZE and processes
    each batch concurrently using a thread pool.

    Args:
        ingredients: List of ingredient names.

    Returns:
        List of IngredientData for all ingredients, preserving order.
    """
    # Split into batches
    batches = _create_batches(ingredients, BATCH_SIZE)
    num_workers = len(batches)

    logger.info(
        f"Parallel research: {len(ingredients)} ingredients -> "
        f"{num_workers} workers (batch size: {BATCH_SIZE})"
    )

    # Process batches in parallel
    results_by_batch = {}

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all batches
        future_to_batch = {
            executor.submit(_research_batch, batch_idx, batch): batch_idx
            for batch_idx, batch in enumerate(batches)
        }

        # Collect results as they complete
        for future in as_completed(future_to_batch):
            batch_idx = future_to_batch[future]
            try:
                batch_results = future.result()
                results_by_batch[batch_idx] = batch_results
                logger.debug(
                    f"Batch {batch_idx + 1}/{num_workers} complete: "
                    f"{len(batch_results)} ingredients"
                )
            except Exception as e:
                logger.error(f"Batch {batch_idx} failed: {e}")
                # Create unknown records for failed batch
                results_by_batch[batch_idx] = [
                    _create_unknown_ingredient(name)
                    for name in batches[batch_idx]
                ]

    # Reassemble results in original order
    all_results = []
    for batch_idx in range(num_workers):
        all_results.extend(results_by_batch.get(batch_idx, []))

    return all_results


def _create_batches(items: list, batch_size: int) -> list[list]:
    """Split a list into batches of specified size.

    Args:
        items: List to split.
        batch_size: Maximum items per batch.

    Returns:
        List of batches.
    """
    return [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]


def _research_batch(batch_idx: int, ingredients: list[str]) -> list[IngredientData]:
    """Research a batch of ingredients sequentially.

    Args:
        batch_idx: Batch index for logging.
        ingredients: List of ingredient names in this batch.

    Returns:
        List of IngredientData for the batch.
    """
    logger.debug(f"Worker {batch_idx} starting: {len(ingredients)} ingredients")

    results = []
    for ingredient_name in ingredients:
        data = _research_single_ingredient(ingredient_name)
        if data:
            results.append(data)
        else:
            results.append(_create_unknown_ingredient(ingredient_name))

    return results


def _research_single_ingredient(ingredient_name: str) -> IngredientData | None:
    """Research a single ingredient.

    Attempts Qdrant lookup first, falls back to grounded search
    if confidence is below threshold.

    Args:
        ingredient_name: Name of ingredient to research.

    Returns:
        IngredientData if successful, None otherwise.
    """
    logger.info(f">>> Starting research for: '{ingredient_name}'")

    # Try vector database first
    logger.debug(f"Looking up '{ingredient_name}' in Qdrant")
    result = lookup_ingredient(ingredient_name)

    if result and result["confidence"] >= CONFIDENCE_THRESHOLD:
        logger.info(
            f"Found '{ingredient_name}' in Qdrant "
            f"(confidence: {result['confidence']:.2f})"
        )
        return result

    # Fall back to grounded search
    if result:
        logger.info(
            f"Low confidence ({result['confidence']:.2f}) for '{ingredient_name}', "
            "falling back to Google Search"
        )
    else:
        logger.info(
            f"'{ingredient_name}' not in Qdrant, "
            "falling back to Google Search"
        )

    grounded_result = grounded_ingredient_search(ingredient_name)

    if grounded_result:
        logger.info(f"<<< Found '{ingredient_name}' via Google Search")
        return grounded_result

    logger.warning(f"<<< No data found for '{ingredient_name}' - will use unknown record")
    return None


def _create_unknown_ingredient(ingredient_name: str) -> IngredientData:
    """Create a minimal record for an unknown ingredient.

    Args:
        ingredient_name: Name of the ingredient.

    Returns:
        IngredientData with default values.
    """
    logger.warning(f"Creating unknown record for '{ingredient_name}'")

    return IngredientData(
        name=ingredient_name,
        purpose="Unknown",
        safety_rating=5,  # Moderate safety for unknowns
        concerns="No safety data available for this ingredient.",
        recommendation="Use with caution - ingredient not recognized.",
        allergy_risk_flag=AllergyRiskFlag.LOW,
        allergy_potential="Unknown",
        origin="Unknown",
        category="Unknown",
        regulatory_status="Unknown",
        regulatory_bans="Unknown",
        source="unknown",
        confidence=0.0,
        # Legacy fields
        aliases=[],
        risk_score=0.5,  # Moderate risk for unknowns
        safety_notes="No safety data available for this ingredient.",
    )


def has_research_data(state: WorkflowState) -> bool:
    """Check if state has research data for all ingredients.

    Args:
        state: Current workflow state.

    Returns:
        True if research data exists and covers all ingredients.
    """
    ingredient_data = state.get("ingredient_data", [])
    raw_count = len(state.get("raw_ingredients", []))

    return len(ingredient_data) >= raw_count
