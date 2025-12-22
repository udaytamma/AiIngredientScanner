"""Integration tests for the LangGraph workflow."""

from unittest.mock import patch, MagicMock

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


class TestWorkflowCreation:
    """Tests for workflow creation."""

    def test_create_workflow(self) -> None:
        """Test workflow graph is created."""
        from graph import create_workflow
        workflow = create_workflow()
        assert workflow is not None

    def test_compile_workflow(self) -> None:
        """Test workflow compiles successfully."""
        from graph import compile_workflow
        app = compile_workflow()
        assert app is not None


class TestWorkflowExecution:
    """Integration tests for workflow execution."""

    @pytest.fixture
    def mock_research(self) -> MagicMock:
        """Create mock for research agent."""
        def research_fn(state: WorkflowState) -> dict:
            return {
                "ingredient_data": [
                    IngredientData(
                        name="water",
                        aliases=["aqua"],
                        category="solvent",
                        risk_score=0.0,
                        safety_notes="Safe",
                        source="mock",
                        confidence=0.99,
                    ),
                    IngredientData(
                        name="glycerin",
                        aliases=[],
                        category="humectant",
                        risk_score=0.1,
                        safety_notes="Moisturizing",
                        source="mock",
                        confidence=0.95,
                    ),
                ],
                "routing_history": state.get("routing_history", []) + ["research"],
            }
        return MagicMock(side_effect=research_fn)

    @pytest.fixture
    def mock_analysis(self) -> MagicMock:
        """Create mock for analysis agent."""
        def analysis_fn(state: WorkflowState) -> dict:
            return {
                "analysis_report": AnalysisReport(
                    product_name=state["product_name"],
                    overall_risk=RiskLevel.LOW,
                    summary="This product is safe.",
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
                    expertise_tone=state["user_profile"]["expertise"],
                ),
                "routing_history": state.get("routing_history", []) + ["analysis"],
            }
        return MagicMock(side_effect=analysis_fn)

    @pytest.fixture
    def mock_critic_approve(self) -> MagicMock:
        """Create mock for critic agent that approves."""
        def critic_fn(state: WorkflowState) -> dict:
            return {
                "critic_feedback": CriticFeedback(
                    result=ValidationResult.APPROVED,
                    completeness_ok=True,
                    format_ok=True,
                    allergens_ok=True,
                    consistency_ok=True,
                    tone_ok=True,
                    feedback="All validation gates passed.",
                    failed_gates=[],
                ),
                "retry_count": state.get("retry_count", 0),
                "routing_history": state.get("routing_history", []) + ["critic"],
            }
        return MagicMock(side_effect=critic_fn)

    @pytest.fixture
    def initial_state(self) -> WorkflowState:
        """Create initial workflow state."""
        return WorkflowState(
            session_id="test-integration-123",
            product_name="Test Moisturizer",
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

    @patch("agents.research.research_ingredients")
    @patch("agents.analysis.analyze_ingredients")
    @patch("agents.critic.validate_report")
    def test_happy_path(
        self,
        mock_validate: MagicMock,
        mock_analyze: MagicMock,
        mock_research: MagicMock,
        initial_state: WorkflowState,
    ) -> None:
        """Test happy path: research -> analysis -> approve."""
        from graph import compile_workflow

        # Setup mocks
        mock_research.side_effect = lambda s: {
            "ingredient_data": [
                IngredientData(
                    name="water",
                    aliases=[],
                    category="solvent",
                    risk_score=0.0,
                    safety_notes="Safe",
                    source="mock",
                    confidence=0.99,
                ),
                IngredientData(
                    name="glycerin",
                    aliases=[],
                    category="humectant",
                    risk_score=0.1,
                    safety_notes="Safe",
                    source="mock",
                    confidence=0.95,
                ),
            ],
            "routing_history": s.get("routing_history", []) + ["research"],
        }

        mock_analyze.side_effect = lambda s: {
            "analysis_report": AnalysisReport(
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
            ),
            "routing_history": s.get("routing_history", []) + ["analysis"],
        }

        mock_validate.side_effect = lambda s: {
            "critic_feedback": CriticFeedback(
                result=ValidationResult.APPROVED,
                completeness_ok=True,
                format_ok=True,
                allergens_ok=True,
                consistency_ok=True,
                tone_ok=True,
                feedback="All gates passed",
                failed_gates=[],
            ),
            "retry_count": 0,
            "routing_history": s.get("routing_history", []) + ["critic"],
        }

        # Run workflow
        app = compile_workflow()
        final_state = app.invoke(initial_state)

        # Verify
        assert final_state["critic_feedback"]["result"] == ValidationResult.APPROVED
        assert "research" in final_state["routing_history"]
        assert "analysis" in final_state["routing_history"]
        assert "critic" in final_state["routing_history"]

    def test_supervisor_retry_routing(self) -> None:
        """Test supervisor routes to analysis after rejection."""
        from agents.supervisor import route_next

        # State after first rejection
        state = WorkflowState(
            session_id="test",
            product_name="Test",
            raw_ingredients=["water", "glycerin"],
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
                    confidence=0.99,
                ),
                IngredientData(
                    name="glycerin",
                    aliases=[],
                    category="humectant",
                    risk_score=0.1,
                    safety_notes="",
                    source="test",
                    confidence=0.95,
                ),
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
            ),
            critic_feedback=CriticFeedback(
                result=ValidationResult.REJECTED,
                completeness_ok=True,
                format_ok=True,
                allergens_ok=True,
                consistency_ok=True,
                tone_ok=False,
                feedback="Tone does not match expertise level",
                failed_gates=["Tone"],
            ),
            retry_count=1,
            routing_history=["research", "analysis", "critic"],
            error=None,
        )

        # Supervisor should route back to analysis
        next_node = route_next(state)
        assert next_node == "analysis"

    def test_supervisor_escalation_routing(self) -> None:
        """Test supervisor routes to end after escalation."""
        from agents.supervisor import route_next

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
                    confidence=0.99,
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
                result=ValidationResult.ESCALATED,
                completeness_ok=True,
                format_ok=True,
                allergens_ok=True,
                consistency_ok=True,
                tone_ok=False,
                feedback="Max retries exceeded. Failed gates: Tone.",
                failed_gates=["Tone"],
            ),
            retry_count=2,
            routing_history=["research", "analysis", "critic", "analysis", "critic"],
            error=None,
        )

        # Supervisor should route to end
        next_node = route_next(state)
        assert next_node == "end"
