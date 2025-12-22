"""Tests for Supervisor Agent routing logic."""

import pytest

from state.schema import (
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
from agents.supervisor import (
    route_next,
    should_continue,
    get_routing_decision,
    NODE_RESEARCH,
    NODE_ANALYSIS,
    NODE_CRITIC,
    NODE_END,
)


class TestRouteNext:
    """Tests for route_next function."""

    @pytest.fixture
    def empty_state(self) -> WorkflowState:
        """Create empty initial state."""
        return WorkflowState(
            session_id="test-123",
            product_name="Test Product",
            raw_ingredients=["water", "glycerin"],
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
            error=None,
        )

    @pytest.fixture
    def state_with_data(self, empty_state: WorkflowState) -> WorkflowState:
        """Create state with research data."""
        empty_state["ingredient_data"] = [
            IngredientData(
                name="water",
                aliases=[],
                category="solvent",
                risk_score=0.0,
                safety_notes="Safe",
                source="qdrant",
                confidence=0.99,
            ),
            IngredientData(
                name="glycerin",
                aliases=[],
                category="humectant",
                risk_score=0.1,
                safety_notes="Safe",
                source="qdrant",
                confidence=0.95,
            ),
        ]
        return empty_state

    @pytest.fixture
    def state_with_report(self, state_with_data: WorkflowState) -> WorkflowState:
        """Create state with analysis report."""
        state_with_data["analysis_report"] = AnalysisReport(
            product_name="Test Product",
            overall_risk=RiskLevel.LOW,
            summary="Safe product",
            assessments=[
                IngredientAssessment(
                    name="water",
                    risk_level=RiskLevel.LOW,
                    rationale="Safe",
                    is_allergen_match=False,
                    alternatives=[],
                ),
                IngredientAssessment(
                    name="glycerin",
                    risk_level=RiskLevel.LOW,
                    rationale="Safe",
                    is_allergen_match=False,
                    alternatives=[],
                ),
            ],
            allergen_warnings=[],
            expertise_tone=ExpertiseLevel.BEGINNER,
        )
        return state_with_data

    def test_route_to_research_when_no_data(
        self, empty_state: WorkflowState
    ) -> None:
        """Test routing to research when no ingredient data."""
        assert route_next(empty_state) == NODE_RESEARCH

    def test_route_to_analysis_when_data_no_report(
        self, state_with_data: WorkflowState
    ) -> None:
        """Test routing to analysis when data exists but no report."""
        assert route_next(state_with_data) == NODE_ANALYSIS

    def test_route_to_critic_when_report_exists(
        self, state_with_report: WorkflowState
    ) -> None:
        """Test routing to critic when report needs validation."""
        assert route_next(state_with_report) == NODE_CRITIC

    def test_route_to_end_when_approved(
        self, state_with_report: WorkflowState
    ) -> None:
        """Test routing to end when approved."""
        state_with_report["critic_feedback"] = CriticFeedback(
            result=ValidationResult.APPROVED,
            coverage_ok=True,
            allergies_ok=True,
            tone_ok=True,
            feedback="Good",
        )
        assert route_next(state_with_report) == NODE_END

    def test_route_to_analysis_when_rejected(
        self, state_with_report: WorkflowState
    ) -> None:
        """Test routing back to analysis when rejected."""
        state_with_report["critic_feedback"] = CriticFeedback(
            result=ValidationResult.REJECTED,
            coverage_ok=True,
            allergies_ok=True,
            tone_ok=False,
            feedback="Fix tone",
        )
        assert route_next(state_with_report) == NODE_ANALYSIS

    def test_route_to_end_when_escalated(
        self, state_with_report: WorkflowState
    ) -> None:
        """Test routing to end when escalated."""
        state_with_report["critic_feedback"] = CriticFeedback(
            result=ValidationResult.ESCALATED,
            coverage_ok=True,
            allergies_ok=True,
            tone_ok=False,
            feedback="Max retries",
        )
        assert route_next(state_with_report) == NODE_END

    def test_route_to_end_on_error(self, empty_state: WorkflowState) -> None:
        """Test routing to end on error."""
        empty_state["error"] = "Some error occurred"
        assert route_next(empty_state) == NODE_END


class TestShouldContinue:
    """Tests for should_continue function."""

    def test_should_continue_true(self) -> None:
        """Test should_continue returns True when more work needed."""
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[],  # Empty, needs research
            analysis_report=None,
            critic_feedback=None,
            retry_count=0,
            routing_history=[],
            error=None,
        )
        assert should_continue(state) is True

    def test_should_continue_false(self) -> None:
        """Test should_continue returns False when done."""
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water"],
            user_profile=UserProfile(
                allergies=[],
                skin_type=SkinType.NORMAL,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[
                IngredientData(
                    name="water",
                    aliases=[],
                    category="solvent",
                    risk_score=0.0,
                    safety_notes="",
                    source="test",
                    confidence=1.0,
                )
            ],
            analysis_report=AnalysisReport(
                product_name="Test",
                overall_risk=RiskLevel.LOW,
                summary="Safe",
                assessments=[
                    IngredientAssessment(
                        name="water",
                        risk_level=RiskLevel.LOW,
                        rationale="Safe",
                        is_allergen_match=False,
                        alternatives=[],
                    )
                ],
                allergen_warnings=[],
                expertise_tone=ExpertiseLevel.BEGINNER,
            ),
            critic_feedback=CriticFeedback(
                result=ValidationResult.APPROVED,
                coverage_ok=True,
                allergies_ok=True,
                tone_ok=True,
                feedback="Good",
            ),
            retry_count=0,
            routing_history=[],
            error=None,
        )
        assert should_continue(state) is False


class TestGetRoutingDecision:
    """Tests for get_routing_decision function."""

    def test_routing_decision_research(self) -> None:
        """Test human-readable decision for research."""
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
            error=None,
        )
        decision = get_routing_decision(state)
        assert "ingredient" in decision.lower() or "knowledge" in decision.lower()
