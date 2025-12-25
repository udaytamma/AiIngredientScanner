"""Prompts for the Grounded Search Tool.

The Grounded Search tool uses Gemini with Google Search grounding
to find real-time information about ingredients when the vector
database lacks sufficient data.
"""

# =============================================================================
# INGREDIENT RESEARCH PROMPT
# =============================================================================
# Purpose: Research an ingredient's safety profile using Google Search
#          grounding for up-to-date information.
#
# Required format variables:
#   - ingredient_name: Name of the ingredient to research
#
# Expected response format (structured for parsing):
#   INGREDIENT_NAME: [name]
#   PURPOSE: [purpose/function]
#   SAFETY_RATING: [1-10, 10 being safest]
#   CONCERNS: [simple language concerns]
#   RECOMMENDATION: [usage recommendation]
#   ALLERGY_RISK_FLAG: [High/Low]
#   ALLERGY_POTENTIAL: [affected skin types/conditions]
#   ORIGIN: [natural/synthetic/etc]
#   CATEGORY: [Food/Cosmetics/Both]
#   REGULATORY_STATUS: [US FDA and EU status]
#   REGULATORY_BANS: [Yes/No]
# =============================================================================

INGREDIENT_RESEARCH_PROMPT = """Research the ingredient "{ingredient_name}" used in food and/or cosmetics.

CRITICAL: You MUST use EXACTLY "{ingredient_name}" as the INGREDIENT_NAME in your response.
Do NOT substitute, correct, translate, or use an alternative/scientific name.
Use the EXACT name provided in the query, even if you know a different name for it.

Provide data in the structure below only. Do not give additional data.

INGREDIENT_NAME: {ingredient_name}
PURPOSE: [what this ingredient does/its function]
SAFETY_RATING: [1-10 scale, 10 being safest]
CONCERNS: [safety concerns in simple language, no technical terms]
RECOMMENDATION: [usage recommendation]
ALLERGY_RISK_FLAG: [High or Low]
ALLERGY_POTENTIAL: [allergy risk for which types of skin/conditions]
ORIGIN: [natural, synthetic, or semi-synthetic]
CATEGORY: [Food, Cosmetics, or Both]
REGULATORY_STATUS: [US FDA and EU regulatory status]
REGULATORY_BANS: [Yes or No]

Be factual and cite current research."""
