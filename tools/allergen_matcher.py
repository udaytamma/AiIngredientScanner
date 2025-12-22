"""Allergen matching tool for user-specific warnings.

Cross-references ingredient data against user's declared
allergies to identify potential allergen matches.
"""

from config.logging_config import get_logger
from state.schema import IngredientData, UserProfile


logger = get_logger(__name__)

# Common allergen synonyms and related terms
ALLERGEN_SYNONYMS: dict[str, list[str]] = {
    "milk": ["dairy", "lactose", "casein", "whey", "lactalbumin"],
    "egg": ["albumin", "lysozyme", "mayonnaise", "lecithin"],
    "peanut": ["arachis", "groundnut", "peanut oil"],
    "tree nut": ["almond", "cashew", "walnut", "hazelnut", "pistachio", "macadamia"],
    "soy": ["soya", "soybean", "lecithin", "tofu"],
    "wheat": ["gluten", "flour", "semolina", "durum", "spelt"],
    "fish": ["cod", "salmon", "tuna", "anchovy", "fish oil"],
    "shellfish": ["shrimp", "crab", "lobster", "prawn", "crustacean"],
    "sesame": ["sesame oil", "tahini", "sesame seed"],
    "sulfite": ["sulfur dioxide", "sodium sulfite", "metabisulfite"],
    "fragrance": ["parfum", "perfume", "aroma", "essential oil"],
    "paraben": ["methylparaben", "propylparaben", "butylparaben"],
    "formaldehyde": ["formalin", "dmdm hydantoin", "imidazolidinyl urea"],
}


def get_allergen_terms(allergy: str) -> list[str]:
    """Get all terms associated with an allergy.

    Args:
        allergy: User-declared allergy.

    Returns:
        List of terms to match against ingredients.
    """
    allergy_lower = allergy.lower().strip()
    terms = [allergy_lower]

    # Add synonyms if known
    for key, synonyms in ALLERGEN_SYNONYMS.items():
        if allergy_lower == key or allergy_lower in synonyms:
            terms.extend([key] + synonyms)

    return list(set(terms))


def check_allergen_match(
    ingredient: IngredientData,
    user_profile: UserProfile,
) -> tuple[bool, str | None]:
    """Check if an ingredient matches any user allergies.

    Args:
        ingredient: Ingredient data to check.
        user_profile: User profile with allergies.

    Returns:
        Tuple of (is_match, matched_allergy or None).
    """
    if not user_profile["allergies"]:
        return False, None

    # Build searchable text from ingredient data
    search_text = " ".join([
        ingredient["name"].lower(),
        " ".join(ingredient["aliases"]).lower(),
        ingredient["category"].lower(),
        ingredient["safety_notes"].lower(),
    ])

    # Check each user allergy
    for allergy in user_profile["allergies"]:
        terms = get_allergen_terms(allergy)

        for term in terms:
            if term in search_text:
                logger.info(
                    f"Allergen match: '{ingredient['name']}' "
                    f"matches allergy '{allergy}' via term '{term}'"
                )
                return True, allergy

    return False, None


def find_all_allergen_matches(
    ingredients: list[IngredientData],
    user_profile: UserProfile,
) -> list[dict[str, str]]:
    """Find all allergen matches across ingredients.

    Args:
        ingredients: List of ingredient data.
        user_profile: User profile with allergies.

    Returns:
        List of match records with ingredient and allergy.
    """
    matches = []

    for ingredient in ingredients:
        is_match, allergy = check_allergen_match(ingredient, user_profile)
        if is_match and allergy:
            matches.append({
                "ingredient": ingredient["name"],
                "allergy": allergy,
            })

    logger.info(f"Found {len(matches)} allergen matches")
    return matches
