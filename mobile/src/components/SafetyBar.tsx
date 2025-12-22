/**
 * Safety rating bar component.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface SafetyBarProps {
  score: number; // 1-10
  showLabel?: boolean;
}

export function SafetyBar({ score, showLabel = true }: SafetyBarProps) {
  const getColor = (rating: number): string => {
    if (rating <= 3) return '#dc3545'; // Red
    if (rating <= 6) return '#fd7e14'; // Orange
    return '#28a745'; // Green
  };

  const color = getColor(score);
  const widthPercent = (score / 10) * 100;

  return (
    <View style={styles.container}>
      <View style={styles.barBackground}>
        <View
          style={[
            styles.barFill,
            { width: `${widthPercent}%`, backgroundColor: color },
          ]}
        />
        {showLabel && (
          <Text style={styles.label}>{score}/10</Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  barBackground: {
    height: 24,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
    justifyContent: 'center',
  },
  barFill: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    borderRadius: 4,
  },
  label: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
    textAlign: 'center',
  },
});
