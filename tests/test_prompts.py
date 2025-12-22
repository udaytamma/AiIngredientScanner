"""Tests for prompt modules."""

import pytest

from state.schema import AllergyRiskFlag, IngredientData
from prompts.analysis_prompts import (
    ANALYSIS_PROMPT,
    TONE_INSTRUCTIONS,
    format_ingredient_summary,
)
from prompts.grounded_search_prompts import INGREDIENT_RESEARCH_PROMPT
from prompts.critic_prompts import (
    ALLERGY_VERIFICATION_PROMPT,
    TONE_CHECK_PROMPT,
)


class TestAnalysisPrompts:
    """Tests for analysis prompt templates."""

    def test_tone_instructions_keys(self) -> None:
        """Test TONE_INSTRUCTIONS has all expertise levels."""
        assert "beginner" in TONE_INSTRUCTIONS
        assert "intermediate" in TONE_INSTRUCTIONS
        assert "expert" in TONE_INSTRUCTIONS

    def test_tone_instructions_beginner_content(self) -> None:
        """Test beginner tone instruction content."""
        beginner = TONE_INSTRUCTIONS["beginner"]
        assert "simple" in beginner.lower()
        assert "jargon" in beginner.lower()

    def test_tone_instructions_expert_content(self) -> None:
        """Test expert tone instruction content."""
        expert = TONE_INSTRUCTIONS["expert"]
        assert "technical" in expert.lower()

    def test_analysis_prompt_has_placeholders(self) -> None:
        """Test ANALYSIS_PROMPT has required placeholders."""
        assert "{tone_instruction}" in ANALYSIS_PROMPT
        assert "{skin_type}" in ANALYSIS_PROMPT
        assert "{expertise_level}" in ANALYSIS_PROMPT
        assert "{allergies_list}" in ANALYSIS_PROMPT
        assert "{ingredient_summary}" in ANALYSIS_PROMPT

    def test_analysis_prompt_has_table_format(self) -> None:
        """Test ANALYSIS_PROMPT specifies table format."""
        assert "| Ingredient |" in ANALYSIS_PROMPT
        assert "| Purpose |" in ANALYSIS_PROMPT
        assert "| Safety Rating |" in ANALYSIS_PROMPT

    def test_analysis_prompt_has_sections(self) -> None:
        """Test ANALYSIS_PROMPT has expected sections."""
        assert "## Ingredient Analysis" in ANALYSIS_PROMPT
        assert "## Allergen/Ingredient Check" in ANALYSIS_PROMPT
        assert "## Overall Verdict" in ANALYSIS_PROMPT
        assert "## Summary" in ANALYSIS_PROMPT

    def test_analysis_prompt_formatting(self) -> None:
        """Test ANALYSIS_PROMPT can be formatted without errors."""
        formatted = ANALYSIS_PROMPT.format(
            tone_instruction="Use simple language",
            skin_type="Normal",
            expertise_level="Beginner",
            allergies_list="None",
            ingredient_summary="1. Water - safe ingredient",
        )
        assert "Normal" in formatted
        assert "Beginner" in formatted

    def test_format_ingredient_summary_single(self) -> None:
        """Test format_ingredient_summary with single ingredient."""
        ingredient = IngredientData(
            name="Glycerin",
            purpose="Humectant",
            safety_rating=9,
            concerns="None known",
            recommendation="Safe for daily use",
            allergy_risk_flag=AllergyRiskFlag.LOW,
            allergy_potential="Rare reactions",
            origin="Natural",
            category="Cosmetics",
            regulatory_status="FDA Approved",
            regulatory_bans="No",
            source="test",
            confidence=0.9,
            aliases=[],
            risk_score=0.1,
            safety_notes="",
        )
        result = format_ingredient_summary([ingredient])

        assert "1. Glycerin" in result
        assert "Purpose: Humectant" in result
        assert "Safety Rating: 9/10" in result
        assert "Origin: Natural" in result
        assert "Category: Cosmetics" in result

    def test_format_ingredient_summary_multiple(self) -> None:
        """Test format_ingredient_summary with multiple ingredients."""
        ingredients = [
            IngredientData(
                name="Water",
                purpose="Solvent",
                safety_rating=10,
                concerns="None",
                recommendation="Safe",
                allergy_risk_flag=AllergyRiskFlag.LOW,
                allergy_potential="None",
                origin="Natural",
                category="Both",
                regulatory_status="Approved",
                regulatory_bans="No",
                source="test",
                confidence=1.0,
                aliases=[],
                risk_score=0.0,
                safety_notes="",
            ),
            IngredientData(
                name="Fragrance",
                purpose="Scent",
                safety_rating=5,
                concerns="May irritate sensitive skin",
                recommendation="Avoid if sensitive",
                allergy_risk_flag=AllergyRiskFlag.HIGH,
                allergy_potential="Sensitive skin",
                origin="Synthetic",
                category="Cosmetics",
                regulatory_status="Approved with restrictions",
                regulatory_bans="No",
                source="test",
                confidence=0.8,
                aliases=[],
                risk_score=0.5,
                safety_notes="",
            ),
        ]
        result = format_ingredient_summary(ingredients)

        assert "1. Water" in result
        assert "2. Fragrance" in result
        assert "Allergy Risk Flag: High" in result

    def test_format_ingredient_summary_empty(self) -> None:
        """Test format_ingredient_summary with empty list."""
        result = format_ingredient_summary([])
        assert result == ""


