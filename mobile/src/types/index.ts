/**
 * Type definitions for the Ingredient Scanner mobile app.
 */

export interface UserProfile {
  allergies: string[];
  skinType: SkinType;
  expertise: ExpertiseLevel;
}

export type SkinType = 'normal' | 'dry' | 'oily' | 'combination' | 'sensitive';

export type ExpertiseLevel = 'beginner' | 'expert';

export type ThemeMode = 'light' | 'dark';

export type RiskLevel = 'low' | 'medium' | 'high';

export interface AnalysisRequest {
  product_name?: string;
  ingredients: string;
  allergies: string[];
  skin_type: SkinType;
  expertise: ExpertiseLevel;
}

/**
 * Detailed ingredient information from analysis.
 */
export interface IngredientDetail {
  name: string;
  purpose: string;
  safety_score: number; // 1-10
  risk_level: RiskLevel;
  concerns: string;
  recommendation: string;
  origin: string; // Natural, Synthetic, Semi-synthetic
  category: string; // Food, Cosmetics, Both
  allergy_risk: string; // High, Low
  is_allergen_match: boolean;
  alternatives: string[];
}

export interface AnalysisResponse {
  success: boolean;
  product_name: string;
  overall_risk: string;
  average_safety_score: number;
  summary: string;
  allergen_warnings: string[];
  ingredients: IngredientDetail[];
  execution_time: number;
  error?: string;
}
