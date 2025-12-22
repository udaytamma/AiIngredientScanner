"""Tests for state schema definitions."""

import pytest

from state.schema import (
    ExpertiseLevel,
    SkinType,
    RiskLevel,
    ValidationResult,
    UserProfile,
    IngredientData,
    IngredientAssessment,
    AnalysisReport,
    CriticFeedback,
    WorkflowState,
)


class TestEnums:
    """Test enum definitions."""

    def test_expertise_level_values(self) -> None:
        """Test ExpertiseLevel enum values."""
        assert ExpertiseLevel.BEGINNER.value == "beginner"
        assert ExpertiseLevel.EXPERT.value == "expert"

    def test_skin_type_values(self) -> None:
        """Test SkinType enum values."""
        assert SkinType.NORMAL.value == "normal"
        assert SkinType.SENSITIVE.value == "sensitive"
        assert len(SkinType) == 5

    def test_risk_level_values(self) -> None:
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"

    def test_validation_result_values(self) -> None:
        """Test ValidationResult enum values."""
        assert ValidationResult.PENDING.value == "pending"
        assert ValidationResult.APPROVED.value == "approved"
        assert ValidationResult.REJECTED.value == "rejected"
        assert ValidationResult.ESCALATED.value == "escalated"


class TestTypedDicts:
    """Test TypedDict structures."""

    def test_user_profile_creation(self) -> None:
        """Test UserProfile creation."""
        profile: UserProfile = {
            "allergies": ["peanut", "milk"],
            "skin_type": SkinType.SENSITIVE,
            "expertise": ExpertiseLevel.BEGINNER,
        }
        assert profile["allergies"] == ["peanut", "milk"]
        assert profile["skin_type"] == SkinType.SENSITIVE

    def test_ingredient_data_creation(self) -> None:
        """Test IngredientData creation."""
        data: IngredientData = {
            "name": "sodium lauryl sulfate",
            "aliases": ["SLS", "sodium dodecyl sulfate"],
            "category": "surfactant",
            "risk_score": 0.4,
            "safety_notes": "May cause skin irritation",
            "source": "qdrant",
            "confidence": 0.95,
        }
        assert data["name"] == "sodium lauryl sulfate"
        assert data["risk_score"] == 0.4

    def test_ingredient_assessment_creation(self) -> None:
        """Test IngredientAssessment creation."""
        assessment: IngredientAssessment = {
            "name": "fragrance",
            "risk_level": RiskLevel.MEDIUM,
            "rationale": "May cause sensitivity",
            "is_allergen_match": True,
            "alternatives": ["fragrance-free"],
        }
        assert assessment["risk_level"] == RiskLevel.MEDIUM
        assert assessment["is_allergen_match"] is True

    def test_analysis_report_creation(self) -> None:
        """Test AnalysisReport creation."""
        report: AnalysisReport = {
            "product_name": "Test Product",
            "overall_risk": RiskLevel.LOW,
            "summary": "Safe product",
            "assessments": [],
            "allergen_warnings": [],
            "expertise_tone": ExpertiseLevel.BEGINNER,
        }
        assert report["product_name"] == "Test Product"
        assert report["overall_risk"] == RiskLevel.LOW

    def test_critic_feedback_creation(self) -> None:
        """Test CriticFeedback creation with 5-gate validation."""
        feedback: CriticFeedback = {
            "result": ValidationResult.APPROVED,
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "feedback": "All validation gates passed",
            "failed_gates": [],
        }
        assert feedback["result"] == ValidationResult.APPROVED
        assert feedback["completeness_ok"] is True
        assert feedback["format_ok"] is True
        assert feedback["allergens_ok"] is True
        assert feedback["consistency_ok"] is True
        assert feedback["tone_ok"] is True
        assert feedback["failed_gates"] == []

    def test_critic_feedback_rejected(self) -> None:
        """Test CriticFeedback with rejected validation."""
        feedback: CriticFeedback = {
            "result": ValidationResult.REJECTED,
            "completeness_ok": True,
            "format_ok": False,
            "allergens_ok": True,
            "consistency_ok": False,
            "tone_ok": True,
            "feedback": "Failed gates: Format, Consistency",
            "failed_gates": ["Format", "Consistency"],
        }
        assert feedback["result"] == ValidationResult.REJECTED
        assert feedback["format_ok"] is False
        assert feedback["consistency_ok"] is False
        assert len(feedback["failed_gates"]) == 2

    def test_workflow_state_creation(self) -> None:
        """Test WorkflowState creation."""
        state: WorkflowState = {
            "session_id": "test-123",
            "product_name": "Test Product",
            "raw_ingredients": ["water", "glycerin"],
            "user_profile": {
                "allergies": [],
                "skin_type": SkinType.NORMAL,
                "expertise": ExpertiseLevel.BEGINNER,
            },
            "ingredient_data": [],
            "analysis_report": None,
            "critic_feedback": None,
            "retry_count": 0,
            "routing_history": [],
            "error": None,
        }
        assert state["session_id"] == "test-123"
        assert len(state["raw_ingredients"]) == 2
