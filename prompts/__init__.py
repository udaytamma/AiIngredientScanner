"""Prompt templates for LLM interactions.

Prompts:
    - analysis_prompts: Analysis agent prompt with tone adaptation
    - critic_prompts: Allergy verification and tone check prompts
    - grounded_search_prompts: Ingredient research prompt
"""

from prompts.analysis_prompts import (
    ANALYSIS_PROMPT,
    TONE_INSTRUCTIONS,
    format_ingredient_summary,
)
from prompts.critic_prompts import (
    ALLERGY_VERIFICATION_PROMPT,
    TONE_CHECK_PROMPT,
)
from prompts.grounded_search_prompts import (
    INGREDIENT_RESEARCH_PROMPT,
)

__all__ = [
    "ANALYSIS_PROMPT",
    "TONE_INSTRUCTIONS",
    "format_ingredient_summary",
    "ALLERGY_VERIFICATION_PROMPT",
    "TONE_CHECK_PROMPT",
    "INGREDIENT_RESEARCH_PROMPT",
]
