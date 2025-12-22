"""Safety scoring tool for ingredient risk assessment.

Combines ingredient baseline risk with user-specific factors
to produce personalized risk scores.
"""

from config.logging_config import get_logger
from state.schema import (
    IngredientData,
    RiskLevel,
    UserProfile,
    SkinType,
)


logger = get_logger(__name__)

# Risk modifiers for skin types
SKIN_TYPE_RISK_MODIFIERS: dict[SkinType, dict[str, float]] = {
    SkinType.SENSITIVE: {
        "fragrance": 0.3,
        "preservative": 0.2,
        "colorant": 0.15,
        "surfactant": 0.2,
    },
    SkinType.DRY: {
        "surfactant": 0.15,
        "alcohol": 0.2,
    },
    SkinType.OILY: {
        "emollient": 0.1,
        "oil": 0.1,
    },
    SkinType.NORMAL: {},
    SkinType.COMBINATION: {},
}


def calculate_risk_score(
    ingredient: IngredientData,
    user_profile: UserProfile,
) -> float:
    """Calculate personalized risk score for an ingredient.

    Combines the ingredient's baseline risk with user-specific
    factors like skin type to produce a personalized score.

    Args:
        ingredient: Ingredient data with baseline risk.
        user_profile: User profile for personalization.

    Returns:
        Risk score from 0.0 to 1.0.
    """
    base_risk = ingredient["risk_score"]

    # Apply skin type modifier
    skin_modifiers = SKIN_TYPE_RISK_MODIFIERS.get(
        user_profile["skin_type"],
        {},
    )

    category = ingredient["category"].lower()
    modifier = skin_modifiers.get(category, 0.0)

    # Calculate final risk
    final_risk = min(1.0, base_risk + modifier)

    logger.debug(
        f"Risk for {ingredient['name']}: "
        f"base={base_risk:.2f}, modifier={modifier:.2f}, final={final_risk:.2f}"
    )

    return final_risk


def classify_risk_level(risk_score: float) -> RiskLevel:
    """Classify risk score into risk level.

    Args:
        risk_score: Numeric risk score (0.0 to 1.0).

    Returns:
        Classified risk level.
    """
    if risk_score < 0.3:
        return RiskLevel.LOW
    elif risk_score < 0.6:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


def calculate_overall_risk(
    ingredient_scores: list[float],
) -> RiskLevel:
    """Calculate overall product risk from ingredient scores.

    Uses a weighted approach: highest risk ingredient has most
    influence, with consideration for number of risky ingredients.

    Args:
        ingredient_scores: List of individual ingredient risk scores.

    Returns:
        Overall product risk level.
    """
    if not ingredient_scores:
        return RiskLevel.LOW

    max_risk = max(ingredient_scores)
    avg_risk = sum(ingredient_scores) / len(ingredient_scores)

    # Weight: 70% max risk, 30% average risk
    combined = (0.7 * max_risk) + (0.3 * avg_risk)

    return classify_risk_level(combined)
