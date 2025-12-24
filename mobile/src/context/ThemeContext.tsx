/**
 * Theme Context
 *
 * Provides application-wide theme management with support for light and dark modes.
 * Uses React Context for efficient theme state propagation without prop drilling.
 *
 * Features:
 * - Predefined light and dark color palettes
 * - Theme toggle functionality
 * - Type-safe theme consumption via useTheme hook
 *
 * Usage:
 * ```tsx
 * // Wrap app with ThemeProvider
 * <ThemeProvider>
 *   <App />
 * </ThemeProvider>
 *
 * // Consume theme in components
 * const { theme, toggleTheme } = useTheme();
 * <View style={{ backgroundColor: theme.colors.background }} />
 * ```
 *
 * @module context/ThemeContext
 * @author Uday Tamma
 * @license MIT
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ThemeMode } from '../types';

// =============================================================================
// Theme Definitions
// =============================================================================

/**
 * Light theme color palette.
 *
 * Designed for optimal readability in bright environments with
 * subtle shadows and clear visual hierarchy.
 */
export const lightTheme = {
  mode: 'light' as ThemeMode,
  colors: {
    // Backgrounds
    background: '#f8fafc',
    card: '#ffffff',
    cardBorder: '#e5e7eb',
    inputBackground: '#f9fafb',

    // Text
    textPrimary: '#1f2937',
    textSecondary: '#6b7280',
    textMuted: '#9ca3af',

    // Accent colors
    primary: '#6366f1',
    success: '#22c55e',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6',

    // Specific UI elements
    divider: '#e5e7eb',
    shadow: '#000000',
    overlay: 'rgba(0,0,0,0.5)',

    // Profile tags
    profileTagBg: '#f0f9ff',
    profileTagBorder: '#bae6fd',
    profileTagText: '#0c4a6e',
    profileTagLabel: '#0369a1',

    // Allergy tags
    allergyBg: '#fef2f2',
    allergyBorder: '#fecaca',
    allergyText: '#dc2626',

    // Gallery button
    galleryBg: '#ecfdf5',
    galleryBorder: '#a7f3d0',
    galleryText: '#059669',
  },
};

export const darkTheme = {
  mode: 'dark' as ThemeMode,
  colors: {
    // Backgrounds
    background: '#0f172a',
    card: '#1e293b',
    cardBorder: '#334155',
    inputBackground: '#1e293b',

    // Text
    textPrimary: '#f1f5f9',
    textSecondary: '#94a3b8',
    textMuted: '#64748b',

    // Accent colors
    primary: '#818cf8',
    success: '#4ade80',
    warning: '#fbbf24',
    danger: '#f87171',
    info: '#60a5fa',

    // Specific UI elements
    divider: '#334155',
    shadow: '#000000',
    overlay: 'rgba(0,0,0,0.7)',

    // Profile tags
    profileTagBg: '#1e3a5f',
    profileTagBorder: '#3b82f6',
    profileTagText: '#93c5fd',
    profileTagLabel: '#60a5fa',

    // Allergy tags
    allergyBg: '#450a0a',
    allergyBorder: '#b91c1c',
    allergyText: '#fca5a5',

    // Gallery button
    galleryBg: '#064e3b',
    galleryBorder: '#10b981',
    galleryText: '#6ee7b7',
  },
};

// =============================================================================
// Type Definitions
// =============================================================================

/** Theme object type derived from lightTheme structure */
export type Theme = typeof lightTheme;

/**
 * Theme context value shape.
 * Provides current theme, mode, and toggle functions.
 */
interface ThemeContextType {
  /** Current theme object with color palette */
  theme: Theme;
  /** Current theme mode identifier */
  themeMode: ThemeMode;
  /** Toggles between light and dark modes */
  toggleTheme: () => void;
  /** Directly sets the theme mode */
  setThemeMode: (mode: ThemeMode) => void;
}

// =============================================================================
// Context & Provider
// =============================================================================

/** Theme context - undefined when accessed outside provider */
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/** Props for ThemeProvider component */
interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * Theme provider component.
 *
 * Wraps the application to provide theme state and controls to all descendants.
 * Manages the current theme mode and provides toggle functionality.
 *
 * @param props - Component props containing children
 * @returns Provider component wrapping children with theme context
 */
export function ThemeProvider({ children }: ThemeProviderProps): React.JSX.Element {
  const [themeMode, setThemeMode] = useState<ThemeMode>('light');

  // Select theme object based on current mode
  const theme = themeMode === 'light' ? lightTheme : darkTheme;

  // Toggle handler for theme switching
  const toggleTheme = () => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, themeMode, toggleTheme, setThemeMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

/**
 * Custom hook for consuming theme context.
 *
 * Provides access to current theme colors and toggle functions.
 * Must be used within a ThemeProvider component tree.
 *
 * @returns Theme context value with colors and controls
 * @throws Error if used outside of ThemeProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { theme, toggleTheme } = useTheme();
 *   return (
 *     <View style={{ backgroundColor: theme.colors.card }}>
 *       <Button onPress={toggleTheme} title="Toggle Theme" />
 *     </View>
 *   );
 * }
 * ```
 */
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
