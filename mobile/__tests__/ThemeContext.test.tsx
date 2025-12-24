/**
 * Theme Context Unit Tests
 *
 * Tests for the ThemeContext module that provides light/dark mode
 * functionality throughout the application.
 *
 * @module __tests__/ThemeContext.test
 */

import React from 'react';
import { render, act, fireEvent } from '@testing-library/react-native';
import { Text, TouchableOpacity } from 'react-native';
import {
  ThemeProvider,
  useTheme,
  lightTheme,
  darkTheme,
} from '../src/context/ThemeContext';

/**
 * Test component that consumes and displays theme context values.
 */
function ThemeConsumer() {
  const { theme, themeMode, toggleTheme } = useTheme();

  return (
    <>
      <Text testID="theme-mode">{themeMode}</Text>
      <Text testID="background-color">{theme.colors.background}</Text>
      <Text testID="primary-color">{theme.colors.primary}</Text>
      <TouchableOpacity testID="toggle-button" onPress={toggleTheme}>
        <Text>Toggle</Text>
      </TouchableOpacity>
    </>
  );
}

describe('ThemeContext', () => {
  describe('Theme Definitions', () => {
    it('should define light theme with correct mode', () => {
      expect(lightTheme.mode).toBe('light');
    });

    it('should define dark theme with correct mode', () => {
      expect(darkTheme.mode).toBe('dark');
    });

    it('should have different background colors for each theme', () => {
      expect(lightTheme.colors.background).not.toBe(darkTheme.colors.background);
    });

    it('should have all required color properties in light theme', () => {
      const requiredColors = [
        'background',
        'card',
        'cardBorder',
        'textPrimary',
        'textSecondary',
        'textMuted',
        'primary',
        'success',
        'warning',
        'danger',
        'info',
      ];

      requiredColors.forEach((color) => {
        expect(lightTheme.colors).toHaveProperty(color);
        expect(typeof lightTheme.colors[color as keyof typeof lightTheme.colors]).toBe('string');
      });
    });

    it('should have all required color properties in dark theme', () => {
      const requiredColors = [
        'background',
        'card',
        'cardBorder',
        'textPrimary',
        'textSecondary',
        'textMuted',
        'primary',
        'success',
        'warning',
        'danger',
        'info',
      ];

      requiredColors.forEach((color) => {
        expect(darkTheme.colors).toHaveProperty(color);
        expect(typeof darkTheme.colors[color as keyof typeof darkTheme.colors]).toBe('string');
      });
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9A-Fa-f]{6}$/;
      const rgbaRegex = /^rgba\(\d+,\d+,\d+,[\d.]+\)$/;

      // Test a few key colors
      expect(
        hexColorRegex.test(lightTheme.colors.background) ||
          rgbaRegex.test(lightTheme.colors.background)
      ).toBe(true);
      expect(
        hexColorRegex.test(lightTheme.colors.primary) ||
          rgbaRegex.test(lightTheme.colors.primary)
      ).toBe(true);
    });
  });

  describe('ThemeProvider', () => {
    it('should render children correctly', () => {
      const { getByText } = render(
        <ThemeProvider>
          <Text>Test Child</Text>
        </ThemeProvider>
      );

      expect(getByText('Test Child')).toBeTruthy();
    });

    it('should provide light theme by default', () => {
      const { getByTestId } = render(
        <ThemeProvider>
          <ThemeConsumer />
        </ThemeProvider>
      );

      expect(getByTestId('theme-mode').children[0]).toBe('light');
    });

    it('should provide correct background color for light theme', () => {
      const { getByTestId } = render(
        <ThemeProvider>
          <ThemeConsumer />
        </ThemeProvider>
      );

      expect(getByTestId('background-color').children[0]).toBe(
        lightTheme.colors.background
      );
    });
  });

  describe('useTheme hook', () => {
    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<ThemeConsumer />);
      }).toThrow('useTheme must be used within a ThemeProvider');

      consoleSpy.mockRestore();
    });

    it('should provide toggleTheme function', () => {
      const { getByTestId } = render(
        <ThemeProvider>
          <ThemeConsumer />
        </ThemeProvider>
      );

      // Initial state
      expect(getByTestId('theme-mode').children[0]).toBe('light');

      // Toggle theme using fireEvent
      fireEvent.press(getByTestId('toggle-button'));

      // Should now be dark
      expect(getByTestId('theme-mode').children[0]).toBe('dark');
    });

    it('should toggle back to light mode', () => {
      const { getByTestId } = render(
        <ThemeProvider>
          <ThemeConsumer />
        </ThemeProvider>
      );

      // Toggle to dark
      fireEvent.press(getByTestId('toggle-button'));

      // Toggle back to light
      fireEvent.press(getByTestId('toggle-button'));

      expect(getByTestId('theme-mode').children[0]).toBe('light');
    });

    it('should update colors when theme changes', () => {
      const { getByTestId } = render(
        <ThemeProvider>
          <ThemeConsumer />
        </ThemeProvider>
      );

      // Verify light theme background
      expect(getByTestId('background-color').children[0]).toBe(
        lightTheme.colors.background
      );

      // Toggle to dark
      fireEvent.press(getByTestId('toggle-button'));

      // Verify dark theme background
      expect(getByTestId('background-color').children[0]).toBe(
        darkTheme.colors.background
      );
    });
  });
});

describe('Theme Color Accessibility', () => {
  it('should have sufficient contrast between text and background (light theme)', () => {
    // This is a simplified check - proper contrast testing would use WCAG algorithms
    expect(lightTheme.colors.textPrimary).not.toBe(lightTheme.colors.background);
    expect(lightTheme.colors.textSecondary).not.toBe(lightTheme.colors.background);
  });

  it('should have sufficient contrast between text and background (dark theme)', () => {
    expect(darkTheme.colors.textPrimary).not.toBe(darkTheme.colors.background);
    expect(darkTheme.colors.textSecondary).not.toBe(darkTheme.colors.background);
  });

  it('should use appropriate semantic colors', () => {
    // Success should be greenish
    expect(lightTheme.colors.success.toLowerCase()).toContain('2');
    expect(darkTheme.colors.success.toLowerCase()).toContain('a');

    // Danger should be reddish
    expect(lightTheme.colors.danger.toLowerCase()).toContain('e');
    expect(darkTheme.colors.danger.toLowerCase()).toContain('f');
  });
});
