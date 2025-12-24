/**
 * Type Definitions Unit Tests
 *
 * Tests to ensure type definitions are correct and complete.
 * These tests verify the structure of data types used throughout the app.
 *
 * @module __tests__/types.test
 */

import {
  UserProfile,
  SkinType,
  ExpertiseLevel,
  ThemeMode,
  RiskLevel,
  AnalysisRequest,
  IngredientDetail,
  AnalysisResponse,
} from '../src/types';

describe('UserProfile type', () => {
  it('should accept valid user profile', () => {
    const profile: UserProfile = {
      allergies: ['Fragrance', 'Sulfates'],
      skinType: 'sensitive',
      expertise: 'beginner',
    };

    expect(profile.allergies).toHaveLength(2);
    expect(profile.skinType).toBe('sensitive');
    expect(profile.expertise).toBe('beginner');
  });

  it('should accept empty allergies array', () => {
    const profile: UserProfile = {
      allergies: [],
      skinType: 'normal',
      expertise: 'expert',
    };

    expect(profile.allergies).toHaveLength(0);
  });
});

describe('SkinType type', () => {
  it('should accept all valid skin types', () => {
    const skinTypes: SkinType[] = ['normal', 'dry', 'oily', 'combination', 'sensitive'];

    skinTypes.forEach((type) => {
      const profile: UserProfile = {
        allergies: [],
        skinType: type,
        expertise: 'beginner',
      };
      expect(profile.skinType).toBe(type);
    });
  });
});

describe('ExpertiseLevel type', () => {
  it('should accept beginner level', () => {
    const level: ExpertiseLevel = 'beginner';
    expect(level).toBe('beginner');
  });

  it('should accept expert level', () => {
    const level: ExpertiseLevel = 'expert';
    expect(level).toBe('expert');
  });
});

describe('ThemeMode type', () => {
  it('should accept light mode', () => {
    const mode: ThemeMode = 'light';
    expect(mode).toBe('light');
  });

  it('should accept dark mode', () => {
    const mode: ThemeMode = 'dark';
    expect(mode).toBe('dark');
  });
});

describe('RiskLevel type', () => {
  it('should accept all risk levels', () => {
    const riskLevels: RiskLevel[] = ['low', 'medium', 'high'];

    riskLevels.forEach((level) => {
      expect(['low', 'medium', 'high']).toContain(level);
    });
  });
});

describe('AnalysisRequest type', () => {
  it('should accept request with all fields', () => {
    const request: AnalysisRequest = {
      product_name: 'Test Product',
      ingredients: 'Water, Glycerin',
      allergies: ['Fragrance'],
      skin_type: 'sensitive',
      expertise: 'beginner',
    };

    expect(request.product_name).toBe('Test Product');
    expect(request.ingredients).toBe('Water, Glycerin');
    expect(request.allergies).toContain('Fragrance');
  });

  it('should accept request without optional product_name', () => {
    const request: AnalysisRequest = {
      ingredients: 'Water, Glycerin',
      allergies: [],
      skin_type: 'normal',
      expertise: 'expert',
    };

    expect(request.product_name).toBeUndefined();
    expect(request.ingredients).toBeDefined();
  });
});

describe('IngredientDetail type', () => {
  it('should have all required properties', () => {
    const ingredient: IngredientDetail = {
      name: 'Glycerin',
      purpose: 'Humectant',
      safety_score: 9,
      risk_level: 'low',
      concerns: 'No specific concerns',
      recommendation: 'SAFE',
      origin: 'Natural',
      category: 'Both',
      allergy_risk: 'Low',
      is_allergen_match: false,
      alternatives: [],
    };

    expect(ingredient.name).toBe('Glycerin');
    expect(ingredient.safety_score).toBe(9);
    expect(ingredient.risk_level).toBe('low');
    expect(ingredient.is_allergen_match).toBe(false);
  });

  it('should accept non-empty alternatives array', () => {
    const ingredient: IngredientDetail = {
      name: 'Parabens',
      purpose: 'Preservative',
      safety_score: 4,
      risk_level: 'medium',
      concerns: 'Potential endocrine disruptor',
      recommendation: 'CAUTION',
      origin: 'Synthetic',
      category: 'Cosmetics',
      allergy_risk: 'Low',
      is_allergen_match: false,
      alternatives: ['Phenoxyethanol', 'Potassium Sorbate', 'Sodium Benzoate'],
    };

    expect(ingredient.alternatives).toHaveLength(3);
    expect(ingredient.alternatives).toContain('Phenoxyethanol');
  });

  it('should indicate allergen match correctly', () => {
    const allergenIngredient: IngredientDetail = {
      name: 'Fragrance',
      purpose: 'Scent',
      safety_score: 3,
      risk_level: 'high',
      concerns: 'Common allergen',
      recommendation: 'AVOID',
      origin: 'Synthetic',
      category: 'Cosmetics',
      allergy_risk: 'High',
      is_allergen_match: true,
      alternatives: ['Essential Oils', 'Fragrance-free alternatives'],
    };

    expect(allergenIngredient.is_allergen_match).toBe(true);
    expect(allergenIngredient.risk_level).toBe('high');
  });
});

