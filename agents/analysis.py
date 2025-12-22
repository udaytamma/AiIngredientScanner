"""Analysis Agent for generating safety reports.

Generates personalized safety analysis using LLM with:
- Adaptive detail level by user expertise (beginner/intermediate/expert)
- Cross-reference with user allergies
- Prominent warnings for allergens
- Self-validation for completeness
"""

import re
import time

import google.genai as genai

from config.settings import get_settings
from config.logging_config import get_logger
from config.gemini_logger import get_gemini_logger
from prompts.analysis_prompts import (
    ANALYSIS_PROMPT,
    TONE_INSTRUCTIONS,
    format_ingredient_summary,
)
from state.schema import (
    AnalysisReport,
    ExpertiseLevel,
    IngredientAssessment,
    IngredientData,
    RiskLevel,
    StageTiming,
    UserProfile,
    WorkflowState,
)
from tools.safety_scorer import (
    calculate_risk_score,
    classify_risk_level,
    calculate_overall_risk,
)
from tools.allergen_matcher import check_allergen_match


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


def analyze_ingredients(state: WorkflowState) -> dict:
    """Analysis agent node function.

    Generates personalized safety report using LLM.

    Intelligence:
    - Adapt detail level by user expertise (beginner/intermediate/expert)
    - Cross-reference with user allergies
    - Generate prominent warnings for allergens
    - Self-validate completeness before returning

    Adaptive Behavior:
    - Beginner: Simple, clear language
    - Expert: Technical details and chemical explanations
    - High-risk ingredients: Bold warnings
    - Allergies: AVOID tags prominently displayed

    Args:
        state: Current workflow state.

    Returns:
        State update with analysis_report and routing_history.
    """
    start_time = time.time()

    ingredient_data = state["ingredient_data"]
    user_profile = state["user_profile"]
    product_name = state.get("product_name", "Unknown Product")

    logger.info(
        f"Analyzing {len(ingredient_data)} ingredients for '{product_name}'"
    )

    routing_history = state.get("routing_history", []).copy()
    routing_history.append("analysis")

    # Generate LLM-based analysis
    llm_analysis = _generate_llm_analysis(ingredient_data, user_profile)

    # Also calculate structured assessments for backward compatibility
    assessments, allergen_warnings, risk_scores = _calculate_assessments(
        ingredient_data, user_profile
    )

    # Parse LLM response to determine overall risk based on:
    # 1. Any AVOID recommendation -> HIGH risk
    # 2. Any banned regulatory status -> HIGH risk
    # 3. Otherwise, average safety rating
    overall_risk, avg_safety_score = _parse_llm_overall_risk(llm_analysis)

    # Create report with LLM summary
    report = AnalysisReport(
        product_name=product_name,
        overall_risk=overall_risk,
        average_safety_score=avg_safety_score,
        summary=llm_analysis,  # LLM-generated analysis replaces old summary
        assessments=assessments,
        allergen_warnings=allergen_warnings,
        expertise_tone=user_profile["expertise"],
    )

    elapsed = time.time() - start_time
    logger.info(
        f"Analysis complete in {elapsed:.2f}s: overall risk={overall_risk.value}, "
        f"{len(allergen_warnings)} allergen warnings"
    )

    # Update stage timings
    stage_timings = state.get("stage_timings") or StageTiming(
        research_time=0.0,
        analysis_time=0.0,
        critic_time=0.0,
    )
    stage_timings["analysis_time"] = stage_timings.get("analysis_time", 0.0) + elapsed

    return {
        "analysis_report": report,
        "critic_feedback": None,  # Clear old feedback so critic re-validates
        "routing_history": routing_history,
        "stage_timings": stage_timings,
    }


def _generate_llm_analysis(
    ingredient_data: list[IngredientData],
    user_profile: UserProfile,
) -> str:
    """Generate LLM-based safety analysis.

    Args:
        ingredient_data: List of ingredient data.
        user_profile: User profile for personalization.

    Returns:
        Formatted analysis string from LLM.
    """
    try:
        client = _get_genai_client()
        settings = get_settings()
        model_name = settings.gemini_model

        # Get expertise level and tone instruction
        expertise = user_profile["expertise"].value
        tone_instruction = TONE_INSTRUCTIONS.get(
            expertise, TONE_INSTRUCTIONS["beginner"]
        )

        # Format skin type
        skin_type = user_profile["skin_type"].value.title()

        # Format allergies list
        allergies = user_profile.get("allergies", [])
        allergies_list = ", ".join(allergies) if allergies else "None specified"

        # Format ingredient summary
        ingredient_summary = format_ingredient_summary(ingredient_data)

        # Build prompt
        prompt = ANALYSIS_PROMPT.format(
            tone_instruction=tone_instruction,
            skin_type=skin_type,
            expertise_level=expertise.title(),
            allergies_list=allergies_list,
            ingredient_summary=ingredient_summary,
        )

        # Call LLM
        start_time = time.time()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        text = response.text
        elapsed = time.time() - start_time

        # Log to Gemini logger
        gemini_logger = get_gemini_logger()
        gemini_logger.log_interaction(
            operation="analyze_ingredients",
            prompt=prompt,
            response=text,
            metadata={
                "model": model_name,
                "latency_seconds": f"{elapsed:.3f}",
                "ingredient_count": len(ingredient_data),
                "expertise_level": expertise,
                "skin_type": skin_type,
            },
        )

        logger.info(f"LLM analysis generated in {elapsed:.2f}s")
        return text

    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        # Fallback to basic summary
        return _generate_fallback_summary(ingredient_data, user_profile)


