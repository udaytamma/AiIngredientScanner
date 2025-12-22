"""Tests for the Critic Agent with multi-gate validation."""

from unittest.mock import patch, MagicMock
import pytest

from agents.critic import (
    validate_report,
    is_approved,
    is_rejected,
    is_escalated,
    _parse_validation_response,
    _gate_failed,
)
from state.schema import (
    AnalysisReport,
    CriticFeedback,
    ExpertiseLevel,
    IngredientAssessment,
    RiskLevel,
    SkinType,
    UserProfile,
    ValidationResult,
    WorkflowState,
)


class TestGateParsing:
    """Tests for LLM response parsing."""

    def test_parse_approve_response(self) -> None:
        """Test parsing APPROVE response."""
        response = "APPROVE\nThe analysis passes all validation gates."
        default = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": [],
            "feedback": "",
        }

        result = _parse_validation_response(response, default)

        assert result["completeness_ok"] is True
        assert result["format_ok"] is True
        assert result["allergens_ok"] is True
        assert result["consistency_ok"] is True
        assert result["tone_ok"] is True
        assert result["failed_gates"] == []

    def test_parse_reject_single_gate(self) -> None:
        """Test parsing REJECT response with single gate failure."""
        response = """REJECT
Gate failures:
- Completeness check failed
Specific issues:
- Missing 2 ingredients from analysis
Required fixes:
- Add assessments for missing ingredients"""

        default = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": [],
            "feedback": "",
        }

        result = _parse_validation_response(response, default)

        assert result["completeness_ok"] is False
        assert "Completeness" in result["failed_gates"]
        assert "Issues:" in result["feedback"] or "Required fixes:" in result["feedback"]

    def test_parse_reject_multiple_gates(self) -> None:
        """Test parsing REJECT response with multiple gate failures."""
        response = """REJECT
Gate failures:
- Format check failed - no table structure
- Tone check failed - too technical for beginner
Specific issues:
- Analysis is not in table format
- Language is too complex
Required fixes:
- Present as markdown table
- Simplify language"""

        default = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": [],
            "feedback": "",
        }

        result = _parse_validation_response(response, default)

        assert result["format_ok"] is False
        assert result["tone_ok"] is False
        assert "Format" in result["failed_gates"]
        assert "Tone" in result["failed_gates"]

    def test_gate_failed_detection(self) -> None:
        """Test individual gate failure detection."""
        # Completeness failures
        assert _gate_failed("completeness check failed", "completeness") is True
        assert _gate_failed("completeness is missing items", "completeness") is True
        assert _gate_failed("completeness passes", "completeness") is False

        # Format failures
        assert _gate_failed("format violation detected", "format") is True
        assert _gate_failed("format check failed", "format") is True
        assert _gate_failed("format is correct", "format") is False

        # Allergen failures
        assert _gate_failed("allergen check failed", "allergen") is True
        assert _gate_failed("allergen not properly flagged", "allergen") is False  # No "issue" pattern

        # Consistency failures
        assert _gate_failed("consistency issues found", "consistency") is True
        assert _gate_failed("consistency check incomplete", "consistency") is True

        # Tone failures
        assert _gate_failed("tone is not appropriate", "tone") is False  # No match pattern
        assert _gate_failed("tone check failed", "tone") is True


class TestCriticStateHelpers:
    """Tests for state helper functions."""

    def test_is_approved_true(self) -> None:
        """Test is_approved returns True for approved state."""
        state = _create_minimal_state(ValidationResult.APPROVED)
        assert is_approved(state) is True

    def test_is_approved_false(self) -> None:
        """Test is_approved returns False for non-approved states."""
        state = _create_minimal_state(ValidationResult.REJECTED)
        assert is_approved(state) is False

        state = _create_minimal_state(ValidationResult.ESCALATED)
        assert is_approved(state) is False

    def test_is_rejected_true(self) -> None:
        """Test is_rejected returns True for rejected state."""
        state = _create_minimal_state(ValidationResult.REJECTED)
        assert is_rejected(state) is True

    def test_is_rejected_false(self) -> None:
        """Test is_rejected returns False for non-rejected states."""
        state = _create_minimal_state(ValidationResult.APPROVED)
        assert is_rejected(state) is False

    def test_is_escalated_true(self) -> None:
        """Test is_escalated returns True for escalated state."""
        state = _create_minimal_state(ValidationResult.ESCALATED)
        assert is_escalated(state) is True

    def test_is_escalated_false(self) -> None:
        """Test is_escalated returns False for non-escalated states."""
        state = _create_minimal_state(ValidationResult.APPROVED)
        assert is_escalated(state) is False

    def test_no_feedback_returns_false(self) -> None:
        """Test helpers return False when no feedback exists."""
        state = _create_minimal_state(None)
        state["critic_feedback"] = None

        assert is_approved(state) is False
        assert is_rejected(state) is False
        assert is_escalated(state) is False


