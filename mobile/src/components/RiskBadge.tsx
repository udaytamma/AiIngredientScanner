/**
 * Risk level badge component.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface RiskBadgeProps {
  risk: string;
  size?: 'small' | 'medium' | 'large';
}

export function RiskBadge({ risk, size = 'medium' }: RiskBadgeProps) {
  const getColor = (riskLevel: string): string => {
    const level = riskLevel.toLowerCase();
    if (level === 'high' || level === 'avoid') return '#dc3545';
    if (level === 'medium' || level === 'caution') return '#fd7e14';
    return '#28a745';
  };

  const getLabel = (riskLevel: string): string => {
    const level = riskLevel.toLowerCase();
    if (level === 'high') return 'HIGH RISK';
    if (level === 'medium') return 'MODERATE';
    if (level === 'avoid') return 'AVOID';
    if (level === 'caution') return 'CAUTION';
    return 'SAFE';
  };

  const sizeStyles = {
    small: { paddingHorizontal: 8, paddingVertical: 4, fontSize: 10 },
    medium: { paddingHorizontal: 12, paddingVertical: 6, fontSize: 12 },
    large: { paddingHorizontal: 16, paddingVertical: 8, fontSize: 14 },
  };

  const color = getColor(risk);
  const { paddingHorizontal, paddingVertical, fontSize } = sizeStyles[size];

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: color, paddingHorizontal, paddingVertical },
      ]}
    >
      <Text style={[styles.text, { fontSize }]}>{getLabel(risk)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  text: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
