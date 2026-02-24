"""Tests for tool modules."""

from unittest.mock import MagicMock, patch

import pytest

from state.schema import (
    AllergyRiskFlag,
    ExpertiseLevel,
    IngredientData,
    RiskLevel,
    SkinType,
    UserProfile,
)
from tools.safety_scorer import (
    calculate_risk_score,
    classify_risk_level,
    calculate_overall_risk,
)
from tools.allergen_matcher import (
    get_allergen_terms,
    check_allergen_match,
    find_all_allergen_matches,
)
from tools.grounded_search import (
    grounded_ingredient_search,
    _parse_search_response,
)
from tools.ingredient_lookup import (
    get_embedding,
    lookup_ingredient,
)


def _create_ingredient(
    name: str,
    category: str = "unknown",
    risk_score: float = 0.5,
    safety_notes: str = "",
    aliases: list[str] | None = None,
    source: str = "test",
    confidence: float = 0.9,
) -> IngredientData:
    """Helper to create IngredientData with minimal required fields."""
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


class TestSafetyScorer:
    """Tests for safety scoring functions."""

    @pytest.fixture
    def normal_profile(self) -> UserProfile:
        """Create normal skin profile."""
        return UserProfile(
            allergies=[],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

    @pytest.fixture
    def sensitive_profile(self) -> UserProfile:
        """Create sensitive skin profile."""
        return UserProfile(
            allergies=["fragrance"],
            skin_type=SkinType.SENSITIVE,
            expertise=ExpertiseLevel.EXPERT,
        )

    @pytest.fixture
    def low_risk_ingredient(self) -> IngredientData:
        """Create low risk ingredient."""
        return _create_ingredient(
            name="glycerin",
            category="humectant",
            risk_score=0.1,
            safety_notes="Generally safe",
            aliases=["glycerol"],
            source="qdrant",
            confidence=0.95,
        )

    @pytest.fixture
    def fragrance_ingredient(self) -> IngredientData:
        """Create fragrance ingredient."""
        return _create_ingredient(
            name="parfum",
            category="fragrance",
            risk_score=0.4,
            safety_notes="May cause sensitivity",
            aliases=["fragrance"],
            source="qdrant",
            confidence=0.9,
        )

    def test_calculate_risk_normal_skin(
        self,
        low_risk_ingredient: IngredientData,
        normal_profile: UserProfile,
    ) -> None:
        """Test risk calculation for normal skin."""
        risk = calculate_risk_score(low_risk_ingredient, normal_profile)
        assert risk == 0.1  # No modifier applied

    def test_calculate_risk_sensitive_skin_fragrance(
        self,
        fragrance_ingredient: IngredientData,
        sensitive_profile: UserProfile,
    ) -> None:
        """Test risk increases for fragrance with sensitive skin."""
        risk = calculate_risk_score(fragrance_ingredient, sensitive_profile)
        assert risk == 0.7  # 0.4 base + 0.3 modifier

    def test_risk_capped_at_one(
        self,
        sensitive_profile: UserProfile,
    ) -> None:
        """Test risk score is capped at 1.0."""
        high_risk = _create_ingredient(
            name="test",
            category="fragrance",
            risk_score=0.9,
            confidence=1.0,
        )
        risk = calculate_risk_score(high_risk, sensitive_profile)
        assert risk == 1.0

    def test_classify_risk_level_low(self) -> None:
        """Test low risk classification."""
        assert classify_risk_level(0.0) == RiskLevel.LOW
        assert classify_risk_level(0.29) == RiskLevel.LOW

    def test_classify_risk_level_medium(self) -> None:
        """Test medium risk classification."""
        assert classify_risk_level(0.3) == RiskLevel.MEDIUM
        assert classify_risk_level(0.59) == RiskLevel.MEDIUM

    def test_classify_risk_level_high(self) -> None:
        """Test high risk classification."""
        assert classify_risk_level(0.6) == RiskLevel.HIGH
        assert classify_risk_level(1.0) == RiskLevel.HIGH

    def test_calculate_overall_risk_empty(self) -> None:
        """Test overall risk with no ingredients."""
        assert calculate_overall_risk([]) == RiskLevel.LOW

    def test_calculate_overall_risk_all_low(self) -> None:
        """Test overall risk when all are low."""
        assert calculate_overall_risk([0.1, 0.2, 0.1]) == RiskLevel.LOW

    def test_calculate_overall_risk_one_high(self) -> None:
        """Test overall risk with one high ingredient."""
        # One high (0.8), rest low -> weighted should be high
        result = calculate_overall_risk([0.8, 0.1, 0.1])
        assert result == RiskLevel.HIGH


class TestAllergenMatcher:
    """Tests for allergen matching functions."""

    @pytest.fixture
    def profile_with_allergies(self) -> UserProfile:
        """Create profile with allergies."""
        return UserProfile(
            allergies=["peanut", "milk"],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

    @pytest.fixture
    def profile_no_allergies(self) -> UserProfile:
        """Create profile without allergies."""
        return UserProfile(
            allergies=[],
            skin_type=SkinType.NORMAL,
            expertise=ExpertiseLevel.BEGINNER,
        )

    def test_get_allergen_terms_known(self) -> None:
        """Test getting terms for known allergen."""
        terms = get_allergen_terms("milk")
        assert "milk" in terms
        assert "dairy" in terms
        assert "lactose" in terms

    def test_get_allergen_terms_unknown(self) -> None:
        """Test getting terms for unknown allergen."""
        terms = get_allergen_terms("unknown_allergen")
        assert terms == ["unknown_allergen"]

    def test_check_allergen_match_positive(
        self,
        profile_with_allergies: UserProfile,
    ) -> None:
        """Test positive allergen match."""
        ingredient = _create_ingredient(
            name="whey protein",
            category="protein",
            risk_score=0.2,
            safety_notes="Derived from milk",
            aliases=["whey"],
        )
        is_match, allergy = check_allergen_match(ingredient, profile_with_allergies)
        assert is_match is True
        assert allergy == "milk"

    def test_check_allergen_match_negative(
        self,
        profile_with_allergies: UserProfile,
    ) -> None:
        """Test no allergen match."""
        ingredient = _create_ingredient(
            name="water",
            category="solvent",
            risk_score=0.0,
            safety_notes="Safe",
            aliases=["aqua"],
            confidence=1.0,
        )
        is_match, allergy = check_allergen_match(ingredient, profile_with_allergies)
        assert is_match is False
        assert allergy is None

    def test_check_allergen_no_allergies(
        self,
        profile_no_allergies: UserProfile,
    ) -> None:
        """Test with no user allergies."""
        ingredient = _create_ingredient(
            name="peanut oil",
            category="oil",
            risk_score=0.3,
        )
        is_match, allergy = check_allergen_match(ingredient, profile_no_allergies)
        assert is_match is False

    def test_find_all_allergen_matches(
        self,
        profile_with_allergies: UserProfile,
    ) -> None:
        """Test finding all allergen matches."""
        ingredients = [
            _create_ingredient(
                name="water",
                category="solvent",
                risk_score=0.0,
                confidence=1.0,
            ),
            _create_ingredient(
                name="casein",
                category="protein",
                risk_score=0.2,
                safety_notes="Milk protein",
            ),
            _create_ingredient(
                name="arachis oil",
                category="oil",
                risk_score=0.3,
                aliases=["peanut oil"],
            ),
        ]
        matches = find_all_allergen_matches(ingredients, profile_with_allergies)
        assert len(matches) == 2
        assert any(m["allergy"] == "milk" for m in matches)
        assert any(m["allergy"] == "peanut" for m in matches)


class TestGroundedSearch:
    """Tests for grounded search tool (Google AI Studio)."""

    def test_parse_search_response_complete(self) -> None:
        """Test parsing a complete response with new schema."""
        response = """INGREDIENT_NAME: Glycerin
PURPOSE: Humectant that attracts moisture to skin
SAFETY_RATING: 9
CONCERNS: Generally safe, minimal concerns
RECOMMENDATION: Safe for daily use
ALLERGY_RISK_FLAG: Low
ALLERGY_POTENTIAL: Rare allergic reactions
ORIGIN: Natural or synthetic
CATEGORY: Cosmetics
REGULATORY_STATUS: Approved by FDA and EU
REGULATORY_BANS: No"""

        result = _parse_search_response("glycerin", response)

        assert result["name"] == "Glycerin"
        assert result["purpose"] == "Humectant that attracts moisture to skin"
        assert result["safety_rating"] == 9
        assert result["concerns"] == "Generally safe, minimal concerns"
        assert result["recommendation"] == "Safe for daily use"
        assert result["allergy_risk_flag"].value == "low"
        assert result["origin"] == "Natural or synthetic"
        assert result["category"] == "Cosmetics"
        assert result["regulatory_status"] == "Approved by FDA and EU"
        assert result["regulatory_bans"] == "No"
        assert result["source"] == "google_search"
        assert result["confidence"] == 0.8
        # Check legacy field derived from safety_rating
        assert result["risk_score"] == 0.1  # (10-9)/10 = 0.1

    def test_parse_search_response_partial(self) -> None:
        """Test parsing response with missing fields."""
        response = """INGREDIENT_NAME: Unknown Ingredient
CONCERNS: No data found."""

        result = _parse_search_response("test_ingredient", response)

        assert result["name"] == "Unknown Ingredient"
        assert result["purpose"] == "Unknown purpose"
        assert result["safety_rating"] == 5  # Default
        assert result["category"] == "Unknown"
        assert result["confidence"] == 0.8

    def test_parse_search_response_invalid_safety_rating(self) -> None:
        """Test parsing with invalid safety rating defaults to 5."""
        response = """INGREDIENT_NAME: Test
SAFETY_RATING: invalid"""

        result = _parse_search_response("test", response)
        assert result["safety_rating"] == 5
        assert result["risk_score"] == 0.5  # (10-5)/10 = 0.5

    def test_parse_search_response_high_allergy_risk(self) -> None:
        """Test parsing with high allergy risk flag."""
        response = """INGREDIENT_NAME: Test Allergen
ALLERGY_RISK_FLAG: High"""

        result = _parse_search_response("test", response)
        assert result["allergy_risk_flag"].value == "high"

    def test_grounded_search_not_configured(self) -> None:
        """Test returns None when Google AI not configured."""
        with patch("tools.grounded_search.get_settings") as mock_settings:
            mock_settings.return_value.is_configured.return_value = False

            result = grounded_ingredient_search("test")
            assert result is None

    def test_grounded_search_success(self) -> None:
        """Test successful grounded search with new schema."""
        with patch("tools.grounded_search._get_genai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = """INGREDIENT_NAME: Sodium Lauryl Sulfate
PURPOSE: Surfactant and cleansing agent
SAFETY_RATING: 6
CONCERNS: Can cause irritation for sensitive skin
RECOMMENDATION: Use in rinse-off products only
ALLERGY_RISK_FLAG: Low
ALLERGY_POTENTIAL: May irritate sensitive skin
ORIGIN: Synthetic
CATEGORY: Cosmetics
REGULATORY_STATUS: Approved with restrictions
REGULATORY_BANS: No"""
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            with patch("tools.grounded_search.get_settings") as mock_settings:
                mock_settings.return_value.gemini_model = "gemini-3-flash-preview"

                with patch("tools.grounded_search._save_to_qdrant"):
                    result = grounded_ingredient_search("sodium lauryl sulfate")

                    assert result is not None
                    assert result["name"] == "Sodium Lauryl Sulfate"
                    assert result["purpose"] == "Surfactant and cleansing agent"
                    assert result["safety_rating"] == 6
                    assert result["category"] == "Cosmetics"
                    assert result["risk_score"] == 0.4  # (10-6)/10


class TestIngredientLookup:
    """Tests for ingredient lookup tool (Google AI Studio embeddings)."""

    def test_get_embedding_not_configured(self) -> None:
        """Test embedding fails when not configured."""
        with patch("tools.ingredient_lookup.get_settings") as mock_settings:
            mock_settings.return_value.is_configured.return_value = False

            with pytest.raises(ValueError, match="Google AI not configured"):
                get_embedding("test")

    def test_get_embedding_success(self) -> None:
        """Test successful embedding generation."""
        with patch("tools.ingredient_lookup._get_genai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_embedding = MagicMock()
            mock_embedding.values = [0.1] * 768
            mock_result.embeddings = [mock_embedding]
            mock_client.models.embed_content.return_value = mock_result
            mock_get_client.return_value = mock_client

            result = get_embedding("test ingredient")

            assert len(result) == 768
            mock_client.models.embed_content.assert_called_once()

    def test_lookup_ingredient_not_configured(self) -> None:
        """Test lookup returns None when Qdrant not configured."""
        with patch("tools.ingredient_lookup.get_settings") as mock_settings:
            mock_settings.return_value.is_configured.return_value = False

            result = lookup_ingredient("test")
            assert result is None

    def test_lookup_ingredient_no_match(self) -> None:
        """Test lookup returns None when no match found."""
        with patch("tools.ingredient_lookup.get_qdrant_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.search.return_value = []
            mock_get_client.return_value = mock_client

            with patch("tools.ingredient_lookup.ensure_collection_exists"):
                with patch("tools.ingredient_lookup.get_embedding") as mock_embed:
                    mock_embed.return_value = [0.1] * 768

                    result = lookup_ingredient("unknown_ingredient")
                    assert result is None