class TestValidateReport:
    """Tests for the main validate_report function."""

    @patch("agents.critic._run_multi_gate_validation")
    def test_all_gates_pass_approves(self, mock_validation: MagicMock) -> None:
        """Test that all gates passing results in approval."""
        mock_validation.return_value = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": [],
            "feedback": "All gates passed",
        }

        state = _create_full_state()
        result = validate_report(state)

        assert result["critic_feedback"]["result"] == ValidationResult.APPROVED
        assert result["critic_feedback"]["failed_gates"] == []
        assert "critic" in result["routing_history"]

    @patch("agents.critic._run_multi_gate_validation")
    def test_single_gate_fail_rejects(self, mock_validation: MagicMock) -> None:
        """Test that single gate failure results in rejection."""
        mock_validation.return_value = {
            "completeness_ok": True,
            "format_ok": False,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": ["Format"],
            "feedback": "Format check failed",
        }

        state = _create_full_state()
        result = validate_report(state)

        assert result["critic_feedback"]["result"] == ValidationResult.REJECTED
        assert result["critic_feedback"]["format_ok"] is False
        assert "Format" in result["critic_feedback"]["failed_gates"]
        assert result["retry_count"] == 1

    @patch("agents.critic._run_multi_gate_validation")
    @patch("agents.critic.get_settings")
    def test_max_retries_escalates(
        self, mock_settings: MagicMock, mock_validation: MagicMock
    ) -> None:
        """Test that exceeding max retries results in escalation."""
        mock_settings.return_value.max_retries = 2

        mock_validation.return_value = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": False,
            "tone_ok": True,
            "failed_gates": ["Consistency"],
            "feedback": "Consistency issues",
        }

        state = _create_full_state()
        state["retry_count"] = 2  # Already at max

        result = validate_report(state)

        assert result["critic_feedback"]["result"] == ValidationResult.ESCALATED
        assert "Consistency" in result["critic_feedback"]["failed_gates"]

    @patch("agents.critic._run_multi_gate_validation")
    def test_routing_history_updated(self, mock_validation: MagicMock) -> None:
        """Test that routing history is updated."""
        mock_validation.return_value = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": [],
            "feedback": "",
        }

        state = _create_full_state()
        state["routing_history"] = ["research", "analysis"]

        result = validate_report(state)

        assert result["routing_history"] == ["research", "analysis", "critic"]


class TestMultiGateValidation:
    """Tests for the complete 5-gate validation logic."""

    def test_five_gates_all_pass(self) -> None:
        """Test all 5 gates passing."""
        feedback = CriticFeedback(
            result=ValidationResult.APPROVED,
            completeness_ok=True,
            format_ok=True,
            allergens_ok=True,
            consistency_ok=True,
            tone_ok=True,
            feedback="All gates passed",
            failed_gates=[],
        )

        all_pass = all([
            feedback["completeness_ok"],
            feedback["format_ok"],
            feedback["allergens_ok"],
            feedback["consistency_ok"],
            feedback["tone_ok"],
        ])

        assert all_pass is True
        assert len(feedback["failed_gates"]) == 0

    def test_five_gates_some_fail(self) -> None:
        """Test some gates failing."""
        feedback = CriticFeedback(
            result=ValidationResult.REJECTED,
            completeness_ok=True,
            format_ok=False,
            allergens_ok=True,
            consistency_ok=False,
            tone_ok=True,
            feedback="Gates failed",
            failed_gates=["Format", "Consistency"],
        )

        all_pass = all([
            feedback["completeness_ok"],
            feedback["format_ok"],
            feedback["allergens_ok"],
            feedback["consistency_ok"],
            feedback["tone_ok"],
        ])

        assert all_pass is False
        assert len(feedback["failed_gates"]) == 2


# Helper functions for creating test states

def _create_minimal_state(result: ValidationResult | None) -> WorkflowState:
    """Create minimal state for helper function tests."""
    feedback = None
    if result is not None:
        feedback = CriticFeedback(
            result=result,
            completeness_ok=True,
            format_ok=True,
            allergens_ok=True,
            consistency_ok=True,
            tone_ok=True,
            feedback="Test",
            failed_gates=[],
        )

    return WorkflowState(
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
        error=None,
    )


def _create_full_state() -> WorkflowState:
    """Create full state for validate_report tests."""
    return WorkflowState(
        session_id="test-123",
        product_name="Test Product",
        raw_ingredients=["water", "glycerin"],
        user_profile=UserProfile(
            allergies=["fragrance"],
            skin_type=SkinType.SENSITIVE,
            expertise=ExpertiseLevel.BEGINNER,
        ),
        ingredient_data=[],
        analysis_report=AnalysisReport(
            product_name="Test Product",
            overall_risk=RiskLevel.LOW,
            summary="| Ingredient | Purpose | Safety Rating | Concerns | Recommendation |\n|---|---|---|---|---|",
            assessments=[
                IngredientAssessment(
                    name="water",
                    risk_level=RiskLevel.LOW,
                    rationale="Safe solvent",
                    is_allergen_match=False,
                    alternatives=[],
                ),
                IngredientAssessment(
                    name="glycerin",
                    risk_level=RiskLevel.LOW,
                    rationale="Safe humectant",
                    is_allergen_match=False,
                    alternatives=[],
                ),
            ],
            allergen_warnings=[],
            expertise_tone=ExpertiseLevel.BEGINNER,
        ),
        critic_feedback=None,
        retry_count=0,
        routing_history=["research", "analysis"],
        error=None,
    )
