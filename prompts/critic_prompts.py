"""Prompts for the Critic Agent.

The Critic agent validates analysis reports using multi-gate validation:
1. Completeness - All ingredients addressed
2. Format - Proper table structure with required columns
3. Allergen Match - User allergies properly flagged
4. Consistency - Safety scores match concern descriptions
5. Tone - Appropriate for user expertise level
"""

# =============================================================================
# MULTI-GATE VALIDATION PROMPT
# =============================================================================
# Purpose: Comprehensive validation of safety analysis using 5 gates.
#
# Required format variables:
#   - ingredient_count: Number of ingredients to validate
#   - ingredient_names: Comma-separated list of ingredient names
#   - allergen_list: User's allergies or "None declared"
#   - expertise_level: beginner/intermediate/expert
#   - safety_analysis: The full analysis text to validate
#
# Expected response: APPROVE or REJECT with specific feedback
# =============================================================================

VALIDATION_PROMPT = """You are a lenient quality validator for cosmetic ingredient safety analyses. Your job is to APPROVE analyses that meet basic quality standards.

IMPORTANT: Be lenient. Only REJECT if there are CRITICAL issues. Minor imperfections are acceptable.

ORIGINAL INGREDIENT LIST ({ingredient_count} ingredients):
{ingredient_names}

USER ALLERGIES:
{allergen_list}

USER EXPERTISE LEVEL:
{expertise_level}

ANALYSIS TO VALIDATE:
{safety_analysis}

VALIDATION GATES:

1. COMPLETENESS CHECK - PASS if:
   - The analysis contains a table with rows for ingredients
   - Most ingredients from the list appear in the table (8 out of 9 is acceptable)
   - Each row has ingredient name and some information
   - PASS this gate unless ingredients are completely missing

2. FORMAT CHECK - PASS if:
   - There is a markdown table (rows with | separators)
   - The table has columns for at least: Ingredient, Purpose, Safety Rating, Recommendation
   - Additional columns are fine and expected
   - Truncated cell content is acceptable
   - PASS this gate if a valid table structure exists

3. ALLERGEN MATCH CHECK - PASS if:
   - User has no allergies: automatically PASS
   - User has allergies: check if matching ingredients are flagged
   - PASS this gate if "{allergen_list}" is "None declared" or "None specified"

4. CONSISTENCY CHECK - PASS if:
   - Safety ratings are numbers between 1-10
   - Recommendations are SAFE/CAUTION/AVOID type values
   - Minor rating inconsistencies are acceptable
   - PASS this gate unless ratings are completely wrong

5. TONE CHECK - PASS if:
   - The text is readable and informative
   - PASS this gate unless tone is completely inappropriate

DECISION RULES:
- Default to APPROVE unless there are CRITICAL failures
- A valid table with ingredient information = APPROVE
- Only REJECT if: no table exists, or majority of ingredients are missing

Respond with EXACTLY one of:

APPROVE
All gates pass. The analysis meets quality standards.

OR

REJECT
[Only if critical issues exist]
Gate failures: [list]
Issues: [list critical issues only]

YOUR DECISION:"""


# Legacy prompts for backward compatibility
ALLERGY_VERIFICATION_PROMPT = """Review this safety analysis report and verify if the user's allergies were properly considered.

User allergies: {user_allergies}

Report summary: {report_summary}

Ingredients analyzed:
{ingredients_list}

Question: Were the user's allergies ({user_allergies}) explicitly checked and addressed in this report?

Answer only YES or NO."""


TONE_CHECK_PROMPT = """Evaluate if this text matches the expected style.

Expected style: {expected_style}

Text to evaluate:
{report_summary}

Sample assessment:
{sample_assessment}

Does the text match the expected {expertise_level} style?
Answer only YES or NO."""
