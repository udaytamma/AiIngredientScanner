/**
 * API service for communicating with the backend.
 */

import axios from 'axios';
import { AnalysisRequest, AnalysisResponse } from '../types';

// API base URL - update this to your server's IP address
// For local development, use your Mac's IP address (not localhost)
// Find it with: ipconfig getifaddr en0
const API_BASE_URL = 'http://192.168.6.171:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Check if the API server is healthy.
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
 * Analyze ingredients for safety.
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
      // Server responded with error
      throw new Error(error.response.data.detail || 'Analysis failed');
    } else if (error.request) {
      // No response received
      throw new Error('Cannot connect to server. Check your network connection.');
    } else {
      throw new Error(error.message || 'Unknown error occurred');
    }
  }
}

/**
 * Update the API base URL.
 */
export function setApiBaseUrl(url: string): void {
  api.defaults.baseURL = url;
}

export default api;
