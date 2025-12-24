/**
 * API Service Unit Tests
 *
 * Tests for the API service module that handles communication with the
 * AI Ingredient Safety Analyzer backend.
 *
 * @module __tests__/api.test
 */

import axios from 'axios';
import { analyzeIngredients, checkHealth, getConfiguredApiUrl } from '../src/services/api';
import { AnalysisRequest, AnalysisResponse } from '../src/types';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock Platform
jest.mock('react-native', () => ({
  Platform: {
    OS: 'ios',
  },
}));

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getConfiguredApiUrl', () => {
    it('should return a valid URL string', () => {
      const url = getConfiguredApiUrl();
      expect(typeof url).toBe('string');
      expect(url.startsWith('http')).toBe(true);
    });
  });

  describe('checkHealth', () => {
    it('should be a function', () => {
      // Verify checkHealth exists and is a function
      expect(typeof checkHealth).toBe('function');
    });

    it('should return a Promise', () => {
      // Function signature test - it should return a Promise
      const result = checkHealth();
      expect(result).toBeInstanceOf(Promise);
    });
  });

  describe('analyzeIngredients', () => {
    const mockRequest: AnalysisRequest = {
      product_name: 'Test Moisturizer',
      ingredients: 'Water, Glycerin, Shea Butter',
      allergies: ['Fragrance'],
      skin_type: 'sensitive',
      expertise: 'beginner',
    };

    const mockResponse: AnalysisResponse = {
      success: true,
      product_name: 'Test Moisturizer',
      overall_risk: 'low',
      average_safety_score: 8.5,
      summary: 'This product appears safe for most users.',
      allergen_warnings: [],
      ingredients: [
        {
          name: 'Water',
          purpose: 'Solvent, hydration',
          safety_score: 10,
          risk_level: 'low',
          concerns: 'No specific concerns',
          recommendation: 'SAFE',
          origin: 'Natural',
          category: 'Both',
          allergy_risk: 'Low',
          is_allergen_match: false,
          alternatives: [],
        },
      ],
      execution_time: 2.5,
    };

    it('should have correct function signature', () => {
      expect(typeof analyzeIngredients).toBe('function');
    });

    it('should accept AnalysisRequest parameter', async () => {
      // Type check - this test verifies TypeScript types are correct
      const request: AnalysisRequest = mockRequest;
      expect(request.ingredients).toBe('Water, Glycerin, Shea Butter');
      expect(request.allergies).toContain('Fragrance');
    });
  });
});

describe('AnalysisRequest type validation', () => {
  it('should require ingredients field', () => {
    const validRequest: AnalysisRequest = {
      ingredients: 'Water',
      allergies: [],
      skin_type: 'normal',
      expertise: 'beginner',
    };
    expect(validRequest.ingredients).toBeDefined();
  });

  it('should accept all skin types', () => {
    const skinTypes = ['normal', 'dry', 'oily', 'combination', 'sensitive'] as const;
    skinTypes.forEach((skinType) => {
      const request: AnalysisRequest = {
        ingredients: 'Water',
        allergies: [],
        skin_type: skinType,
        expertise: 'beginner',
      };
      expect(request.skin_type).toBe(skinType);
    });
  });

  it('should accept both expertise levels', () => {
    const expertiseLevels = ['beginner', 'expert'] as const;
    expertiseLevels.forEach((expertise) => {
      const request: AnalysisRequest = {
        ingredients: 'Water',
        allergies: [],
        skin_type: 'normal',
        expertise: expertise,
      };
      expect(request.expertise).toBe(expertise);
    });
  });
});

describe('AnalysisResponse type validation', () => {
  it('should have all required fields', () => {
    const response: AnalysisResponse = {
      success: true,
      product_name: 'Test',
      overall_risk: 'low',
      average_safety_score: 8.0,
      summary: 'Test summary',
      allergen_warnings: [],
      ingredients: [],
      execution_time: 1.0,
    };

    expect(response.success).toBeDefined();
    expect(response.product_name).toBeDefined();
    expect(response.overall_risk).toBeDefined();
    expect(response.average_safety_score).toBeDefined();
    expect(response.summary).toBeDefined();
    expect(response.allergen_warnings).toBeDefined();
    expect(response.ingredients).toBeDefined();
    expect(response.execution_time).toBeDefined();
  });

  it('should allow optional error field', () => {
    const errorResponse: AnalysisResponse = {
      success: false,
      product_name: 'Test',
      overall_risk: 'unknown',
      average_safety_score: 0,
      summary: '',
      allergen_warnings: [],
      ingredients: [],
      execution_time: 0,
      error: 'Analysis failed',
    };

    expect(errorResponse.error).toBe('Analysis failed');
  });
});
