/**
 * Preferences Context
 *
 * Provides centralized user preferences management with Firestore persistence.
 * Syncs preferences across devices for authenticated users and stores locally for guests.
 *
 * Features:
 * - Load preferences from Firestore on login
 * - Auto-save changes to Firestore (debounced)
 * - Theme sync with ThemeContext
 * - Local storage fallback for guests
 * - Offline support via Firestore caching
 *
 * @module context/PreferencesContext
 * @author Uday Tamma
 * @license MIT
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  ReactNode,
} from 'react';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { db } from '../config/firebase';
import { useAuth } from './AuthContext';
import { useTheme } from './ThemeContext';
import { UserProfile, SkinType, ExpertiseLevel, ThemeMode } from '../types';

// =============================================================================
// Constants
// =============================================================================

/** Key for storing preferences in AsyncStorage (guests/offline) */
const PREFERENCES_STORAGE_KEY = '@ingredient_analyzer_preferences';

/** Debounce delay for saving preferences to Firestore (ms) */
const SAVE_DEBOUNCE_MS = 1000;

// =============================================================================
// Type Definitions
// =============================================================================

/**
 * Complete user preferences including theme.
 */
export interface UserPreferences {
  /** User's known allergies */
  allergies: string[];
  /** User's skin type */
  skinType: SkinType;
  /** Preferred explanation complexity */
  expertise: ExpertiseLevel;
  /** Theme preference */
  theme: ThemeMode;
}

/**
 * Default preferences for new users.
 */
const DEFAULT_PREFERENCES: UserPreferences = {
  allergies: [],
  skinType: 'normal',
  expertise: 'beginner',
  theme: 'light',
};

/**
 * Preferences context value shape.
 */
interface PreferencesContextType {
  /** Current user preferences */
  preferences: UserPreferences;
  /** Loading state during initial fetch */
  loading: boolean;
  /** Update allergies list */
  setAllergies: (allergies: string[]) => void;
  /** Update skin type */
  setSkinType: (skinType: SkinType) => void;
  /** Update expertise level */
  setExpertise: (expertise: ExpertiseLevel) => void;
  /** Update theme preference */
  setThemePreference: (theme: ThemeMode) => void;
  /** Update all preferences at once */
  updatePreferences: (prefs: Partial<UserPreferences>) => void;
  /** Get UserProfile for API calls */
  getUserProfile: () => UserProfile;
}

// =============================================================================
// Context & Provider
// =============================================================================

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

interface PreferencesProviderProps {
  children: ReactNode;
}

/**
 * Preferences provider component.
 *
 * Manages user preferences with Firestore sync for authenticated users.
 * Falls back to AsyncStorage for guests.
 */
