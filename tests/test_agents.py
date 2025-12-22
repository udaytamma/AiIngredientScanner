"""Tests for agent modules."""

from unittest.mock import patch, MagicMock

import pytest

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
from agents.research import (
    research_ingredients,
    has_research_data,
    _create_unknown_ingredient,
    _create_batches,
    _research_sequential,
    BATCH_SIZE,
)
from agents.analysis import (
    analyze_ingredients,
    has_analysis_report,
    _generate_fallback_summary,
    _generate_llm_analysis,
    _calculate_assessments,
    _generate_rationale,
    _suggest_alternatives,
)
from agents.critic import (
    validate_report,
    is_approved,
    is_rejected,
    is_escalated,
    _parse_validation_response,
    _gate_failed,
)


def _create_test_ingredient(
    name: str,
    category: str = "unknown",
    risk_score: float = 0.5,
    safety_notes: str = "",
    aliases: list[str] | None = None,
    source: str = "test",
    confidence: float = 0.9,
) -> IngredientData:
    """Helper to create IngredientData with all required fields."""
    return IngredientData(
        name=name,
        purpose="Test purpose",
        safety_rating=int((1 - risk_score) * 10),
        concerns=safety_notes or "No concerns",
        recommendation="Use as directed",
        allergy_risk_flag=AllergyRiskFlag.LOW,
        allergy_potential="Unknown",
        origin="Unknown",
        category=category,
        regulatory_status="Unknown",
        regulatory_bans="No",
        source=source,
        confidence=confidence,
        # Legacy fields
        aliases=aliases or [],
        risk_score=risk_score,
        safety_notes=safety_notes,
    )


class TestResearchAgent:
    """Tests for Research Agent."""

    @pytest.fixture
    def base_state(self) -> WorkflowState:
        """Create base workflow state."""
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

    def test_create_unknown_ingredient(self) -> None:
        """Test creation of unknown ingredient record."""
        result = _create_unknown_ingredient("mystery_ingredient")
        assert result["name"] == "mystery_ingredient"
        assert result["source"] == "unknown"
        assert result["confidence"] == 0.0
        assert result["risk_score"] == 0.5

    def test_has_research_data_false(self, base_state: WorkflowState) -> None:
        """Test has_research_data returns False when empty."""
        assert has_research_data(base_state) is False

    def test_has_research_data_true(self, base_state: WorkflowState) -> None:
        """Test has_research_data returns True when populated."""
        base_state["ingredient_data"] = [
            _create_unknown_ingredient("water"),
            _create_unknown_ingredient("glycerin"),
        ]
        assert has_research_data(base_state) is True

    @patch("agents.research.lookup_ingredient")
    @patch("agents.research.grounded_ingredient_search")
    def test_research_ingredients_fallback(
        self,
        mock_search: MagicMock,
        mock_lookup: MagicMock,
        base_state: WorkflowState,
    ) -> None:
        """Test research falls back to grounded search."""
        # Qdrant returns low confidence
        mock_lookup.return_value = _create_test_ingredient(
            name="water",
            category="solvent",
            risk_score=0.0,
            source="qdrant",
            confidence=0.5,  # Below threshold
        )
        # Grounded search provides result
        mock_search.return_value = _create_test_ingredient(
            name="water",
            category="solvent",
            risk_score=0.0,
            safety_notes="Universal solvent",
            aliases=["aqua"],
            source="google_search",
            confidence=0.8,
        )

        base_state["raw_ingredients"] = ["water"]
        result = research_ingredients(base_state)

        assert len(result["ingredient_data"]) == 1
        assert result["ingredient_data"][0]["source"] == "google_search"
        assert "research" in result["routing_history"]

    def test_create_batches_small(self) -> None:
        """Test batch creation with small list."""
        items = ["a", "b"]
        batches = _create_batches(items, BATCH_SIZE)
        assert len(batches) == 1
        assert batches[0] == ["a", "b"]

    def test_create_batches_exact(self) -> None:
        """Test batch creation with exact batch size."""
        items = ["a", "b", "c"]
        batches = _create_batches(items, BATCH_SIZE)
        assert len(batches) == 1
        assert batches[0] == ["a", "b", "c"]

    def test_create_batches_multiple(self) -> None:
        """Test batch creation with multiple batches."""
        items = ["a", "b", "c", "d", "e", "f", "g"]
        batches = _create_batches(items, BATCH_SIZE)
        assert len(batches) == 3
        assert batches[0] == ["a", "b", "c"]
        assert batches[1] == ["d", "e", "f"]
        assert batches[2] == ["g"]

    def test_batch_size_constant(self) -> None:
        """Verify BATCH_SIZE is set to 3."""
        assert BATCH_SIZE == 3

    @patch("agents.research.lookup_ingredient")
    @patch("agents.research.grounded_ingredient_search")
    def test_parallel_research_large_list(
        self,
        mock_search: MagicMock,
        mock_lookup: MagicMock,
        base_state: WorkflowState,
    ) -> None:
        """Test parallel research with more than BATCH_SIZE ingredients."""
        # Mock both to return known ingredients
        mock_lookup.return_value = None
        mock_search.side_effect = lambda name: _create_test_ingredient(
            name=name,
            category="test",
            source="google_search",
            confidence=0.9,
        )

        # 7 ingredients should spawn 3 workers
        base_state["raw_ingredients"] = [
            "water", "glycerin", "fragrance",
            "alcohol", "phenoxyethanol", "vitamin_e",
            "retinol",
        ]
        result = research_ingredients(base_state)

        assert len(result["ingredient_data"]) == 7
        # All should be from google_search
        for data in result["ingredient_data"]:
            assert data["source"] == "google_search"
        assert "research" in result["routing_history"]

    def test_sequential_research(self) -> None:
        """Test sequential research helper."""
        with patch("agents.research._research_single_ingredient") as mock_research:
            mock_research.return_value = _create_test_ingredient(
                name="test", source="mock", confidence=0.9
            )
            results = _research_sequential(["a", "b"])
            assert len(results) == 2
            assert mock_research.call_count == 2


