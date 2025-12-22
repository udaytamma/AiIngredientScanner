/**
 * Theme context for managing light/dark mode across the app.
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ThemeMode } from '../types';

// Define color schemes
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

export type Theme = typeof lightTheme;

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  toggleTheme: () => void;
  setThemeMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [themeMode, setThemeMode] = useState<ThemeMode>('light');

  const theme = themeMode === 'light' ? lightTheme : darkTheme;

  const toggleTheme = () => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, themeMode, toggleTheme, setThemeMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
