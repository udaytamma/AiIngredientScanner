/**
 * OCR Service
 *
 * Provides optical character recognition functionality for extracting text
 * from ingredient label images. Uses the backend Gemini Vision API for
 * cross-platform compatibility.
 *
 * Supports both native (expo-file-system) and web (data URL) image sources.
 *
 * @module services/ocr
 * @author Uday Tamma
 * @license MIT
 */

import { Platform } from 'react-native';
import api from './api';

/**
 * Converts an image URI to base64 format for API transmission.
 *
 * Handles platform-specific image sources:
 * - Web: Data URLs are already base64, extracts the data portion
 * - Native: Uses expo-file-system to read and convert the file
 *
 * @param imageUri - Image source (file URI or data URL)
 * @returns Base64-encoded image string
 */
async function getBase64FromUri(imageUri: string): Promise<string> {
  // Check if already a data URL (from web camera capture)
  if (imageUri.startsWith('data:image')) {
    // Extract base64 portion from data URL
    // Format: data:image/jpeg;base64,/9j/4AAQSkZJRg...
    const base64Data = imageUri.split(',')[1];
    return base64Data;
  }

  // Native platform: use expo-file-system
  if (Platform.OS !== 'web') {
    // Dynamic import to avoid bundling in web builds
    const { File } = await import('expo-file-system');
    const imageFile = new File(imageUri);

    // Verify file exists before reading
    const exists = imageFile.exists;
    if (!exists) {
      throw new Error('Image file does not exist');
    }

    // Read and return base64-encoded content
    return await imageFile.base64();
  }

  throw new Error('Unable to process image format');
}

/**
 * Extracts text from an image using the backend OCR endpoint.
 *
 * Sends the image to the backend which uses Gemini Vision API for
 * text extraction. This approach ensures consistent results across
 * all platforms without requiring native ML libraries.
 *
 * @param imageUri - Local URI of the image (file:// or data:)
 * @returns Extracted text from the image, empty string if no text found
 * @throws Error if OCR processing fails
 *
 * @example
 * ```typescript
 * const text = await extractTextFromImage(capturedImageUri);
 * if (text) {
 *   setIngredients(text);
 * }
 * ```
 */
export async function extractTextFromImage(imageUri: string): Promise<string> {
  try {
    // Convert image to base64 for API transmission
    const base64Image = await getBase64FromUri(imageUri);

    // Send to backend for OCR processing via Gemini Vision
    const response = await api.post('/ocr', {
      image: base64Image,
    });

    if (response.data && response.data.text) {
      return response.data.text;
    }

    return '';
  } catch (error: any) {
    console.error('OCR failed:', error);

    if (error.response?.status === 404) {
      // OCR endpoint not available - graceful degradation
      console.log('OCR endpoint not available, using manual input');
      return '';
    }

    throw new Error('Failed to extract text from image');
  }
}

/**
 * Extract and clean ingredient text from an image.
 * Attempts to identify ingredient list patterns.
 *
 * @param imageUri - Local URI of the image to process
 * @returns Cleaned ingredient text
 */
export async function extractIngredients(imageUri: string): Promise<string> {
  const rawText = await extractTextFromImage(imageUri);

  if (!rawText) {
    return '';
  }

  // Clean up the text
  let cleanedText = rawText
    // Replace multiple spaces/newlines with single space
    .replace(/\s+/g, ' ')
    // Remove common label prefixes
    .replace(/ingredients?\s*:?\s*/gi, '')
    .replace(/contains?\s*:?\s*/gi, '')
    // Fix common OCR errors
    .replace(/\|/g, 'l') // Pipe to lowercase L
    .trim();

  // Try to find ingredient list by looking for comma-separated items
  const ingredientPatterns = [
    // Match text with multiple commas (likely ingredients)
    /([A-Za-z][A-Za-z0-9\s\-\/\(\)]+(?:,\s*[A-Za-z][A-Za-z0-9\s\-\/\(\)]+){2,})/,
  ];

  for (const pattern of ingredientPatterns) {
    const match = cleanedText.match(pattern);
    if (match) {
      cleanedText = match[1];
      break;
    }
  }

  return cleanedText;
}