def _generate_fallback_summary(
    ingredient_data: list[IngredientData],
    user_profile: UserProfile,
) -> str:
    """Generate fallback summary when LLM fails.

    Args:
        ingredient_data: List of ingredient data.
        user_profile: User profile.

    Returns:
        Basic summary string.
    """
    high_risk = [i for i in ingredient_data if i.get("safety_rating", 5) <= 3]
    allergies = user_profile.get("allergies", [])

    summary = f"## Ingredient Analysis\n\n"
    summary += f"Analyzed {len(ingredient_data)} ingredients.\n\n"

    if high_risk:
        summary += f"**Warning:** {len(high_risk)} ingredient(s) with lower safety ratings.\n\n"

    if allergies:
        summary += f"**Allergens to watch:** {', '.join(allergies)}\n\n"

    summary += "## Overall Verdict\n"
    if high_risk:
        summary += "USE WITH CAUTION - Some ingredients require attention.\n"
    else:
        summary += "SAFE TO USE - No major concerns identified.\n"

    return summary


def _parse_llm_overall_risk(llm_analysis: str) -> tuple[RiskLevel, int]:
    """Parse LLM analysis to determine overall risk based on recommendations and bans.

    Rules:
    1. If ANY ingredient has AVOID recommendation -> HIGH risk
    2. If ANY ingredient has banned regulatory status -> HIGH risk
    3. Otherwise, calculate from average safety rating

    Args:
        llm_analysis: The LLM-generated analysis text.

    Returns:
        Tuple of (RiskLevel, average_safety_score).
    """
    # Check for AVOID recommendations in the table
    has_avoid = False
    has_banned = False
    safety_ratings = []

    # Parse table rows - look for | separators
    lines = llm_analysis.split('\n')
    in_table = False

    for line in lines:
        # Check if this is a table data row (not header or separator)
        if '|' in line and not line.strip().startswith('|--') and not line.strip().startswith('| --'):
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]  # Remove empty cells

            if len(cells) >= 5:
                # Skip header row
                if 'Ingredient' in cells[0] or 'Purpose' in cells[1]:
                    in_table = True
                    continue

                if in_table:
                    # Check Recommendation column (usually 5th column, index 4)
                    for cell in cells:
                        cell_upper = cell.upper()
                        if 'AVOID' in cell_upper and 'USE WITH' not in cell_upper:
                            has_avoid = True
                            break

                    # Check for banned in Regulatory Status (usually last column)
                    last_cell = cells[-1].lower() if cells else ""
                    if 'banned' in last_cell or 'prohibited' in last_cell:
                        has_banned = True

                    # Extract safety rating (usually 3rd column)
                    for cell in cells:
                        # Look for patterns like "6/10", "6", etc.
                        match = re.search(r'(\d+)(?:/10)?', cell)
                        if match:
                            rating = int(match.group(1))
                            if 1 <= rating <= 10:
                                safety_ratings.append(rating)
                                break

    # Determine overall risk
    if has_avoid or has_banned:
        avg_rating = sum(safety_ratings) // len(safety_ratings) if safety_ratings else 5
        return RiskLevel.HIGH, avg_rating

    # Calculate average safety rating
    if safety_ratings:
        avg_rating = sum(safety_ratings) // len(safety_ratings)
        # Convert to risk level: 1-3 = HIGH, 4-6 = MEDIUM, 7-10 = LOW
        if avg_rating <= 3:
            return RiskLevel.HIGH, avg_rating
        elif avg_rating <= 6:
            return RiskLevel.MEDIUM, avg_rating
        else:
            return RiskLevel.LOW, avg_rating

    # Fallback
    return RiskLevel.MEDIUM, 5


