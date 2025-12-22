/**
 * Results screen header with product info and overall safety.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafetyMeter } from './SafetyMeter';
import { RiskLevel } from '../types';
import { useTheme } from '../context/ThemeContext';

interface ResultsHeaderProps {
  productName: string;
  overallRisk: string;
  averageSafetyScore: number;
  ingredientCount: number;
  allergenWarnings: string[];
}

const getRiskConfig = (risk: string) => {
  const riskLower = risk.toLowerCase();
  switch (riskLower) {
    case 'low':
      return {
        label: 'LOW RISK',
        color: '#22c55e',
        bgColor: '#dcfce7',
        icon: '✓',
      };
    case 'medium':
      return {
        label: 'MEDIUM RISK',
        color: '#f59e0b',
        bgColor: '#fef3c7',
        icon: '◐',
      };
    case 'high':
      return {
        label: 'HIGH RISK',
        color: '#ef4444',
        bgColor: '#fee2e2',
        icon: '!',
      };
    default:
      return {
        label: 'UNKNOWN',
        color: '#6b7280',
        bgColor: '#f3f4f6',
        icon: '?',
      };
  }
};

export function ResultsHeader({
  productName,
  overallRisk,
  averageSafetyScore,
  ingredientCount,
  allergenWarnings,
}: ResultsHeaderProps) {
  const { theme } = useTheme();
  const riskConfig = getRiskConfig(overallRisk);

  return (
    <View style={styles.container}>
      {/* Product Name */}
      <Text style={[styles.productName, { color: theme.colors.textPrimary }]} numberOfLines={2}>
        {productName}
      </Text>

      {/* Safety Overview Card */}
      <View style={[styles.safetyCard, { backgroundColor: theme.colors.card }]}>
        <View style={styles.safetyRow}>
          {/* Safety Meter */}
          <SafetyMeter score={averageSafetyScore} size="large" />

          {/* Risk Badge */}
          <View style={styles.riskSection}>
            <View
              style={[
                styles.riskBadge,
                { backgroundColor: riskConfig.bgColor },
              ]}
            >
              <Text style={[styles.riskIcon, { color: riskConfig.color }]}>
                {riskConfig.icon}
              </Text>
              <Text style={[styles.riskLabel, { color: riskConfig.color }]}>
                {riskConfig.label}
              </Text>
            </View>
            <Text style={[styles.ingredientCount, { color: theme.colors.textSecondary }]}>
              {ingredientCount} ingredient{ingredientCount !== 1 ? 's' : ''} analyzed
            </Text>
          </View>
        </View>
      </View>

      {/* Allergen Warnings */}
      {allergenWarnings.length > 0 && (
        <View style={styles.warningsCard}>
          <View style={styles.warningsHeader}>
            <Text style={styles.warningsIcon}>⚠️</Text>
            <Text style={styles.warningsTitle}>Allergen Alert</Text>
          </View>
          {allergenWarnings.map((warning, index) => (
            <Text key={index} style={styles.warningText}>
              • {warning}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  productName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 16,
  },
  safetyCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
    marginBottom: 16,
  },
  safetyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 24,
  },
  riskSection: {
    flex: 1,
    alignItems: 'flex-start',
    gap: 10,
  },
  riskBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 24,
    gap: 8,
  },
  riskIcon: {
    fontSize: 18,
    fontWeight: '700',
  },
  riskLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  ingredientCount: {
    fontSize: 13,
    color: '#6b7280',
  },
  warningsCard: {
    backgroundColor: '#fffbeb',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#fbbf24',
  },
  warningsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  warningsIcon: {
    fontSize: 18,
  },
  warningsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#92400e',
  },
  warningText: {
    fontSize: 14,
    color: '#92400e',
    marginBottom: 4,
    lineHeight: 20,
  },
});