export function PreferencesProvider({ children }: PreferencesProviderProps): React.JSX.Element {
  const { user } = useAuth();
  const { setThemeMode } = useTheme();
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isInitialLoadRef = useRef(true);

  // ---------------------------------------------------------------------------
  // Load preferences on mount or auth change
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const loadPreferences = async () => {
      setLoading(true);
      isInitialLoadRef.current = true;

      try {
        if (user) {
          // Authenticated: Load from Firestore
          const userRef = doc(db, 'users', user.uid);
          const userSnap = await getDoc(userRef);

          if (userSnap.exists()) {
            const data = userSnap.data();
            const firestorePrefs = data.preferences as UserPreferences | undefined;

            if (firestorePrefs) {
              setPreferences(firestorePrefs);
              // Sync theme with ThemeContext
              setThemeMode(firestorePrefs.theme || 'light');
            } else {
              // User exists but no preferences - use defaults and save them
              setPreferences(DEFAULT_PREFERENCES);
              setThemeMode(DEFAULT_PREFERENCES.theme);
              await saveToFirestore(user.uid, DEFAULT_PREFERENCES);
            }
          }
        } else {
          // Guest: Load from AsyncStorage
          const stored = await AsyncStorage.getItem(PREFERENCES_STORAGE_KEY);
          if (stored) {
            const parsed = JSON.parse(stored) as UserPreferences;
            setPreferences(parsed);
            setThemeMode(parsed.theme || 'light');
          } else {
            setPreferences(DEFAULT_PREFERENCES);
            setThemeMode(DEFAULT_PREFERENCES.theme);
          }
        }
      } catch (error) {
        console.error('Error loading preferences:', error);
        setPreferences(DEFAULT_PREFERENCES);
      } finally {
        setLoading(false);
        // Allow saves after initial load completes
        setTimeout(() => {
          isInitialLoadRef.current = false;
        }, 100);
      }
    };

    loadPreferences();
  }, [user, setThemeMode]);

  // ---------------------------------------------------------------------------
  // Save helpers
  // ---------------------------------------------------------------------------

  /**
   * Save preferences to Firestore.
   */
  const saveToFirestore = async (uid: string, prefs: UserPreferences): Promise<void> => {
    try {
      const userRef = doc(db, 'users', uid);
      await setDoc(userRef, { preferences: prefs }, { merge: true });
    } catch (error) {
      console.error('Error saving preferences to Firestore:', error);
    }
  };

  /**
   * Save preferences to AsyncStorage (for guests).
   */
  const saveToAsyncStorage = async (prefs: UserPreferences): Promise<void> => {
    try {
      await AsyncStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(prefs));
    } catch (error) {
      console.error('Error saving preferences to AsyncStorage:', error);
    }
  };

  /**
   * Debounced save function.
   * Waits for SAVE_DEBOUNCE_MS before saving to avoid excessive writes.
   */
  const debouncedSave = useCallback((newPrefs: UserPreferences) => {
    // Skip save during initial load
    if (isInitialLoadRef.current) {
      return;
    }

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout
    saveTimeoutRef.current = setTimeout(async () => {
      if (user) {
        await saveToFirestore(user.uid, newPrefs);
      } else {
        await saveToAsyncStorage(newPrefs);
      }
    }, SAVE_DEBOUNCE_MS);
  }, [user]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Preference update functions
  // ---------------------------------------------------------------------------

  const updatePreferences = useCallback((updates: Partial<UserPreferences>) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, ...updates };
      debouncedSave(newPrefs);

      // Sync theme if it changed
      if (updates.theme && updates.theme !== prev.theme) {
        setThemeMode(updates.theme);
      }

      return newPrefs;
    });
  }, [debouncedSave, setThemeMode]);

  const setAllergies = useCallback((allergies: string[]) => {
    updatePreferences({ allergies });
  }, [updatePreferences]);

  const setSkinType = useCallback((skinType: SkinType) => {
    updatePreferences({ skinType });
  }, [updatePreferences]);

  const setExpertise = useCallback((expertise: ExpertiseLevel) => {
    updatePreferences({ expertise });
  }, [updatePreferences]);

  const setThemePreference = useCallback((theme: ThemeMode) => {
    updatePreferences({ theme });
  }, [updatePreferences]);

  /**
   * Get UserProfile for API calls (excludes theme).
   */
  const getUserProfile = useCallback((): UserProfile => ({
    allergies: preferences.allergies,
    skinType: preferences.skinType,
    expertise: preferences.expertise,
  }), [preferences]);

  // ---------------------------------------------------------------------------
  // Context value
  // ---------------------------------------------------------------------------

  return (
    <PreferencesContext.Provider
      value={{
        preferences,
        loading,
        setAllergies,
        setSkinType,
        setExpertise,
        setThemePreference,
        updatePreferences,
        getUserProfile,
      }}
    >
      {children}
    </PreferencesContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

/**
 * Custom hook for consuming preferences context.
 *
 * @returns Preferences context value with state and update functions
 * @throws Error if used outside of PreferencesProvider
 */
export function usePreferences(): PreferencesContextType {
  const context = useContext(PreferencesContext);
  if (context === undefined) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
}