class TestGroundedSearchPrompts:
    """Tests for grounded search prompt templates."""

    def test_ingredient_research_prompt_has_placeholder(self) -> None:
        """Test INGREDIENT_RESEARCH_PROMPT has ingredient_name placeholder."""
        assert "{ingredient_name}" in INGREDIENT_RESEARCH_PROMPT

    def test_ingredient_research_prompt_has_fields(self) -> None:
        """Test prompt specifies all required response fields."""
        assert "INGREDIENT_NAME:" in INGREDIENT_RESEARCH_PROMPT
        assert "PURPOSE:" in INGREDIENT_RESEARCH_PROMPT
        assert "SAFETY_RATING:" in INGREDIENT_RESEARCH_PROMPT
        assert "CONCERNS:" in INGREDIENT_RESEARCH_PROMPT
        assert "RECOMMENDATION:" in INGREDIENT_RESEARCH_PROMPT
        assert "ALLERGY_RISK_FLAG:" in INGREDIENT_RESEARCH_PROMPT
        assert "ALLERGY_POTENTIAL:" in INGREDIENT_RESEARCH_PROMPT
        assert "ORIGIN:" in INGREDIENT_RESEARCH_PROMPT
        assert "CATEGORY:" in INGREDIENT_RESEARCH_PROMPT
        assert "REGULATORY_STATUS:" in INGREDIENT_RESEARCH_PROMPT
        assert "REGULATORY_BANS:" in INGREDIENT_RESEARCH_PROMPT

    def test_ingredient_research_prompt_formatting(self) -> None:
        """Test INGREDIENT_RESEARCH_PROMPT can be formatted."""
        formatted = INGREDIENT_RESEARCH_PROMPT.format(
            ingredient_name="Sodium Lauryl Sulfate"
        )
        assert "Sodium Lauryl Sulfate" in formatted
        assert "{ingredient_name}" not in formatted


class TestCriticPrompts:
    """Tests for critic agent prompt templates."""

    def test_allergy_verification_prompt_placeholders(self) -> None:
        """Test ALLERGY_VERIFICATION_PROMPT has required placeholders."""
        assert "{user_allergies}" in ALLERGY_VERIFICATION_PROMPT
        assert "{report_summary}" in ALLERGY_VERIFICATION_PROMPT
        assert "{ingredients_list}" in ALLERGY_VERIFICATION_PROMPT

    def test_allergy_verification_prompt_yes_no(self) -> None:
        """Test prompt asks for YES/NO response."""
        assert "YES or NO" in ALLERGY_VERIFICATION_PROMPT

    def test_allergy_verification_prompt_formatting(self) -> None:
        """Test ALLERGY_VERIFICATION_PROMPT can be formatted."""
        formatted = ALLERGY_VERIFICATION_PROMPT.format(
            user_allergies="fragrance, sulfates",
            report_summary="This product is safe.",
            ingredients_list="- Water: Safe\n- Glycerin: Safe",
        )
        assert "fragrance, sulfates" in formatted
        assert "This product is safe." in formatted

    def test_tone_check_prompt_placeholders(self) -> None:
        """Test TONE_CHECK_PROMPT has required placeholders."""
        assert "{expected_style}" in TONE_CHECK_PROMPT
        assert "{expertise_level}" in TONE_CHECK_PROMPT
        assert "{report_summary}" in TONE_CHECK_PROMPT
        assert "{sample_assessment}" in TONE_CHECK_PROMPT

    def test_tone_check_prompt_yes_no(self) -> None:
        """Test prompt asks for YES/NO response."""
        assert "YES or NO" in TONE_CHECK_PROMPT

    def test_tone_check_prompt_formatting(self) -> None:
        """Test TONE_CHECK_PROMPT can be formatted."""
        formatted = TONE_CHECK_PROMPT.format(
            expected_style="Simple, clear language",
            expertise_level="beginner",
            report_summary="This product is safe to use.",
            sample_assessment="Glycerin is a safe moisturizer.",
        )
        assert "Simple, clear language" in formatted
        assert "beginner" in formatted