def _calculate_assessments(
    ingredient_data: list[IngredientData],
    user_profile: UserProfile,
) -> tuple[list[IngredientAssessment], list[str], list[float]]:
    """Calculate structured assessments for backward compatibility.

    Args:
        ingredient_data: List of ingredient data.
        user_profile: User profile.

    Returns:
        Tuple of (assessments, allergen_warnings, risk_scores).
    """
    assessments: list[IngredientAssessment] = []
    allergen_warnings: list[str] = []
    risk_scores: list[float] = []

    for ingredient in ingredient_data:
        # Check allergen match
        is_allergen, matched_allergy = check_allergen_match(
            ingredient, user_profile
        )

        # Calculate risk
        risk_score = calculate_risk_score(ingredient, user_profile)
        risk_level = classify_risk_level(risk_score)
        risk_scores.append(risk_score)

        # Override to HIGH if allergen match
        if is_allergen:
            risk_level = RiskLevel.HIGH

        # Generate rationale
        rationale = _generate_rationale(
            ingredient=ingredient,
            risk_level=risk_level,
            is_allergen=is_allergen,
            matched_allergy=matched_allergy,
            expertise=user_profile["expertise"],
        )

        # Suggest alternatives for high risk
        alternatives = _suggest_alternatives(ingredient, risk_level)

        assessment = IngredientAssessment(
            name=ingredient["name"],
            risk_level=risk_level,
            rationale=rationale,
            is_allergen_match=is_allergen,
            alternatives=alternatives,
        )
        assessments.append(assessment)

        # Create allergen warning if match
        if is_allergen and matched_allergy:
            warning = (
                f"ALLERGEN WARNING: {ingredient['name']} - "
                f"matches your declared sensitivity: {matched_allergy}"
            )
            allergen_warnings.append(warning)

    return assessments, allergen_warnings, risk_scores


def _generate_rationale(
    ingredient: IngredientData,
    risk_level: RiskLevel,
    is_allergen: bool,
    matched_allergy: str | None,
    expertise: ExpertiseLevel,
) -> str:
    """Generate explanation rationale for an ingredient.

    Args:
        ingredient: Ingredient data.
        risk_level: Classified risk level.
        is_allergen: Whether it's an allergen match.
        matched_allergy: The matched allergy name.
        expertise: User expertise level.

    Returns:
        Rationale string adapted to expertise level.
    """
    parts = []

    # Risk explanation based on expertise
    if expertise == ExpertiseLevel.BEGINNER:
        risk_text = {
            RiskLevel.LOW: "This ingredient is generally considered safe.",
            RiskLevel.MEDIUM: "This ingredient has some concerns to be aware of.",
            RiskLevel.HIGH: "This ingredient may pose risks for some users.",
        }
        parts.append(risk_text[risk_level])
    else:
        # Expert level: include technical details
        safety_rating = ingredient.get("safety_rating", 5)
        parts.append(
            f"Risk classification: {risk_level.value.upper()} "
            f"(safety rating: {safety_rating}/10)"
        )

    # Allergen warning
    if is_allergen:
        if expertise == ExpertiseLevel.BEGINNER:
            parts.append(
                f"WARNING: This matches your {matched_allergy} sensitivity!"
            )
        else:
            parts.append(
                f"Allergen alert: Cross-reactivity with declared "
                f"sensitivity to {matched_allergy}."
            )

    # Include concerns
    concerns = ingredient.get("concerns", "")
    if concerns and concerns != "No known concerns":
        if expertise == ExpertiseLevel.BEGINNER:
            # Simplify for beginners
            parts.append(concerns[:200] + ("..." if len(concerns) > 200 else ""))
        else:
            parts.append(concerns)

    return " ".join(parts)


def _suggest_alternatives(
    ingredient: IngredientData,
    risk_level: RiskLevel,
) -> list[str]:
    """Suggest safer alternatives for risky ingredients.

    Args:
        ingredient: Ingredient data.
        risk_level: Risk level classification.

    Returns:
        List of alternative ingredient suggestions.
    """
    if risk_level == RiskLevel.LOW:
        return []

    # Category-based alternatives
    alternatives_map = {
        "preservative": ["tocopherol (vitamin E)", "rosemary extract"],
        "fragrance": ["fragrance-free alternatives", "natural essential oils"],
        "surfactant": ["coco-glucoside", "decyl glucoside"],
        "colorant": ["mineral pigments", "plant-based dyes"],
        "emulsifier": ["lecithin", "cetearyl alcohol"],
        "cosmetics": ["hypoallergenic alternatives"],
        "food": ["organic alternatives"],
    }

    category = ingredient.get("category", "").lower()
    return alternatives_map.get(category, [])


def has_analysis_report(state: WorkflowState) -> bool:
    """Check if state has an analysis report.

    Args:
        state: Current workflow state.

    Returns:
        True if analysis_report exists.
    """
    return state.get("analysis_report") is not None
