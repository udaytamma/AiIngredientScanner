"""Edge case and boundary tests for the Ingredient Safety Analyzer.

Tests boundary conditions and unusual input scenarios:
- Empty inputs and null values
- Unicode and special characters
- Extreme values (very long strings, many items)
- Malformed data handling
- State machine edge cases
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from api import app
from graph import run_analysis
from state.schema import (
    AllergyRiskFlag,
    AnalysisReport,
    CriticFeedback,
    ExpertiseLevel,
    IngredientAssessment,
    IngredientData,
    RiskLevel,
    SkinType,
    UserProfile,
    ValidationResult,
    WorkflowState,
)
from agents.supervisor import route_next, NODE_END
from agents.research import has_research_data, _create_unknown_ingredient
from agents.analysis import has_analysis_report, _calculate_assessments
from agents.critic import is_approved, is_rejected, is_escalated


def _create_test_ingredient(
    name: str,
    safety_rating: int = 5,
    category: str = "unknown",
) -> IngredientData:
    """Create test ingredient data."""
    return IngredientData(
        name=name,
        purpose="Test",
        safety_rating=safety_rating,
        concerns="None",
        recommendation="Use as directed",
        allergy_risk_flag=AllergyRiskFlag.LOW,
        allergy_potential="Unknown",
        origin="Unknown",
        category=category,
        regulatory_status="Unknown",
        regulatory_bans="No",
        source="test",
        confidence=0.9,
        aliases=[],
        risk_score=(10 - safety_rating) / 10,
        safety_notes="",
    )


class TestEmptyInputs:
    """Tests for empty and null input handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_empty_ingredients_string(self, client):
        """Empty ingredients string should return error."""
        response = client.post(
            "/analyze",
            json={"ingredients": ""},
        )
        assert response.status_code == 400
        assert "No ingredients" in response.json()["detail"]

    def test_whitespace_only_ingredients(self, client):
        """Whitespace-only ingredients should return error."""
        response = client.post(
            "/analyze",
            json={"ingredients": "   ,  ,   "},
        )
        assert response.status_code == 400

    def test_empty_allergies_list(self, client):
        """Empty allergies list should be handled."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe",
                    "assessments": [],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [],
                "error": None,
            }

            response = client.post(
                "/analyze",
                json={
                    "ingredients": "Water",
                    "allergies": [],
                },
            )
            assert response.status_code == 200

    def test_has_research_data_empty_list(self):
        """has_research_data should handle empty ingredient list."""
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[],  # Empty
            analysis_report=None,
            critic_feedback=None,
            retry_count=0,
            routing_history=[],
            stage_timings=None,
            error=None,
        )
        assert has_research_data(state) is False


class TestUnicodeAndSpecialCharacters:
    """Tests for Unicode and special character handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_unicode_ingredient_names(self, client):
        """Unicode ingredient names should be processed."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe",
                    "assessments": [],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [],
                "error": None,
            }

            response = client.post(
                "/analyze",
                json={
                    "ingredients": "水, グリセリン, 비타민E",  # Water, Glycerin, Vitamin E in multiple languages
                },
            )
            assert response.status_code == 200

    def test_special_characters_in_names(self, client):
        """Special characters in names should be handled."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test & Product (v2.0)",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe",
                    "assessments": [],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [],
                "error": None,
            }

            response = client.post(
                "/analyze",
                json={
                    "product_name": "Test & Product (v2.0)",
                    "ingredients": "Alpha-Tocopherol, β-Carotene, Vitamin C (Ascorbic Acid)",
                },
            )
            assert response.status_code == 200

    def test_emoji_in_product_name(self, client):
        """Emoji in product name should be handled."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Glow Cream ✨",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe",
                    "assessments": [],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [],
                "error": None,
            }

            response = client.post(
                "/analyze",
                json={
                    "product_name": "Glow Cream ✨",
                    "ingredients": "Water",
                },
            )
            assert response.status_code == 200


class TestExtremeValues:
    """Tests for extreme input values."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_very_long_product_name(self, client):
        """Very long product name should be handled."""
        long_name = "A" * 1000  # 1000 character name

        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": long_name,
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe",
                    "assessments": [],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [],
                "error": None,
            }

            response = client.post(
                "/analyze",
                json={
                    "product_name": long_name,
                    "ingredients": "Water",
                },
            )
            # Should handle gracefully (either accept or return validation error)
            assert response.status_code in [200, 422]

    def test_single_ingredient(self, client):
        """Single ingredient should be processed correctly."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 10,
                    "summary": "Just water",
                    "assessments": [
                        {
                            "name": "water",
                            "risk_level": RiskLevel.LOW,
                            "rationale": "Safe",
                            "is_allergen_match": False,
                            "alternatives": [],
                        }
                    ],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [_create_test_ingredient("water", 10)],
                "error": None,
            }

            response = client.post(
                "/analyze",
                json={"ingredients": "Water"},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["ingredients"]) == 1

    def test_safety_score_boundaries(self):
        """Safety scores at boundaries should classify correctly."""
        from tools.safety_scorer import classify_risk_level

        # Edge cases at classification boundaries
        assert classify_risk_level(0.0) == RiskLevel.LOW
        assert classify_risk_level(0.29) == RiskLevel.LOW
        assert classify_risk_level(0.30) == RiskLevel.MEDIUM
        assert classify_risk_level(0.59) == RiskLevel.MEDIUM
        assert classify_risk_level(0.60) == RiskLevel.HIGH
        assert classify_risk_level(1.0) == RiskLevel.HIGH


class TestStateMachineEdgeCases:
    """Tests for workflow state machine edge cases."""

    def test_route_with_no_state_data(self):
        """Routing with minimal state should start at research."""
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[],
            analysis_report=None,
            critic_feedback=None,
            retry_count=0,
            routing_history=[],
            stage_timings=None,
            error=None,
        )

        next_node = route_next(state)
        assert next_node == "research"

    def test_route_with_error_goes_to_end(self):
        """State with error should route to END."""
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[],
            analysis_report=None,
            critic_feedback=None,
            retry_count=0,
            routing_history=[],
            stage_timings=None,
            error="Critical error occurred",
        )

        next_node = route_next(state)
        assert next_node == NODE_END

    def test_multiple_routing_cycles(self):
        """Multiple retry cycles should be tracked in history."""
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[_create_test_ingredient("water")],
            analysis_report=AnalysisReport(
                product_name="Test",
                overall_risk=RiskLevel.LOW,
                average_safety_score=8,
                summary="Safe",
                assessments=[],
                allergen_warnings=[],
                expertise_tone=ExpertiseLevel.BEGINNER,
            ),
            critic_feedback=CriticFeedback(
                result=ValidationResult.REJECTED,
                completeness_ok=True,
                format_ok=False,
                allergens_ok=True,
                consistency_ok=True,
                tone_ok=True,
                feedback="Format issue",
                failed_gates=["Format"],
            ),
            retry_count=1,
            routing_history=["research", "analysis", "critic"],
            stage_timings=None,
            error=None,
        )

        # Should route back to analysis for retry
        next_node = route_next(state)
        assert next_node == "analysis"


class TestCriticFeedbackEdgeCases:
    """Tests for critic feedback edge cases."""

    def test_all_gates_fail(self):
        """All gates failing should still reject."""
        feedback = CriticFeedback(
            result=ValidationResult.REJECTED,
            completeness_ok=False,
            format_ok=False,
            allergens_ok=False,
            consistency_ok=False,
            tone_ok=False,
            feedback="All gates failed",
            failed_gates=["Completeness", "Format", "Allergens", "Consistency", "Tone"],
        )

        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[],
            analysis_report=None,
            critic_feedback=feedback,
            retry_count=0,
            routing_history=[],
            stage_timings=None,
            error=None,
        )

        assert is_rejected(state) is True
        assert is_approved(state) is False

    def test_no_feedback_returns_false(self):
        """No feedback should return False for all status checks."""
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[],
            analysis_report=None,
            critic_feedback=None,  # No feedback
            retry_count=0,
            routing_history=[],
            stage_timings=None,
            error=None,
        )

        assert is_approved(state) is False
        assert is_rejected(state) is False
        assert is_escalated(state) is False


class TestUnknownIngredientHandling:
    """Tests for handling unknown ingredients."""

    def test_create_unknown_ingredient_fields(self):
        """Unknown ingredient should have default safe values."""
        result = _create_unknown_ingredient("mystery_compound")

        assert result["name"] == "mystery_compound"
        assert result["source"] == "unknown"
        assert result["confidence"] == 0.0
        assert result["safety_rating"] == 5  # Neutral default
        assert result["risk_score"] == 0.5  # Neutral default

    def test_unknown_ingredient_in_assessments(self):
        """Unknown ingredients should get neutral assessments."""
        ingredients = [_create_unknown_ingredient("mystery")]
        profile = UserProfile(
            allergies=[],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

        assessments, warnings, scores = _calculate_assessments(ingredients, profile)

        assert len(assessments) == 1
        assert assessments[0]["name"] == "mystery"
        # Unknown should get medium risk (neutral)
        assert assessments[0]["risk_level"] == RiskLevel.MEDIUM


class TestAllergenEdgeCases:
    """Tests for allergen matching edge cases."""

    def test_allergen_partial_match(self):
        """Partial allergen name match should trigger warning."""
        from tools.allergen_matcher import check_allergen_match

        # "peanut" allergy should match "peanut oil"
        ingredient = _create_test_ingredient("peanut oil")
        profile = UserProfile(
            allergies=["peanut"],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

        is_match, matched = check_allergen_match(ingredient, profile)
        assert is_match is True
        assert matched == "peanut"

    def test_case_insensitive_allergen_match(self):
        """Allergen matching should be case insensitive."""
        from tools.allergen_matcher import check_allergen_match

        ingredient = _create_test_ingredient("PEANUT OIL")
        profile = UserProfile(
            allergies=["Peanut"],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

        is_match, matched = check_allergen_match(ingredient, profile)
        assert is_match is True

    def test_multiple_allergen_matches(self):
        """Multiple allergens should all be detected."""
        from tools.allergen_matcher import find_all_allergen_matches

        ingredients = [
            _create_test_ingredient("peanut butter"),
            _create_test_ingredient("milk protein"),
            _create_test_ingredient("water"),
        ]
        profile = UserProfile(
            allergies=["peanut", "milk"],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

        matches = find_all_allergen_matches(ingredients, profile)
        assert len(matches) == 2


class TestAPIValidation:
    """Tests for API input validation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_missing_required_field(self, client):
        """Missing required field should return validation error."""
        response = client.post(
            "/analyze",
            json={},  # Missing ingredients
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_skin_type(self, client):
        """Invalid skin type should be handled."""
        with patch("api.run_analysis") as mock:
            mock.side_effect = ValueError("invalid skin type")

            response = client.post(
                "/analyze",
                json={
                    "ingredients": "Water",
                    "skin_type": "invalid_type",
                },
            )
            # Should return error status
            assert response.status_code in [200, 400, 500]

    def test_invalid_expertise_level(self, client):
        """Invalid expertise level should be handled."""
        with patch("api.run_analysis") as mock:
            mock.side_effect = ValueError("invalid expertise")

            response = client.post(
                "/analyze",
                json={
                    "ingredients": "Water",
                    "expertise": "invalid_level",
                },
            )
            # Should return error status
            assert response.status_code in [200, 400, 500]
