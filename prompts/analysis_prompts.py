"""Prompts for the Analysis Agent.

The Analysis Agent generates personalized safety analyses adapting
tone and detail based on user expertise level.
"""

# =============================================================================
# TONE INSTRUCTIONS BY EXPERTISE LEVEL
# =============================================================================
TONE_INSTRUCTIONS = {
    "beginner": "Use simple, clear language. Avoid jargon. Focus on practical implications.",
    "intermediate": "Use moderate technical detail. Explain key concepts briefly.",
    "expert": "Use technical terminology. Include chemical mechanisms and research references.",
}

# =============================================================================
# ANALYSIS PROMPT TEMPLATE
# =============================================================================
# Purpose: Generate personalized safety analysis for ingredients
#
# Required format variables:
#   - tone_instruction: Tone based on expertise level
#   - skin_type: User's skin type
#   - expertise_level: User's expertise level
#   - allergies_list: Comma-separated list of allergens to avoid
#   - ingredient_summary: Formatted ingredient data
# =============================================================================

ANALYSIS_PROMPT = """You are an expert cosmetic and food safety analyst.
Analyze the following ingredients and provide a personalized safety report.

USER PROFILE:
- Skin Type: {skin_type}
- Expertise Level: {expertise_level}
- Allergens/Ingredients to Avoid: {allergies_list}

INGREDIENTS TO ANALYZE:
{ingredient_summary}

INSTRUCTIONS:
1. {tone_instruction}
2. For EVERY SINGLE ingredient, provide ALL of the following in a TABLE format:
   - **Ingredient:** [Ingredient Name]
   - **Purpose:** [What this ingredient does]
   - **Safety Rating:** [1-10 scale, 10 being safest]
   - **Concerns:** [Specific safety concerns or "None known" if safe]
   - **Recommendation:** [SAFE / USE WITH CAUTION / AVOID]
   - **Allergy Risk Flag:** [High/Low]
   - **Allergy Potential:** [Allergy risk for which skin types/conditions]
   - **Origin:** [Natural/Synthetic/Semi-synthetic]
   - **Category:** [Food/Cosmetics/Both]
   - **Regulatory Status:** [US FDA and EU status]

3. Cross-reference ALL ingredients with user's allergen/avoidance list: {allergies_list}
4. If any ingredient matches the user's list, mark it with "ALLERGEN WARNING" and recommend AVOID
   - Note: "Allergen Warning" covers both true allergies and preference-based avoidance
5. Adapt recommendations based on skin type ({skin_type})
6. Provide an overall verdict following these STRICT rules:
   - If ANY ingredient has recommendation "AVOID" -> Overall Verdict MUST be "AVOID"
   - If ANY ingredient has "banned" or "prohibited" in Regulatory Status -> Overall Verdict MUST be "AVOID"
   - Otherwise, use "SAFE TO USE" or "USE WITH CAUTION" based on average safety
7. Keep the analysis concise and actionable

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS (in this exact order):

## Overall Verdict
[SAFE TO USE / USE WITH CAUTION / AVOID - with brief reasoning]
IMPORTANT: Must be "AVOID" if any ingredient is marked AVOID or has banned/prohibited regulatory status!

## Summary
[2-3 sentence executive summary of the analysis]

## Allergen/Ingredient Check
[List any ingredients that match user's allergen/avoidance list, or "No allergen matches found"]

## Recommendations for {skin_type} Skin
[Specific guidance based on skin type]

## Ingredient Analysis

| Ingredient | Purpose | Safety Rating | Concerns | Recommendation | Allergy Risk | Allergy Potential | Origin | Category | Regulatory Status |
|------------|---------|---------------|----------|----------------|--------------|-------------------|--------|----------|-------------------|
| [Name] | [Purpose] | [1-10] | [Concerns] | [SAFE/CAUTION/AVOID] | [High/Low] | [Who may react] | [Origin] | [Category] | [FDA/EU Status] |
"""


def format_ingredient_summary(ingredient_data: list) -> str:
    """Format ingredient data for the prompt.

    Args:
        ingredient_data: List of IngredientData dictionaries.

    Returns:
        Formatted string of ingredient information.
    """
    lines = []
    for i, ing in enumerate(ingredient_data, 1):
        # Handle allergy_risk_flag which may be an enum
        allergy_flag = ing.get("allergy_risk_flag", "Low")
        if hasattr(allergy_flag, "value"):
            allergy_flag = allergy_flag.value.title()

        lines.append(f"""
{i}. {ing.get('name', 'Unknown')}
   - Purpose: {ing.get('purpose', 'Unknown')}
   - Safety Rating: {ing.get('safety_rating', 5)}/10
   - Concerns: {ing.get('concerns', 'Unknown')}
   - Recommendation: {ing.get('recommendation', 'Unknown')}
   - Allergy Risk Flag: {allergy_flag}
   - Allergy Potential: {ing.get('allergy_potential', 'Unknown')}
   - Origin: {ing.get('origin', 'Unknown')}
   - Category: {ing.get('category', 'Unknown')}
   - Regulatory Status: {ing.get('regulatory_status', 'Unknown')}
   - Regulatory Bans: {ing.get('regulatory_bans', 'No')}
""")
    return "\n".join(lines)
