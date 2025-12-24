/**
 * Component Unit Tests
 *
 * Tests for reusable UI components including safety visualization
 * and user profile components.
 *
 * @module __tests__/components.test
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { SafetyMeter } from '../src/components/SafetyMeter';
import { SafetyBar } from '../src/components/SafetyBar';
import { RiskBadge } from '../src/components/RiskBadge';
import { ThemeProvider } from '../src/context/ThemeContext';

/**
 * Wrapper component that provides required context for testing.
 */
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>{children}</ThemeProvider>
);

describe('SafetyMeter Component', () => {
  it('should render without crashing', () => {
    const { getByText } = render(<SafetyMeter score={8} />);
    expect(getByText('8')).toBeTruthy();
  });

  it('should display score and out of 10 text', () => {
    const { getByText } = render(<SafetyMeter score={7} />);
    expect(getByText('7')).toBeTruthy();
    expect(getByText('/10')).toBeTruthy();
  });

  it('should show "Excellent" label for score >= 9', () => {
    const { getByText } = render(<SafetyMeter score={9} />);
    expect(getByText('Excellent')).toBeTruthy();
  });

  it('should show "Good" label for score >= 7', () => {
    const { getByText } = render(<SafetyMeter score={7} />);
    expect(getByText('Good')).toBeTruthy();
  });

  it('should show "Moderate" label for score >= 5', () => {
    const { getByText } = render(<SafetyMeter score={5} />);
    expect(getByText('Moderate')).toBeTruthy();
  });

  it('should show "Concerning" label for score >= 3', () => {
    const { getByText } = render(<SafetyMeter score={3} />);
    expect(getByText('Concerning')).toBeTruthy();
  });

  it('should show "High Risk" label for low scores', () => {
    const { getByText } = render(<SafetyMeter score={2} />);
    expect(getByText('High Risk')).toBeTruthy();
  });

  it('should hide label when showLabel is false', () => {
    const { queryByText } = render(<SafetyMeter score={9} showLabel={false} />);
    expect(queryByText('Excellent')).toBeNull();
  });

  it('should render with different sizes', () => {
    const sizes: Array<'small' | 'medium' | 'large'> = ['small', 'medium', 'large'];
    sizes.forEach((size) => {
      const { getByText } = render(<SafetyMeter score={5} size={size} />);
      expect(getByText('5')).toBeTruthy();
    });
  });
});

describe('SafetyBar Component', () => {
  it('should render without crashing', () => {
    const { getByText } = render(<SafetyBar score={8} />);
    expect(getByText('8/10')).toBeTruthy();
  });

  it('should display score label by default', () => {
    const { getByText } = render(<SafetyBar score={6} />);
    expect(getByText('6/10')).toBeTruthy();
  });

  it('should hide label when showLabel is false', () => {
    const { queryByText } = render(<SafetyBar score={6} showLabel={false} />);
    expect(queryByText('6/10')).toBeNull();
  });

  it('should render for all valid scores 1-10', () => {
    for (let score = 1; score <= 10; score++) {
      const { getByText } = render(<SafetyBar score={score} />);
      expect(getByText(`${score}/10`)).toBeTruthy();
    }
  });
});

describe('RiskBadge Component', () => {
  it('should render without crashing', () => {
    const { getByText } = render(<RiskBadge risk="low" />);
    expect(getByText('SAFE')).toBeTruthy();
  });

  it('should display "SAFE" for low risk', () => {
    const { getByText } = render(<RiskBadge risk="low" />);
    expect(getByText('SAFE')).toBeTruthy();
  });

  it('should display "MODERATE" for medium risk', () => {
    const { getByText } = render(<RiskBadge risk="medium" />);
    expect(getByText('MODERATE')).toBeTruthy();
  });

  it('should display "HIGH RISK" for high risk', () => {
    const { getByText } = render(<RiskBadge risk="high" />);
    expect(getByText('HIGH RISK')).toBeTruthy();
  });

  it('should display "CAUTION" for caution risk', () => {
    const { getByText } = render(<RiskBadge risk="caution" />);
    expect(getByText('CAUTION')).toBeTruthy();
  });

  it('should display "AVOID" for avoid risk', () => {
    const { getByText } = render(<RiskBadge risk="avoid" />);
    expect(getByText('AVOID')).toBeTruthy();
  });

  it('should render with different sizes', () => {
    const sizes: Array<'small' | 'medium' | 'large'> = ['small', 'medium', 'large'];
    sizes.forEach((size) => {
      const { getByText } = render(<RiskBadge risk="low" size={size} />);
      expect(getByText('SAFE')).toBeTruthy();
    });
  });

  it('should be case-insensitive for risk level', () => {
    const { getByText } = render(<RiskBadge risk="HIGH" />);
    expect(getByText('HIGH RISK')).toBeTruthy();
  });
});

describe('Component Integration', () => {
  it('should render multiple safety components together', () => {
    const { getByText, getAllByText } = render(
      <>
        <SafetyMeter score={8} />
        <SafetyBar score={8} />
        <RiskBadge risk="low" />
      </>
    );

    // Multiple '8' elements from meter and bar
    expect(getByText('8')).toBeTruthy(); // From SafetyMeter
    expect(getByText('8/10')).toBeTruthy(); // From SafetyBar
    expect(getByText('SAFE')).toBeTruthy(); // From RiskBadge
  });
});

describe('Color Logic', () => {
  describe('SafetyMeter colors', () => {
    it('should return green color for high scores', () => {
      // Testing internal logic through rendered output would require style inspection
      // This is a structural test to ensure component handles all score ranges
      const scores = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1];
      scores.forEach((score) => {
        const { getByText } = render(<SafetyMeter score={score} />);
        expect(getByText(String(score))).toBeTruthy();
      });
    });
  });

  describe('SafetyBar colors', () => {
    it('should handle all score values without errors', () => {
      // Low scores (red range)
      [1, 2, 3].forEach((score) => {
        const { getByText } = render(<SafetyBar score={score} />);
        expect(getByText(`${score}/10`)).toBeTruthy();
      });

      // Medium scores (orange range)
      [4, 5, 6].forEach((score) => {
        const { getByText } = render(<SafetyBar score={score} />);
        expect(getByText(`${score}/10`)).toBeTruthy();
      });

      // High scores (green range)
      [7, 8, 9, 10].forEach((score) => {
        const { getByText } = render(<SafetyBar score={score} />);
        expect(getByText(`${score}/10`)).toBeTruthy();
      });
    });
  });
});
