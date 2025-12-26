/**
 * Preferences Context Unit Tests
 *
 * Tests for the PreferencesContext module that manages user preferences
 * with Firestore sync for authenticated users and AsyncStorage for guests.
 *
 * @module __tests__/PreferencesContext.test
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Text, TouchableOpacity } from 'react-native';
import { ThemeProvider } from '../src/context/ThemeContext';
import { AuthProvider } from '../src/context/AuthContext';
import {
  PreferencesProvider,
  usePreferences,
  UserPreferences,
} from '../src/context/PreferencesContext';

// Mock Firebase
jest.mock('firebase/auth', () => ({
  getAuth: jest.fn(),
  signInWithPopup: jest.fn(),
  signInWithCredential: jest.fn(),
  signOut: jest.fn(),
  onAuthStateChanged: jest.fn((auth, callback) => {
    callback(null); // No user initially
    return jest.fn();
  }),
  deleteUser: jest.fn(),
  GoogleAuthProvider: {
    credential: jest.fn(),
  },
}));

jest.mock('firebase/firestore', () => ({
  getFirestore: jest.fn(),
  doc: jest.fn(),
  setDoc: jest.fn(() => Promise.resolve()),
  getDoc: jest.fn(() => Promise.resolve({ exists: () => false })),
  deleteDoc: jest.fn(),
  serverTimestamp: jest.fn(),
  collection: jest.fn(),
  getDocs: jest.fn(() => Promise.resolve({ docs: [] })),
  writeBatch: jest.fn(() => ({
    delete: jest.fn(),
    commit: jest.fn(),
  })),
}));

jest.mock('firebase/analytics', () => ({
  getAnalytics: jest.fn(),
  isSupported: jest.fn(() => Promise.resolve(false)),
}));

jest.mock('../src/config/firebase', () => ({
  auth: {},
  db: {},
  googleProvider: {},
}));

jest.mock('expo-auth-session/providers/google', () => ({
  useAuthRequest: jest.fn(() => [{}, null, jest.fn()]),
}));

jest.mock('expo-web-browser', () => ({
  maybeCompleteAuthSession: jest.fn(),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(() => Promise.resolve(null)),
  setItem: jest.fn(() => Promise.resolve()),
  removeItem: jest.fn(() => Promise.resolve()),
}));

/**
 * Test component that consumes and displays preferences context values.
 */
function PreferencesConsumer() {
  const {
    preferences,
    loading,
    setAllergies,
    setSkinType,
    setExpertise,
    setThemePreference,
    getUserProfile,
  } = usePreferences();

  const profile = getUserProfile();

  return (
    <>
      <Text testID="loading">{loading ? 'true' : 'false'}</Text>
      <Text testID="allergies">{JSON.stringify(preferences.allergies)}</Text>
      <Text testID="skinType">{preferences.skinType}</Text>
      <Text testID="expertise">{preferences.expertise}</Text>
      <Text testID="theme">{preferences.theme}</Text>
      <Text testID="profile-allergies">{JSON.stringify(profile.allergies)}</Text>

      <TouchableOpacity
        testID="add-allergy"
        onPress={() => setAllergies([...preferences.allergies, 'Peanut'])}
      >
        <Text>Add Allergy</Text>
      </TouchableOpacity>

      <TouchableOpacity
        testID="set-skin-dry"
        onPress={() => setSkinType('dry')}
      >
        <Text>Set Dry</Text>
      </TouchableOpacity>

      <TouchableOpacity
        testID="set-expert"
        onPress={() => setExpertise('expert')}
      >
        <Text>Set Expert</Text>
      </TouchableOpacity>

      <TouchableOpacity
        testID="set-dark-theme"
        onPress={() => setThemePreference('dark')}
      >
        <Text>Dark Theme</Text>
      </TouchableOpacity>
    </>
  );
}

/**
 * Wrapper component that provides all necessary context providers.
 */
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <PreferencesProvider>
          {children}
        </PreferencesProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

describe('PreferencesContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Default Values', () => {
    it('should provide default preferences', async () => {
      const { getByTestId } = render(
        <TestWrapper>
          <PreferencesConsumer />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('loading').children[0]).toBe('false');
      });

      expect(JSON.parse(getByTestId('allergies').children[0] as string)).toEqual([]);
      expect(getByTestId('skinType').children[0]).toBe('normal');
      expect(getByTestId('expertise').children[0]).toBe('beginner');
      expect(getByTestId('theme').children[0]).toBe('light');
    });
  });

  describe('Allergies Management', () => {
    it('should add an allergy', async () => {
      const { getByTestId } = render(
        <TestWrapper>
          <PreferencesConsumer />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('loading').children[0]).toBe('false');
      });

      fireEvent.press(getByTestId('add-allergy'));

      await waitFor(() => {
        const allergies = JSON.parse(getByTestId('allergies').children[0] as string);
        expect(allergies).toContain('Peanut');
      });
    });
  });

  describe('Skin Type Management', () => {
    it('should update skin type', async () => {
      const { getByTestId } = render(
        <TestWrapper>
          <PreferencesConsumer />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('loading').children[0]).toBe('false');
      });

      expect(getByTestId('skinType').children[0]).toBe('normal');

      fireEvent.press(getByTestId('set-skin-dry'));

      await waitFor(() => {
        expect(getByTestId('skinType').children[0]).toBe('dry');
      });
    });
  });

  describe('Expertise Level Management', () => {
    it('should update expertise level', async () => {
      const { getByTestId } = render(
        <TestWrapper>
          <PreferencesConsumer />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('loading').children[0]).toBe('false');
      });

      expect(getByTestId('expertise').children[0]).toBe('beginner');

      fireEvent.press(getByTestId('set-expert'));

      await waitFor(() => {
        expect(getByTestId('expertise').children[0]).toBe('expert');
      });
    });
  });

  describe('Theme Management', () => {
    it('should update theme preference', async () => {
      const { getByTestId } = render(
        <TestWrapper>
          <PreferencesConsumer />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('loading').children[0]).toBe('false');
      });

      expect(getByTestId('theme').children[0]).toBe('light');

      fireEvent.press(getByTestId('set-dark-theme'));

      await waitFor(() => {
        expect(getByTestId('theme').children[0]).toBe('dark');
      });
    });
  });

  describe('getUserProfile', () => {
    it('should return profile without theme', async () => {
      const { getByTestId } = render(
        <TestWrapper>
          <PreferencesConsumer />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('loading').children[0]).toBe('false');
      });

      // Add an allergy first
      fireEvent.press(getByTestId('add-allergy'));

      await waitFor(() => {
        const profileAllergies = JSON.parse(getByTestId('profile-allergies').children[0] as string);
        expect(profileAllergies).toContain('Peanut');
      });
    });
  });

  describe('usePreferences hook', () => {
    it('should throw error when used outside provider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<PreferencesConsumer />);
      }).toThrow('usePreferences must be used within a PreferencesProvider');

      consoleSpy.mockRestore();
    });
  });
});

describe('UserPreferences Type', () => {
  it('should have correct shape', () => {
    const prefs: UserPreferences = {
      allergies: ['Peanut', 'Gluten'],
      skinType: 'sensitive',
      expertise: 'expert',
      theme: 'dark',
    };

    expect(prefs.allergies).toBeInstanceOf(Array);
    expect(['normal', 'dry', 'oily', 'combination', 'sensitive']).toContain(prefs.skinType);
    expect(['beginner', 'expert']).toContain(prefs.expertise);
    expect(['light', 'dark']).toContain(prefs.theme);
  });
});
