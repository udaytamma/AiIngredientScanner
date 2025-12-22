/**
 * Circular safety meter component with gradient colors.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface SafetyMeterProps {
  score: number; // 1-10
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

const getScoreColor = (score: number): string => {
  if (score >= 8) return '#22c55e'; // Green
  if (score >= 6) return '#84cc16'; // Light green
  if (score >= 4) return '#f59e0b'; // Amber
  if (score >= 2) return '#f97316'; // Orange
  return '#ef4444'; // Red
};

const getScoreBackground = (score: number): string => {
  if (score >= 8) return '#dcfce7'; // Light green
  if (score >= 6) return '#ecfccb'; // Light lime
  if (score >= 4) return '#fef3c7'; // Light amber
  if (score >= 2) return '#ffedd5'; // Light orange
  return '#fee2e2'; // Light red
};

const getScoreLabel = (score: number): string => {
  if (score >= 9) return 'Excellent';
  if (score >= 7) return 'Good';
  if (score >= 5) return 'Moderate';
  if (score >= 3) return 'Concerning';
  return 'High Risk';
};

export function SafetyMeter({
  score,
  size = 'medium',
  showLabel = true,
}: SafetyMeterProps) {
  const color = getScoreColor(score);
  const bgColor = getScoreBackground(score);
  const label = getScoreLabel(score);

  const sizeConfig = {
    small: { container: 60, score: 20, label: 9 },
    medium: { container: 90, score: 28, label: 11 },
    large: { container: 120, score: 36, label: 13 },
  };

  const config = sizeConfig[size];

  return (
    <View style={styles.wrapper}>
      <View
        style={[
          styles.container,
          {
            width: config.container,
            height: config.container,
            backgroundColor: bgColor,
            borderColor: color,
          },
        ]}
      >
        <Text style={[styles.score, { fontSize: config.score, color }]}>
          {score}
        </Text>
        <Text style={[styles.outOf, { color }]}>/10</Text>
      </View>
      {showLabel && (
        <Text style={[styles.label, { fontSize: config.label, color }]}>
          {label}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
  },
  container: {
    borderRadius: 999,
    borderWidth: 4,
    justifyContent: 'center',
    alignItems: 'center',
  },
  score: {
    fontWeight: '800',
    marginTop: 4,
  },
  outOf: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: -4,
  },
  label: {
    fontWeight: '600',
    marginTop: 6,
  },
});
