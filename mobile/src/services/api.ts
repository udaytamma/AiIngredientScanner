/**
 * API Service
 *
 * Handles all HTTP communication with the AI Ingredient Safety Analyzer backend.
 * Supports both production deployment (api.zeroleaf.dev) and local development.
 *
 * @module services/api
 * @author Uday Tamma
 * @license MIT
 */

import axios from 'axios';
import { Platform } from 'react-native';
import { AnalysisRequest, AnalysisResponse } from '../types';

/**
 * Determines the appropriate API base URL based on the runtime environment.
 *
 * Production (web builds and native release): Uses the deployed Railway API
 * Development (Expo Go): Uses local development server via IP address
 *
 * @returns The API base URL for the current environment
 */
const getApiBaseUrl = (): string => {
  // Production API endpoint - Railway deployment
  const PRODUCTION_API = 'https://api.zeroleaf.dev';

  // Local development API - for Expo Go testing
  // Update this IP when your local network changes
  const LOCAL_DEV_API = 'http://192.168.6.171:8000';

  // Check if running in production (web builds or native release builds)
  // __DEV__ is true in development mode (Expo Go, Metro bundler)
  // @ts-ignore - __DEV__ is a React Native global
  const isDevelopment = typeof __DEV__ !== 'undefined' && __DEV__;

  // For web platform, always use production API (handles CORS properly)
  if (Platform.OS === 'web') {
    return PRODUCTION_API;
  }

  // For native platforms: use production in release, local in development
  return isDevelopment ? LOCAL_DEV_API : PRODUCTION_API;
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Performs a health check against the API server.
 *
 * Used to verify connectivity before attempting analysis requests.
 * Returns true if the server responds with a healthy status.
 *
 * @returns Promise resolving to true if server is healthy, false otherwise
 *
 * @example
 * ```typescript
 * const isConnected = await checkHealth();
 * if (!isConnected) {
 *   showOfflineMessage();
 * }
 * ```
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await api.get('/health');
    return response.data.status === 'healthy';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
}

/**
 * Submits ingredients for AI-powered safety analysis.
 *
 * Sends the ingredient list along with user profile preferences to the backend,
 * which uses Gemini AI to analyze each ingredient's safety profile.
 *
 * @param request - Analysis request containing ingredients and user profile
 * @returns Promise resolving to detailed analysis results
 * @throws Error with user-friendly message if analysis fails
 *
 * @example
 * ```typescript
 * const result = await analyzeIngredients({
 *   product_name: 'Moisturizer',
 *   ingredients: 'Water, Glycerin, Shea Butter',
 *   allergies: ['Fragrance'],
 *   skin_type: 'sensitive',
 *   expertise: 'beginner'
 * });
 * console.log(result.overall_risk); // 'low' | 'medium' | 'high'
 * ```
 */
export async function analyzeIngredients(
  request: AnalysisRequest
): Promise<AnalysisResponse> {
  try {
    const response = await api.post<AnalysisResponse>('/analyze', request);
    return response.data;
  } catch (error: any) {
    console.error('Analysis failed:', error);

    if (error.response) {
      // Server responded with error status code
      throw new Error(error.response.data.detail || 'Analysis failed');
    } else if (error.request) {
      // Request was made but no response received (network error)
      throw new Error('Cannot connect to server. Check your network connection.');
    } else {
      // Error occurred during request setup
      throw new Error(error.message || 'Unknown error occurred');
    }
  }
}

/**
 * Dynamically updates the API base URL.
 *
 * Useful for switching between environments or testing against different servers.
 *
 * @param url - New API base URL (e.g., 'https://api.zeroleaf.dev')
 */
export function setApiBaseUrl(url: string): void {
  api.defaults.baseURL = url;
}

/**
 * Returns the currently configured API base URL.
 *
 * @returns The active API base URL
 */
export function getConfiguredApiUrl(): string {
  return API_BASE_URL;
}

export default api;
