"""Pytest configuration and shared fixtures for test suite.

Provides common test fixtures, mock configurations, and
test utilities used across all test modules.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Generator

from fastapi.testclient import TestClient

from api import app
from state.schema import (
    AllergyRiskFlag,
    AnalysisReport,
    CriticFeedback,
    ExpertiseLevel,
    IngredientAssessment,
    IngredientData,
    RiskLevel,
    SkinType,
    StageTiming,
    UserProfile,
    ValidationResult,
    WorkflowState,
)


# =============================================================================
# API Fixtures
# =============================================================================

@pytest.fixture
def api_client() -> TestClient:
    """Create FastAPI test client.

    Returns:
        TestClient instance for API testing.
    """
    return TestClient(app)


# =============================================================================
# State Fixtures
# =============================================================================

@pytest.fixture
def base_user_profile() -> UserProfile:
    """Create base user profile with default values.

    Returns:
        UserProfile with normal skin, beginner expertise, no allergies.
    """
    return UserProfile(
        allergies=[],
        skin_type=SkinType.NORMAL,
        expertise=ExpertiseLevel.BEGINNER,
    )


@pytest.fixture
def sensitive_user_profile() -> UserProfile:
    """Create sensitive skin user profile.

    Returns:
        UserProfile with sensitive skin and common allergies.
    """
    return UserProfile(
        allergies=["fragrance", "nuts"],
        skin_type=SkinType.SENSITIVE,
        expertise=ExpertiseLevel.BEGINNER,
    )


@pytest.fixture
def expert_user_profile() -> UserProfile:
    """Create expert-level user profile.

    Returns:
        UserProfile with expert expertise level.
    """
    return UserProfile(
        allergies=[],
        skin_type=SkinType.NORMAL,
        expertise=ExpertiseLevel.EXPERT,
    )


@pytest.fixture
def base_workflow_state(base_user_profile: UserProfile) -> WorkflowState:
    """Create base workflow state for testing.

    Args:
        base_user_profile: User profile fixture.

    Returns:
        WorkflowState with minimal initial values.
    """
    return WorkflowState(
        session_id="test-session-001",
        product_name="Test Product",
        raw_ingredients=["water", "glycerin"],
        user_profile=base_user_profile,
        ingredient_data=[],
        analysis_report=None,
        critic_feedback=None,
        retry_count=0,
        routing_history=[],
        stage_timings=StageTiming(
            research_time=0.0,
            analysis_time=0.0,
            critic_time=0.0,
        ),
        error=None,
    )


# =============================================================================
# Ingredient Fixtures
# =============================================================================

def create_test_ingredient(
    name: str,
    safety_rating: int = 7,
    category: str = "Unknown",
    concerns: str = "No known concerns",
    allergy_risk: AllergyRiskFlag = AllergyRiskFlag.LOW,
    source: str = "test",
    confidence: float = 0.9,
) -> IngredientData:
    """Factory function to create test ingredient data.

    Args:
        name: Ingredient name.
        safety_rating: Safety rating 1-10.
        category: Ingredient category.
        concerns: Safety concerns text.
        allergy_risk: Allergy risk flag.
        source: Data source identifier.
        confidence: Confidence score 0-1.

    Returns:
        Fully populated IngredientData.
    """
    return IngredientData(
        name=name,
        purpose="Test purpose",
        safety_rating=safety_rating,
        concerns=concerns,
        recommendation="Use as directed",
        allergy_risk_flag=allergy_risk,
        allergy_potential="Unknown",
        origin="Unknown",
        category=category,
        regulatory_status="Approved",
        regulatory_bans="No",
        source=source,
        confidence=confidence,
        aliases=[],
        risk_score=(10 - safety_rating) / 10,
        safety_notes=concerns,
    )


@pytest.fixture
def water_ingredient() -> IngredientData:
    """Create water ingredient (very safe)."""
    return create_test_ingredient(
        name="Water",
        safety_rating=10,
        category="Solvent",
        concerns="None",
    )


@pytest.fixture
def glycerin_ingredient() -> IngredientData:
    """Create glycerin ingredient (safe)."""
    return create_test_ingredient(
        name="Glycerin",
        safety_rating=9,
        category="Humectant",
        concerns="None",
    )


@pytest.fixture
def fragrance_ingredient() -> IngredientData:
    """Create fragrance ingredient (potential sensitizer)."""
    return create_test_ingredient(
        name="Fragrance",
        safety_rating=5,
        category="Fragrance",
        concerns="May cause skin sensitivity",
        allergy_risk=AllergyRiskFlag.HIGH,
    )


@pytest.fixture
def safe_ingredient_list(
    water_ingredient: IngredientData,
    glycerin_ingredient: IngredientData,
) -> list[IngredientData]:
    """Create list of safe ingredients."""
    return [water_ingredient, glycerin_ingredient]


# =============================================================================
# Report Fixtures
# =============================================================================

@pytest.fixture
def approved_report() -> AnalysisReport:
    """Create an approved analysis report."""
    return AnalysisReport(
        product_name="Test Product",
        overall_risk=RiskLevel.LOW,
        average_safety_score=8,
        summary="This product is safe for use.",
        assessments=[
            IngredientAssessment(
                name="water",
                risk_level=RiskLevel.LOW,
                rationale="Universal solvent, completely safe",
                is_allergen_match=False,
                alternatives=[],
            ),
            IngredientAssessment(
                name="glycerin",
                risk_level=RiskLevel.LOW,
                rationale="Safe moisturizing ingredient",
                is_allergen_match=False,
                alternatives=[],
            ),
        ],
        allergen_warnings=[],
        expertise_tone=ExpertiseLevel.BEGINNER,
    )


@pytest.fixture
def approval_feedback() -> CriticFeedback:
    """Create critic feedback indicating approval."""
    return CriticFeedback(
        result=ValidationResult.APPROVED,
        completeness_ok=True,
        format_ok=True,
        allergens_ok=True,
        consistency_ok=True,
        tone_ok=True,
        feedback="All validation gates passed.",
        failed_gates=[],
    )


@pytest.fixture
def rejection_feedback() -> CriticFeedback:
    """Create critic feedback indicating rejection."""
    return CriticFeedback(
        result=ValidationResult.REJECTED,
        completeness_ok=True,
        format_ok=False,
        allergens_ok=True,
        consistency_ok=True,
        tone_ok=True,
        feedback="Format check failed.",
        failed_gates=["Format"],
    )


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_services() -> Generator[dict, None, None]:
    """Mock all external LLM services.

    Yields:
        Dictionary of mock objects for LLM services.
    """
    with patch("agents.research.lookup_ingredient") as mock_lookup, \
         patch("agents.research.grounded_ingredient_search") as mock_search, \
         patch("agents.analysis._generate_llm_analysis") as mock_analysis, \
         patch("agents.critic._run_multi_gate_validation") as mock_critic:

        # Default behaviors
        mock_lookup.return_value = None
        mock_search.side_effect = lambda name: create_test_ingredient(name)
        mock_analysis.return_value = "## Analysis\n\nSafe for use."
        mock_critic.return_value = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": [],
            "feedback": "Approved",
        }

        yield {
            "lookup": mock_lookup,
            "search": mock_search,
            "analysis": mock_analysis,
            "critic": mock_critic,
        }


@pytest.fixture
def mock_workflow_success() -> Generator[MagicMock, None, None]:
    """Mock run_analysis to return successful result.

    Yields:
        Mock of run_analysis function.
    """
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
            "ingredient_data": [create_test_ingredient("water", 10)],
            "error": None,
        }
        yield mock


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
