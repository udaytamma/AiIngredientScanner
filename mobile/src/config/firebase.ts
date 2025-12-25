/**
 * Firebase Configuration
 *
 * Initializes Firebase services for the AI Ingredient Safety Analyzer.
 * Services enabled:
 * - Authentication (Google Sign-In)
 * - Firestore (User profiles and scan history)
 * - Analytics (Usage tracking)
 *
 * @module config/firebase
 * @author Uday Tamma
 * @license MIT
 */

import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getAnalytics, isSupported } from 'firebase/analytics';

// =============================================================================
// Firebase Configuration
// =============================================================================

/**
 * Firebase project configuration.
 * Project: AI Ingredient Analyzer (aiingredientanalyzer)
 */
const firebaseConfig = {
  apiKey: 'AIzaSyAZrDY0qEBT1FfzcTPaNYR_4OAf7B8p35I',
  authDomain: 'aiingredientanalyzer.firebaseapp.com',
  projectId: 'aiingredientanalyzer',
  storageBucket: 'aiingredientanalyzer.firebasestorage.app',
  messagingSenderId: '410617034936',
  appId: '1:410617034936:web:b148f2f395e2755430dc4d',
  measurementId: 'G-4WQL0QWJGE',
};

// =============================================================================
// Firebase Initialization
// =============================================================================

/**
 * Initialize Firebase app (singleton pattern).
 * Prevents multiple initializations in development with hot reload.
 */
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

/**
 * Firebase Authentication instance.
 * Used for Google Sign-In and user session management.
 */
export const auth = getAuth(app);

/**
 * Google Auth Provider for Sign-In.
 * Configured with profile and email scopes.
 */
export const googleProvider = new GoogleAuthProvider();
googleProvider.addScope('profile');
googleProvider.addScope('email');

/**
 * Firestore database instance.
 * Used for storing user profiles and scan history.
 */
export const db = getFirestore(app);

/**
 * Initialize Analytics (only in browser environments).
 * Returns null in React Native/Expo native environments.
 */
export const initAnalytics = async () => {
  if (await isSupported()) {
    return getAnalytics(app);
  }
  return null;
};

export default app;
