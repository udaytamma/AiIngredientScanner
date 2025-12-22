/**
 * AI Ingredient Safety Analyzer - Mobile App
 *
 * Scan ingredient labels and get personalized safety analysis.
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { HomeScreen } from './src/screens/HomeScreen';
import { ThemeProvider, useTheme } from './src/context/ThemeContext';

function AppContent() {
  const { theme, themeMode } = useTheme();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar style={themeMode === 'dark' ? 'light' : 'dark'} />
      <HomeScreen />
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
