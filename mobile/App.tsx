/**
 * AI Ingredient Safety Analyzer - Mobile & Web Application
 *
 * A cross-platform React Native/Expo application that enables users to scan
 * ingredient labels from food and cosmetic products for AI-powered
 * safety analysis.
 *
 * Features:
 * - Camera-based ingredient label scanning (OCR via Gemini Vision)
 * - Personalized safety analysis based on user profile (allergies, skin type)
 * - Dark/Light theme support with system preference detection
 * - Cross-platform: iOS, Android, and Web (via Expo)
 * - Google Sign-In with Firebase Authentication
 * - User profile persistence with Firestore
 *
 * Architecture:
 * - Entry Point: App.tsx (this file)
 * - State Management: React Context (ThemeContext, AuthContext)
 * - Navigation: Single-screen with modal-based flows
 * - Backend: FastAPI on Railway (api.zeroleaf.dev)
 * - Auth: Firebase (Google Sign-In)
 *
 * @module App
 * @author Uday Tamma
 * @license MIT
 * @see https://github.com/udaytamma/AiIngredientScanner
 */

import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { HomeScreen } from './src/screens/HomeScreen';
import { LoginScreen } from './src/screens/LoginScreen';
import { ThemeProvider, useTheme } from './src/context/ThemeContext';
import { AuthProvider, useAuth } from './src/context/AuthContext';

/**
 * Application content wrapper that applies theme-aware styling.
 *
 * This component consumes the ThemeContext and AuthContext to:
 * - Apply appropriate background colors and status bar styling
 * - Show login screen or main app based on auth state
 * - Display loading indicator during auth state resolution
 *
 * @returns Themed application container with appropriate screen
 */
function AppContent(): React.JSX.Element {
  const { theme, themeMode } = useTheme();
  const { user, loading } = useAuth();
  const [guestMode, setGuestMode] = useState(false);

  // Show loading indicator while auth state is being resolved
  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  // Show login screen if user is not authenticated and not in guest mode
  const isAuthenticated = user !== null || guestMode;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar style={themeMode === 'dark' ? 'light' : 'dark'} />
      {isAuthenticated ? (
        <HomeScreen />
      ) : (
        <LoginScreen onGuestMode={() => setGuestMode(true)} />
      )}
    </SafeAreaView>
  );
}

/**
 * Root application component.
 *
 * Sets up the provider hierarchy:
 * 1. SafeAreaProvider - Handles safe area insets for notched devices
 * 2. ThemeProvider - Manages light/dark theme state
 * 3. AuthProvider - Manages Firebase authentication state
 *
 * @returns The complete application component tree
 */
export default function App(): React.JSX.Element {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

/**
 * Base application styles
 */
const styles = StyleSheet.create({
  /** Full-screen container for the application */
  container: {
    flex: 1,
  },
  /** Loading container with centered spinner */
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
