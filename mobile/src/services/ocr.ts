/**
 * OCR service using backend API for text extraction.
 *
 * Since ML Kit requires native builds (not compatible with Expo Go),
 * we send the image to the backend which uses Gemini Vision API.
 */

import { File } from 'expo-file-system';
import api from './api';

/**
 * Extract text from an image by sending to backend OCR endpoint.
 *
 * @param imageUri - Local URI of the image to process
 * @returns Extracted text from the image
 */
export async function extractTextFromImage(imageUri: string): Promise<string> {
  try {
    // Create a File reference from the URI
    const imageFile = new File(imageUri);

    // Check if file exists
    const exists = imageFile.exists;
    if (!exists) {
      throw new Error('Image file does not exist');
    }

    // Read the image as base64
    const base64Image = await imageFile.base64();

    // Send to backend for OCR processing
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
      // OCR endpoint not available, return empty to allow manual input
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