describe('AnalysisResponse type', () => {
  it('should represent successful analysis', () => {
    const response: AnalysisResponse = {
      success: true,
      product_name: 'Moisturizer',
      overall_risk: 'low',
      average_safety_score: 8.5,
      summary: 'This product is generally safe.',
      allergen_warnings: [],
      ingredients: [],
      execution_time: 2.5,
    };

    expect(response.success).toBe(true);
    expect(response.overall_risk).toBe('low');
    expect(response.error).toBeUndefined();
  });

  it('should represent failed analysis with error', () => {
    const response: AnalysisResponse = {
      success: false,
      product_name: 'Unknown',
      overall_risk: 'unknown',
      average_safety_score: 0,
      summary: '',
      allergen_warnings: [],
      ingredients: [],
      execution_time: 0,
      error: 'Failed to analyze ingredients',
    };

    expect(response.success).toBe(false);
    expect(response.error).toBe('Failed to analyze ingredients');
  });

  it('should contain allergen warnings when applicable', () => {
    const response: AnalysisResponse = {
      success: true,
      product_name: 'Test Product',
      overall_risk: 'medium',
      average_safety_score: 6,
      summary: 'Contains known allergens',
      allergen_warnings: [
        'Contains Fragrance - matches your allergy profile',
        'Contains Sulfates - matches your allergy profile',
      ],
      ingredients: [],
      execution_time: 3.0,
    };

    expect(response.allergen_warnings).toHaveLength(2);
    expect(response.allergen_warnings[0]).toContain('Fragrance');
  });

  it('should contain ingredient details', () => {
    const response: AnalysisResponse = {
      success: true,
      product_name: 'Test Product',
      overall_risk: 'low',
      average_safety_score: 8,
      summary: 'Safe product',
      allergen_warnings: [],
      ingredients: [
        {
          name: 'Water',
          purpose: 'Solvent',
          safety_score: 10,
          risk_level: 'low',
          concerns: 'None',
          recommendation: 'SAFE',
          origin: 'Natural',
          category: 'Both',
          allergy_risk: 'Low',
          is_allergen_match: false,
          alternatives: [],
        },
        {
          name: 'Glycerin',
          purpose: 'Humectant',
          safety_score: 9,
          risk_level: 'low',
          concerns: 'None',
          recommendation: 'SAFE',
          origin: 'Natural',
          category: 'Both',
          allergy_risk: 'Low',
          is_allergen_match: false,
          alternatives: [],
        },
      ],
      execution_time: 2.0,
    };

    expect(response.ingredients).toHaveLength(2);
    expect(response.ingredients[0].name).toBe('Water');
    expect(response.ingredients[1].name).toBe('Glycerin');
  });
});

describe('Type compatibility', () => {
  it('should work with real-world data structure', () => {
    // Simulate a real API response structure
    const apiResponse = {
      success: true,
      product_name: 'CeraVe Moisturizing Cream',
      overall_risk: 'low',
      average_safety_score: 8.7,
      summary: 'This product appears safe for most skin types including sensitive skin.',
      allergen_warnings: [],
      ingredients: [
        {
          name: 'Aqua/Water',
          purpose: 'Solvent, Vehicle',
          safety_score: 10,
          risk_level: 'low' as RiskLevel,
          concerns: 'No specific concerns',
          recommendation: 'SAFE',
          origin: 'Natural',
          category: 'Both',
          allergy_risk: 'Low',
          is_allergen_match: false,
          alternatives: [],
        },
      ],
      execution_time: 3.45,
    };

    // Type assertion to verify compatibility
    const typedResponse: AnalysisResponse = apiResponse;
    expect(typedResponse.success).toBe(true);
    expect(typedResponse.ingredients[0].safety_score).toBe(10);
  });
});