class TestAnalysisAgent:
    """Tests for Analysis Agent."""

    @pytest.fixture
    def state_with_data(self) -> WorkflowState:
        """Create state with ingredient data."""
        return WorkflowState(
            session_id="test-123",
            product_name="Test Moisturizer",
            raw_ingredients=["water", "glycerin", "fragrance"],
            user_profile=UserProfile(
                allergies=["fragrance"],
                skin_type=SkinType.SENSITIVE,
                expertise=ExpertiseLevel.BEGINNER,
            ),
            ingredient_data=[
                _create_test_ingredient(
                    name="water",
                    category="solvent",
                    risk_score=0.0,
                    safety_notes="Safe",
                    aliases=["aqua"],
                    source="qdrant",
                    confidence=0.99,
                ),
                _create_test_ingredient(
                    name="glycerin",
                    category="humectant",
                    risk_score=0.1,
                    safety_notes="Moisturizing",
                    source="qdrant",
                    confidence=0.95,
                ),
                _create_test_ingredient(
                    name="fragrance",
                    category="fragrance",
                    risk_score=0.4,
                    safety_notes="May irritate",
                    aliases=["parfum"],
                    source="qdrant",
                    confidence=0.9,
                ),
            ],
            analysis_report=None,
            critic_feedback=None,
            retry_count=0,
            routing_history=["research"],
            error=None,
        )

    @pytest.fixture
    def beginner_profile(self) -> UserProfile:
        """Create beginner user profile."""
        return UserProfile(
            allergies=[],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

    def test_has_analysis_report_false(self, state_with_data: WorkflowState) -> None:
        """Test has_analysis_report returns False when missing."""
        assert has_analysis_report(state_with_data) is False

    @patch("agents.analysis._generate_llm_analysis")
    def test_analyze_ingredients(
        self,
        mock_llm: MagicMock,
        state_with_data: WorkflowState,
    ) -> None:
        """Test analysis generates report."""
        mock_llm.return_value = "## Ingredient Analysis\n\nTest analysis."

        result = analyze_ingredients(state_with_data)

        assert "analysis_report" in result
        report = result["analysis_report"]
        assert report["product_name"] == "Test Moisturizer"
        assert len(report["assessments"]) == 3
        assert "analysis" in result["routing_history"]

    @patch("agents.analysis._generate_llm_analysis")
    def test_allergen_flagged(
        self,
        mock_llm: MagicMock,
        state_with_data: WorkflowState,
    ) -> None:
        """Test allergen is properly flagged."""
        mock_llm.return_value = "## Ingredient Analysis\n\nTest analysis."

        result = analyze_ingredients(state_with_data)
        report = result["analysis_report"]

        # Find fragrance assessment
        fragrance_assessment = next(
            a for a in report["assessments"] if a["name"] == "fragrance"
        )
        assert fragrance_assessment["is_allergen_match"] is True
        assert fragrance_assessment["risk_level"] == RiskLevel.HIGH

        # Check allergen warning exists
        assert len(report["allergen_warnings"]) > 0

    def test_generate_fallback_summary(self, beginner_profile: UserProfile) -> None:
        """Test fallback summary generation."""
        ingredient_data = [
            _create_test_ingredient(
                name="water",
                risk_score=0.0,
                safety_notes="Safe",
            )
        ]
        summary = _generate_fallback_summary(ingredient_data, beginner_profile)
        assert "Ingredient Analysis" in summary
        assert "Analyzed 1 ingredients" in summary

    def test_generate_fallback_summary_with_high_risk(
        self, beginner_profile: UserProfile
    ) -> None:
        """Test fallback summary includes warning for high risk."""
        ingredient_data = [
            _create_test_ingredient(
                name="risky",
                risk_score=0.8,  # High risk -> safety_rating 2
                safety_notes="Very risky",
            )
        ]
        summary = _generate_fallback_summary(ingredient_data, beginner_profile)
        assert "Warning" in summary
        assert "CAUTION" in summary

    def test_calculate_assessments(self, state_with_data: WorkflowState) -> None:
        """Test calculate_assessments generates structured data."""
        assessments, warnings, scores = _calculate_assessments(
            state_with_data["ingredient_data"],
            state_with_data["user_profile"],
        )

        assert len(assessments) == 3
        assert len(scores) == 3

        # Check fragrance is flagged as allergen
        fragrance_assessment = next(
            a for a in assessments if a["name"] == "fragrance"
        )
        assert fragrance_assessment["is_allergen_match"] is True
        assert len(warnings) > 0

    @patch("agents.analysis._get_genai_client")
    @patch("agents.analysis.get_settings")
    def test_generate_llm_analysis_success(
        self,
        mock_settings: MagicMock,
        mock_get_client: MagicMock,
        state_with_data: WorkflowState,
    ) -> None:
        """Test LLM analysis generation succeeds."""
        mock_settings.return_value.gemini_model = "gemini-2.0-flash"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "## Ingredient Analysis\n\nTest LLM response."
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        with patch("agents.analysis.get_gemini_logger") as mock_logger:
            mock_logger.return_value.log_interaction = MagicMock()
            result = _generate_llm_analysis(
                state_with_data["ingredient_data"],
                state_with_data["user_profile"],
            )

        assert "Test LLM response" in result
        mock_client.models.generate_content.assert_called_once()

    @patch("agents.analysis._get_genai_client")
    def test_generate_llm_analysis_fallback_on_error(
        self,
        mock_get_client: MagicMock,
        state_with_data: WorkflowState,
    ) -> None:
        """Test LLM analysis falls back on error."""
        mock_get_client.side_effect = Exception("API Error")

        result = _generate_llm_analysis(
            state_with_data["ingredient_data"],
            state_with_data["user_profile"],
        )

        # Should return fallback summary
        assert "Ingredient Analysis" in result
        assert "Analyzed" in result

    def test_generate_rationale_beginner(self) -> None:
        """Test rationale generation for beginner level."""
        ingredient = _create_test_ingredient(
            name="test",
            risk_score=0.2,
            safety_notes="Some concerns",
        )
        rationale = _generate_rationale(
            ingredient=ingredient,
            risk_level=RiskLevel.LOW,
            is_allergen=False,
            matched_allergy=None,
            expertise=ExpertiseLevel.BEGINNER,
        )
        assert "safe" in rationale.lower()

    def test_generate_rationale_expert(self) -> None:
        """Test rationale generation for expert level."""
        ingredient = _create_test_ingredient(
            name="test",
            risk_score=0.2,
            safety_notes="Some concerns",
        )
        rationale = _generate_rationale(
            ingredient=ingredient,
            risk_level=RiskLevel.LOW,
            is_allergen=False,
            matched_allergy=None,
            expertise=ExpertiseLevel.EXPERT,
        )
        assert "rating" in rationale.lower()

    def test_generate_rationale_with_allergen(self) -> None:
        """Test rationale includes allergen warning."""
        ingredient = _create_test_ingredient(
            name="fragrance",
            category="fragrance",
            risk_score=0.4,
        )
        rationale = _generate_rationale(
            ingredient=ingredient,
            risk_level=RiskLevel.HIGH,
            is_allergen=True,
            matched_allergy="fragrance",
            expertise=ExpertiseLevel.BEGINNER,
        )
        assert "warning" in rationale.lower()
        assert "fragrance" in rationale.lower()

    def test_suggest_alternatives_preservative(self) -> None:
        """Test alternatives for preservative category."""
        ingredient = _create_test_ingredient(
            name="paraben",
            category="preservative",
            risk_score=0.5,
        )
        alternatives = _suggest_alternatives(ingredient, RiskLevel.MEDIUM)
        assert len(alternatives) > 0
        assert any("tocopherol" in alt.lower() for alt in alternatives)

    def test_suggest_alternatives_fragrance(self) -> None:
        """Test alternatives for fragrance category."""
        ingredient = _create_test_ingredient(
            name="parfum",
            category="fragrance",
            risk_score=0.6,
        )
        alternatives = _suggest_alternatives(ingredient, RiskLevel.HIGH)
        assert len(alternatives) > 0
        assert any("fragrance-free" in alt.lower() for alt in alternatives)

    def test_suggest_alternatives_low_risk_empty(self) -> None:
        """Test no alternatives for low risk ingredients."""
        ingredient = _create_test_ingredient(
            name="water",
            category="solvent",
            risk_score=0.0,
        )
        alternatives = _suggest_alternatives(ingredient, RiskLevel.LOW)
        assert alternatives == []

    def test_has_analysis_report_true(self, state_with_data: WorkflowState) -> None:
        """Test has_analysis_report returns True when report exists."""
        state_with_data["analysis_report"] = AnalysisReport(
            product_name="Test",
            overall_risk=RiskLevel.LOW,
            summary="Test summary",
            assessments=[],
            allergen_warnings=[],
            expertise_tone=ExpertiseLevel.BEGINNER,
        )
        assert has_analysis_report(state_with_data) is True


class TestCriticAgent:
    """Tests for Critic Agent with multi-gate validation."""

    @pytest.fixture
    def good_report(self) -> AnalysisReport:
        """Create a good quality report."""
        return AnalysisReport(
            product_name="Test Product",
            overall_risk=RiskLevel.LOW,
            summary="| Ingredient | Purpose | Safety Rating | Concerns | Recommendation |\n|---|---|---|---|---|\n| water | solvent | 10 | None | Safe |",
            assessments=[
                IngredientAssessment(
                    name="water",
                    risk_level=RiskLevel.LOW,
                    rationale="Safe ingredient",
                    is_allergen_match=False,
                    alternatives=[],
                ),
                IngredientAssessment(
                    name="glycerin",
                    risk_level=RiskLevel.LOW,
                    rationale="Safe moisturizer",
                    is_allergen_match=False,
                    alternatives=[],
                ),
            ],
            allergen_warnings=[],
            expertise_tone=ExpertiseLevel.BEGINNER,
        )

    @pytest.fixture
    def state_with_report(self, good_report: AnalysisReport) -> WorkflowState:
        """Create state with analysis report."""
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
            analysis_report=good_report,
            critic_feedback=None,
            retry_count=0,
            routing_history=["research", "analysis"],
            error=None,
        )

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
        assert len(result["failed_gates"]) == 0

    def test_parse_reject_response(self) -> None:
        """Test parsing REJECT response with gate failures."""
        response = """REJECT
Gate failures:
- Completeness check failed
Specific issues:
- Missing ingredients
Required fixes:
- Add all ingredients"""
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

    def test_gate_failed_detection(self) -> None:
        """Test gate failure pattern detection."""
        assert _gate_failed("completeness check failed", "completeness") is True
        assert _gate_failed("format violation detected", "format") is True
        assert _gate_failed("tone is fine", "tone") is False

    @patch("agents.critic._run_multi_gate_validation")
    def test_validate_report_approved(
        self,
        mock_validation: MagicMock,
        state_with_report: WorkflowState,
    ) -> None:
        """Test report approval when all gates pass."""
        mock_validation.return_value = {
            "completeness_ok": True,
            "format_ok": True,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": [],
            "feedback": "All gates passed",
        }

        result = validate_report(state_with_report)

        assert result["critic_feedback"]["result"] == ValidationResult.APPROVED
        assert result["critic_feedback"]["completeness_ok"] is True
        assert result["critic_feedback"]["failed_gates"] == []

    @patch("agents.critic._run_multi_gate_validation")
    def test_validate_report_rejected(
        self,
        mock_validation: MagicMock,
        state_with_report: WorkflowState,
    ) -> None:
        """Test report rejection when gates fail."""
        mock_validation.return_value = {
            "completeness_ok": True,
            "format_ok": False,
            "allergens_ok": True,
            "consistency_ok": True,
            "tone_ok": True,
            "failed_gates": ["Format"],
            "feedback": "Format check failed",
        }

        result = validate_report(state_with_report)

        assert result["critic_feedback"]["result"] == ValidationResult.REJECTED
        assert result["critic_feedback"]["format_ok"] is False
        assert "Format" in result["critic_feedback"]["failed_gates"]
        assert result["retry_count"] == 1

    @patch("agents.critic._run_multi_gate_validation")
    @patch("agents.critic.get_settings")
    def test_validate_report_escalated(
        self,
        mock_settings: MagicMock,
        mock_validation: MagicMock,
        state_with_report: WorkflowState,
    ) -> None:
        """Test escalation after max retries."""
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

        state_with_report["retry_count"] = 2  # Already at max

        result = validate_report(state_with_report)

        assert result["critic_feedback"]["result"] == ValidationResult.ESCALATED
        assert "Consistency" in result["critic_feedback"]["failed_gates"]

    def test_is_approved(self) -> None:
        """Test is_approved helper with new schema."""
        state: WorkflowState = {
            "session_id": "",
            "product_name": "",
            "raw_ingredients": [],
            "user_profile": {"allergies": [], "skin_type": SkinType.NORMAL, "expertise": ExpertiseLevel.BEGINNER},
            "ingredient_data": [],
            "analysis_report": None,
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
            "routing_history": [],
            "error": None,
        }
        assert is_approved(state) is True
        assert is_rejected(state) is False

    def test_is_rejected(self) -> None:
        """Test is_rejected helper with new schema."""
        state: WorkflowState = {
            "session_id": "",
            "product_name": "",
            "raw_ingredients": [],
            "user_profile": {"allergies": [], "skin_type": SkinType.NORMAL, "expertise": ExpertiseLevel.BEGINNER},
            "ingredient_data": [],
            "analysis_report": None,
            "critic_feedback": CriticFeedback(
                result=ValidationResult.REJECTED,
                completeness_ok=True,
                format_ok=True,
                allergens_ok=True,
                consistency_ok=True,
                tone_ok=False,
                feedback="Tone does not match expertise level",
                failed_gates=["Tone"],
            ),
            "retry_count": 1,
            "routing_history": [],
            "error": None,
        }
        assert is_rejected(state) is True
        assert is_approved(state) is False
