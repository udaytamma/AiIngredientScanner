"""State schema for the ingredient analyzer workflow.

Defines the TypedDict structures for workflow state management,
user profiles, ingredient data, and analysis reports.
"""

from enum import Enum
from typing import TypedDict


class ExpertiseLevel(str, Enum):
    """User expertise level for tone adaptation."""

    BEGINNER = "beginner"
    EXPERT = "expert"


class SkinType(str, Enum):
    """Skin type classification."""

    NORMAL = "normal"
    DRY = "dry"
    OILY = "oily"
    COMBINATION = "combination"
    SENSITIVE = "sensitive"


class RiskLevel(str, Enum):
    """Risk level classification for ingredients/products."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ValidationResult(str, Enum):
    """Critic agent validation outcomes."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class UserProfile(TypedDict):
    """User profile for personalized analysis.

    Attributes:
        allergies: List of known allergens.
        skin_type: User's skin type classification.
        expertise: Expertise level for tone adaptation.
    """

    allergies: list[str]
    skin_type: SkinType
    expertise: ExpertiseLevel


class AllergyRiskFlag(str, Enum):
    """Allergy risk flag classification."""

    HIGH = "high"
    LOW = "low"


class IngredientData(TypedDict):
    """Data for a single ingredient.

    Attributes:
        name: Ingredient name (normalized).
        purpose: What this ingredient does/its function.
        safety_rating: Safety rating (1-10, 10 being safest).
        concerns: Safety concerns in simple language.
        recommendation: Usage recommendation.
        allergy_risk_flag: High or Low allergy risk.
        allergy_potential: Allergy risk for which skin types/conditions.
        origin: Natural, synthetic, or semi-synthetic.
        category: Food, Cosmetics, or Both.
        regulatory_status: US FDA and EU regulatory status.
        regulatory_bans: Whether there are regulatory bans (Yes/No).
        source: Data source (qdrant, google_search).
        confidence: Confidence score for the data (0.0 to 1.0).
        # Legacy fields for backward compatibility
        aliases: Alternative names for the ingredient.
        risk_score: Baseline risk score (0.0 to 1.0) - derived from safety_rating.
        safety_notes: Safety information - derived from concerns.
    """

    name: str
    purpose: str
    safety_rating: int
    concerns: str
    recommendation: str
    allergy_risk_flag: AllergyRiskFlag
    allergy_potential: str
    origin: str
    category: str
    regulatory_status: str
    regulatory_bans: str
    source: str
    confidence: float
    # Legacy fields
    aliases: list[str]
    risk_score: float
    safety_notes: str


class IngredientAssessment(TypedDict):
    """Assessment for a single ingredient in the report.

    Attributes:
        name: Ingredient name.
        risk_level: Classified risk level.
        rationale: Explanation for the risk assessment.
        is_allergen_match: Whether it matches user allergies.
        alternatives: Suggested safer alternatives.
    """

    name: str
    risk_level: RiskLevel
    rationale: str
    is_allergen_match: bool
    alternatives: list[str]


class AnalysisReport(TypedDict):
    """Complete analysis report for a product.

    Attributes:
        product_name: Name of the analyzed product.
        overall_risk: Overall product risk level.
        average_safety_score: Average safety rating (1-10) from LLM analysis.
        summary: Executive summary of the analysis.
        assessments: Per-ingredient assessments.
        allergen_warnings: Specific allergen match warnings.
        expertise_tone: Tone used in the report.
    """

    product_name: str
    overall_risk: RiskLevel
    average_safety_score: int
    summary: str
    assessments: list[IngredientAssessment]
    allergen_warnings: list[str]
    expertise_tone: ExpertiseLevel


class CriticFeedback(TypedDict):
    """Feedback from the critic agent.

    Multi-gate validation results:
    1. Completeness - All ingredients addressed
    2. Format - Proper table structure with required columns
    3. Allergen Match - User allergies properly flagged
    4. Consistency - Safety scores match concern descriptions
    5. Tone - Appropriate for user expertise level

    Attributes:
        result: Validation outcome (APPROVED, REJECTED, ESCALATED).
        completeness_ok: Gate 1 - All ingredients have assessments.
        format_ok: Gate 2 - Proper markdown table structure.
        allergens_ok: Gate 3 - User allergies properly flagged.
        consistency_ok: Gate 4 - Safety scores match concerns.
        tone_ok: Gate 5 - Tone matches expertise level.
        feedback: Detailed feedback for improvements or approval.
        failed_gates: List of gate names that failed validation.
    """

    result: ValidationResult
    completeness_ok: bool
    format_ok: bool
    allergens_ok: bool
    consistency_ok: bool
    tone_ok: bool
    feedback: str
    failed_gates: list[str]


class StageTiming(TypedDict):
    """Timing information for workflow stages.

    Attributes:
        research_time: Time spent in research stage (seconds).
        analysis_time: Time spent in analysis stage (seconds).
        critic_time: Time spent in critic stage (seconds).
    """

    research_time: float
    analysis_time: float
    critic_time: float


class WorkflowState(TypedDict):
    """Complete state for the analysis workflow.

    Attributes:
        session_id: Unique session identifier.
        product_name: Name of the product being analyzed.
        raw_ingredients: Raw ingredient list from user input.
        user_profile: User's personalization profile.
        ingredient_data: Research data for each ingredient.
        analysis_report: Generated analysis report.
        critic_feedback: Feedback from validation.
        retry_count: Number of analysis retries attempted.
        routing_history: History of routing decisions.
        stage_timings: Time spent in each workflow stage.
        error: Error message if workflow failed.
    """

    session_id: str
    product_name: str
    raw_ingredients: list[str]
    user_profile: UserProfile
    ingredient_data: list[IngredientData]
    analysis_report: AnalysisReport | None
    critic_feedback: CriticFeedback | None
    retry_count: int
    routing_history: list[str]
    stage_timings: StageTiming | None
    error: str | None
