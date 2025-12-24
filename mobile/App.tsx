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
 *
 * Architecture:
 * - Entry Point: App.tsx (this file)
 * - State Management: React Context (ThemeContext)
 * - Navigation: Single-screen with modal-based flows
 * - Backend: FastAPI on Railway (api.zeroleaf.dev)
 *
 * @module App
 * @author Uday Tamma
 * @license MIT
 * @see https://github.com/udaytamma/AiIngredientScanner
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { HomeScreen } from './src/screens/HomeScreen';
import { ThemeProvider, useTheme } from './src/context/ThemeContext';

/**
 * Application content wrapper that applies theme-aware styling.
 *
 * This component consumes the ThemeContext to apply appropriate
 * background colors and status bar styling based on the current theme.
 *
 * @returns Themed application container with HomeScreen
 */
function AppContent(): React.JSX.Element {
  const { theme, themeMode } = useTheme();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar style={themeMode === 'dark' ? 'light' : 'dark'} />
      <HomeScreen />
    </SafeAreaView>
  );
}

/**
 * Root application component.
 *
 * Sets up the provider hierarchy:
 * 1. SafeAreaProvider - Handles safe area insets for notched devices
 * 2. ThemeProvider - Manages light/dark theme state
 *
 * @returns The complete application component tree
 */
export default function App(): React.JSX.Element {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AppContent />
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
});
