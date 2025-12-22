"""End-to-End validation tests for the Ingredient Safety Analyzer.

Tests complete workflows from API request to response, validating:
- Full pipeline execution with mocked LLM services
- Multi-agent coordination
- State transitions and data flow
- Response structure and content validation
"""

import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from api import app, AnalysisRequest, AnalysisResponse
from graph import run_analysis
from state.schema import (
    AllergyRiskFlag,
    ExpertiseLevel,
    IngredientData,
    RiskLevel,
    SkinType,
    ValidationResult,
    WorkflowState,
)


def _create_mock_ingredient(
    name: str,
    safety_rating: int = 7,
    category: str = "Unknown",
    concerns: str = "No known concerns",
) -> IngredientData:
    """Create mock ingredient data for testing."""
    return IngredientData(
        name=name,
        purpose="Test purpose",
        safety_rating=safety_rating,
        concerns=concerns,
        recommendation="Use as directed",
        allergy_risk_flag=AllergyRiskFlag.LOW,
        allergy_potential="Unknown",
        origin="Unknown",
        category=category,
        regulatory_status="Approved",
        regulatory_bans="No",
        source="mock",
        confidence=0.9,
        aliases=[],
        risk_score=(10 - safety_rating) / 10,
        safety_notes=concerns,
    )


class TestEndToEndWorkflow:
    """E2E tests for the complete analysis workflow."""

    @pytest.fixture
    def mock_llm_responses(self):
        """Setup mock LLM responses for complete workflow."""
        with patch("agents.research.lookup_ingredient") as mock_lookup, \
             patch("agents.research.grounded_ingredient_search") as mock_search, \
             patch("agents.analysis._generate_llm_analysis") as mock_analysis, \
             patch("agents.critic._run_multi_gate_validation") as mock_critic:

            # Research mocks - return ingredient data
            mock_lookup.return_value = None  # Force grounded search
            mock_search.side_effect = lambda name: _create_mock_ingredient(
                name=name,
                safety_rating=8 if name.lower() == "water" else 6,
                category="solvent" if name.lower() == "water" else "active",
            )

            # Analysis mock
            mock_analysis.return_value = "## Analysis\n\nThis product is safe for use."

            # Critic mock - approve on first try
            mock_critic.return_value = {
                "completeness_ok": True,
                "format_ok": True,
                "allergens_ok": True,
                "consistency_ok": True,
                "tone_ok": True,
                "failed_gates": [],
                "feedback": "All validation gates passed.",
            }

            yield {
                "lookup": mock_lookup,
                "search": mock_search,
                "analysis": mock_analysis,
                "critic": mock_critic,
            }

    def test_complete_workflow_happy_path(self, mock_llm_responses):
        """Test complete workflow from start to finish with approval."""
        result = run_analysis(
            session_id="e2e-test-001",
            product_name="Test Moisturizer",
            ingredients=["Water", "Glycerin", "Vitamin E"],
            allergies=[],
            skin_type="normal",
            expertise="beginner",
        )

        # Verify workflow completed successfully
        assert result.get("error") is None
        assert result.get("analysis_report") is not None
        assert result.get("critic_feedback") is not None

        # Verify routing history shows complete flow
        history = result.get("routing_history", [])
        assert "research" in history
        assert "analysis" in history
        assert "critic" in history

        # Verify critic approved
        assert result["critic_feedback"]["result"] == ValidationResult.APPROVED

    def test_complete_workflow_with_allergen(self, mock_llm_responses):
        """Test workflow detects and flags user allergens."""
        # Update mock to return fragrance ingredient
        mock_llm_responses["search"].side_effect = lambda name: _create_mock_ingredient(
            name=name,
            safety_rating=5 if "fragrance" in name.lower() else 8,
            category="fragrance" if "fragrance" in name.lower() else "solvent",
        )

        result = run_analysis(
            session_id="e2e-test-002",
            product_name="Scented Lotion",
            ingredients=["Water", "Fragrance", "Glycerin"],
            allergies=["fragrance"],
            skin_type="sensitive",
            expertise="beginner",
        )

        # Verify allergen was flagged
        report = result.get("analysis_report", {})
        allergen_warnings = report.get("allergen_warnings", [])
        assert len(allergen_warnings) > 0

        # Verify fragrance assessment shows allergen match
        assessments = report.get("assessments", [])
        fragrance_assessment = next(
            (a for a in assessments if "fragrance" in a["name"].lower()),
            None
        )
        assert fragrance_assessment is not None
        assert fragrance_assessment["is_allergen_match"] is True

    def test_workflow_retry_on_rejection(self, mock_llm_responses):
        """Test workflow retries analysis when critic rejects."""
        # First critic call rejects, second approves
        mock_llm_responses["critic"].side_effect = [
            {
                "completeness_ok": True,
                "format_ok": False,
                "allergens_ok": True,
                "consistency_ok": True,
                "tone_ok": True,
                "failed_gates": ["Format"],
                "feedback": "Format check failed. Please fix.",
            },
            {
                "completeness_ok": True,
                "format_ok": True,
                "allergens_ok": True,
                "consistency_ok": True,
                "tone_ok": True,
                "failed_gates": [],
                "feedback": "All gates passed on retry.",
            },
        ]

        result = run_analysis(
            session_id="e2e-test-003",
            product_name="Test Product",
            ingredients=["Water", "Glycerin"],
            allergies=[],
            skin_type="normal",
            expertise="beginner",
        )

        # Verify retry occurred
        assert result.get("retry_count", 0) >= 1

        # Verify eventually approved
        feedback = result.get("critic_feedback", {})
        assert feedback.get("result") == ValidationResult.APPROVED

    def test_workflow_escalation_after_max_retries(self, mock_llm_responses):
        """Test workflow escalates after exceeding max retries."""
        # Critic always rejects
        mock_llm_responses["critic"].return_value = {
            "completeness_ok": True,
            "format_ok": False,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": ["Format"],
            "feedback": "Format check failed repeatedly.",
        }

        with patch("agents.critic.get_settings") as mock_settings:
            mock_settings.return_value.max_retries = 2

            result = run_analysis(
                session_id="e2e-test-004",
                product_name="Test Product",
                ingredients=["Water"],
                allergies=[],
                skin_type="normal",
                expertise="beginner",
            )

            # Verify escalation occurred
            feedback = result.get("critic_feedback", {})
            assert feedback.get("result") == ValidationResult.ESCALATED


