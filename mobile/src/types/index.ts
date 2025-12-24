/**
 * Type Definitions
 *
 * Central type definitions for the AI Ingredient Safety Analyzer mobile application.
 * These types define the data structures used throughout the app for user profiles,
 * API communication, and analysis results.
 *
 * @module types
 * @author Uday Tamma
 * @license MIT
 */

// =============================================================================
// User Profile Types
// =============================================================================

/**
 * User profile containing personalization preferences.
 *
 * Used to customize ingredient analysis based on individual needs,
 * allergies, and skin characteristics.
 */
export interface UserProfile {
  /** List of known allergens to flag during analysis */
  allergies: string[];
  /** User's skin type for cosmetic product recommendations */
  skinType: SkinType;
  /** Preferred explanation complexity level */
  expertise: ExpertiseLevel;
}

/**
 * Supported skin types for personalized cosmetic analysis.
 * Affects how ingredient recommendations are weighted.
 */
export type SkinType = 'normal' | 'dry' | 'oily' | 'combination' | 'sensitive';

/**
 * Expertise level determines the complexity of explanations.
 * - beginner: Simple, accessible language with minimal technical terms
 * - expert: Detailed technical information with chemical names
 */
export type ExpertiseLevel = 'beginner' | 'expert';

// =============================================================================
// Application State Types
// =============================================================================

/**
 * Application theme mode.
 * Supports light and dark color schemes.
 */
export type ThemeMode = 'light' | 'dark';

/**
 * Risk severity levels for ingredient safety assessment.
 * - low: Generally safe for most users
 * - medium: Use with caution, may cause issues for sensitive individuals
 * - high: Potential concerns, consider alternatives
 */
export type RiskLevel = 'low' | 'medium' | 'high';

// =============================================================================
// API Request/Response Types
// =============================================================================

/**
 * Request payload for ingredient analysis API endpoint.
 *
 * Sent to POST /analyze on the backend server.
 */
export interface AnalysisRequest {
  /** Optional product name for context */
  product_name?: string;
  /** Raw ingredient list (comma-separated or space-separated) */
  ingredients: string;
  /** User's known allergies to check against */
  allergies: string[];
  /** User's skin type for personalized recommendations */
  skin_type: SkinType;
  /** Desired complexity level for explanations */
  expertise: ExpertiseLevel;
}

/**
 * Detailed information about a single analyzed ingredient.
 *
 * Returned as part of AnalysisResponse.ingredients array.
 * Contains comprehensive safety data from the AI analysis.
 */
export interface IngredientDetail {
  /** Common name of the ingredient */
  name: string;
  /** Primary function/purpose in the product */
  purpose: string;
  /** Safety score from 1 (dangerous) to 10 (completely safe) */
  safety_score: number;
  /** Categorical risk assessment */
  risk_level: RiskLevel;
  /** Potential concerns or side effects */
  concerns: string;
  /** AI recommendation: SAFE, CAUTION, or AVOID */
  recommendation: string;
  /** Origin classification: Natural, Synthetic, or Semi-synthetic */
  origin: string;
  /** Product category: Food, Cosmetics, or Both */
  category: string;
  /** General allergy risk: High or Low */
  allergy_risk: string;
  /** True if this ingredient matches user's specified allergies */
  is_allergen_match: boolean;
  /** Suggested safer alternatives if concerns exist */
  alternatives: string[];
}

/**
 * Complete response from the ingredient analysis API.
 *
 * Contains overall assessment and detailed breakdown of each ingredient.
 */
export interface AnalysisResponse {
  /** Whether the analysis completed successfully */
  success: boolean;
  /** Product name (from request or 'Unknown Product') */
  product_name: string;
  /** Overall risk assessment: low, medium, or high */
  overall_risk: string;
  /** Average safety score across all ingredients (1-10) */
  average_safety_score: number;
  /** AI-generated summary of the analysis */
  summary: string;
  /** List of allergen warnings based on user's profile */
  allergen_warnings: string[];
  /** Detailed analysis for each identified ingredient */
  ingredients: IngredientDetail[];
  /** Time taken to complete analysis in seconds */
  execution_time: number;
  /** Error message if analysis failed */
  error?: string;
}