class TestEndToEndAPI:
    """E2E tests for the complete API flow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_workflow(self):
        """Mock the workflow to return predictable results."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test Product",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe for use.",
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
                "ingredient_data": [
                    _create_mock_ingredient("water", safety_rating=10),
                ],
                "error": None,
            }
            yield mock

    def test_api_analyze_complete_flow(self, client, mock_workflow):
        """Test complete API analyze endpoint flow."""
        response = client.post(
            "/analyze",
            json={
                "product_name": "Test Cream",
                "ingredients": "Water, Glycerin, Vitamin E",
                "allergies": [],
                "skin_type": "normal",
                "expertise": "beginner",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert data["product_name"] == "Test Product"
        assert data["overall_risk"] == "low"
        assert "ingredients" in data
        assert "execution_time" in data
        assert data["error"] is None

    def test_api_analyze_with_allergies(self, client, mock_workflow):
        """Test API correctly passes allergies to workflow."""
        response = client.post(
            "/analyze",
            json={
                "product_name": "Scented Lotion",
                "ingredients": "Water, Fragrance",
                "allergies": ["fragrance", "nuts"],
                "skin_type": "sensitive",
                "expertise": "beginner",
            },
        )

        assert response.status_code == 200

        # Verify allergies were passed to workflow
        call_args = mock_workflow.call_args
        assert "fragrance" in call_args.kwargs["allergies"]
        assert "nuts" in call_args.kwargs["allergies"]

    def test_api_response_timing(self, client, mock_workflow):
        """Test API response includes execution timing."""
        response = client.post(
            "/analyze",
            json={
                "ingredients": "Water, Glycerin",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify timing is included and reasonable
        assert "execution_time" in data
        assert data["execution_time"] >= 0


class TestDataFlowValidation:
    """Tests to validate data flows correctly through workflow stages."""

    def test_ingredient_data_flows_to_analysis(self):
        """Verify ingredient data from research flows to analysis."""
        with patch("agents.research.lookup_ingredient") as mock_lookup, \
             patch("agents.research.grounded_ingredient_search") as mock_search, \
             patch("agents.analysis._generate_llm_analysis") as mock_llm, \
             patch("agents.critic._run_multi_gate_validation") as mock_critic:

            test_ingredient = _create_mock_ingredient(
                name="TestIngredient",
                safety_rating=7,
                concerns="Test concerns",
            )

            mock_lookup.return_value = test_ingredient
            mock_search.return_value = None
            mock_llm.return_value = "Test analysis"
            mock_critic.return_value = {
                "completeness_ok": True,
                "format_ok": True,
                "allergens_ok": True,
                "consistency_ok": True,
                "tone_ok": True,
                "failed_gates": [],
                "feedback": "Approved",
            }

            result = run_analysis(
                session_id="flow-test-001",
                product_name="Test",
                ingredients=["TestIngredient"],
                allergies=[],
                skin_type="normal",
                expertise="beginner",
            )

            # Verify ingredient data was captured
            ingredient_data = result.get("ingredient_data", [])
            assert len(ingredient_data) == 1
            assert ingredient_data[0]["name"] == "TestIngredient"
            assert ingredient_data[0]["concerns"] == "Test concerns"

    def test_user_profile_flows_through_workflow(self):
        """Verify user profile affects analysis throughout workflow."""
        with patch("agents.research.lookup_ingredient") as mock_lookup, \
             patch("agents.research.grounded_ingredient_search") as mock_search, \
             patch("agents.analysis._generate_llm_analysis") as mock_llm, \
             patch("agents.critic._run_multi_gate_validation") as mock_critic:

            mock_lookup.return_value = _create_mock_ingredient("water")
            mock_search.return_value = None
            mock_llm.return_value = "Expert analysis"
            mock_critic.return_value = {
                "completeness_ok": True,
                "format_ok": True,
                "allergens_ok": True,
                "consistency_ok": True,
                "tone_ok": True,
                "failed_gates": [],
                "feedback": "Approved",
            }

            result = run_analysis(
                session_id="profile-test-001",
                product_name="Test",
                ingredients=["Water"],
                allergies=["peanut"],
                skin_type="sensitive",
                expertise="expert",
            )

            # Verify user profile is captured in state
            user_profile = result.get("user_profile", {})
            assert "peanut" in user_profile.get("allergies", [])
            assert user_profile.get("skin_type") == SkinType.SENSITIVE
            assert user_profile.get("expertise") == ExpertiseLevel.EXPERT

            # Verify report uses expert tone
            report = result.get("analysis_report", {})
            assert report.get("expertise_tone") == ExpertiseLevel.EXPERT


class TestErrorHandling:
    """E2E tests for error handling scenarios."""

    def test_workflow_handles_research_failure(self):
        """Test workflow captures error gracefully when research fails."""
        with patch("agents.research.lookup_ingredient") as mock_lookup, \
             patch("agents.research.grounded_ingredient_search") as mock_search, \
             patch("agents.analysis._generate_llm_analysis") as mock_llm, \
             patch("agents.critic._run_multi_gate_validation") as mock_critic:

            # Research fails - workflow should capture error in state
            mock_lookup.side_effect = Exception("API Error")
            mock_search.return_value = None
            mock_llm.return_value = "Analysis"
            mock_critic.return_value = {
                "completeness_ok": True,
                "format_ok": True,
                "allergens_ok": True,
                "consistency_ok": True,
                "tone_ok": True,
                "failed_gates": [],
                "feedback": "Approved",
            }

            result = run_analysis(
                session_id="error-test-001",
                product_name="Test",
                ingredients=["Unknown", "Glycerin"],
                allergies=[],
                skin_type="normal",
                expertise="beginner",
            )

            # Workflow should capture error in state without crashing
            # The error is recorded in the workflow state
            assert result is not None
            # Either error is captured or workflow returns with empty data
            has_error = result.get("error") is not None
            has_empty_data = len(result.get("ingredient_data", [])) == 0
            assert has_error or has_empty_data, "Workflow should handle failures gracefully"

    def test_api_handles_workflow_error(self):
        """Test API returns error response when workflow fails."""
        client = TestClient(app)

        with patch("api.run_analysis") as mock:
            mock.return_value = {"error": "Critical failure in workflow"}

            response = client.post(
                "/analyze",
                json={"ingredients": "Water, Glycerin"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data
            assert data["error"] == "Critical failure in workflow"
