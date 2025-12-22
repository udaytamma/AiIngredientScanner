/**
 * Expandable ingredient card with safety visualization.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  LayoutAnimation,
} from 'react-native';
import { IngredientDetail, RiskLevel } from '../types';
import { useTheme } from '../context/ThemeContext';

// Note: LayoutAnimation is now enabled by default in React Native's New Architecture

interface IngredientCardProps {
  ingredient: IngredientDetail;
}

const getRiskColor = (riskLevel: RiskLevel): string => {
  switch (riskLevel) {
    case 'low':
      return '#22c55e'; // Green
    case 'medium':
      return '#f59e0b'; // Amber
    case 'high':
      return '#ef4444'; // Red
    default:
      return '#6b7280'; // Gray
  }
};

const getScoreColor = (score: number): string => {
  if (score >= 8) return '#22c55e'; // Green
  if (score >= 6) return '#84cc16'; // Light green
  if (score >= 4) return '#f59e0b'; // Amber
  if (score >= 2) return '#f97316'; // Orange
  return '#ef4444'; // Red
};

const getScoreEmoji = (score: number): string => {
  if (score >= 8) return '✓';
  if (score >= 6) return '●';
  if (score >= 4) return '◐';
  return '!';
};

export function IngredientCard({ ingredient }: IngredientCardProps) {
  const { theme } = useTheme();
  const [expanded, setExpanded] = useState(false);

  const toggleExpanded = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
  };

  const riskColor = getRiskColor(ingredient.risk_level as RiskLevel);
  const scoreColor = getScoreColor(ingredient.safety_score);
  const scorePercent = (ingredient.safety_score / 10) * 100;

  return (
    <TouchableOpacity
      style={[
        styles.card,
        { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder },
        ingredient.is_allergen_match && styles.allergenCard,
      ]}
      onPress={toggleExpanded}
      activeOpacity={0.7}
    >
      {/* Header Row */}
      <View style={styles.header}>
        <View style={styles.nameContainer}>
          {ingredient.is_allergen_match && (
            <Text style={styles.allergenBadge}>⚠️</Text>
          )}
          <Text style={[styles.name, { color: theme.colors.textPrimary }]} numberOfLines={1}>
            {ingredient.name}
          </Text>
        </View>
        <View style={styles.scoreContainer}>
          <Text style={[styles.score, { color: scoreColor }]}>
            {ingredient.safety_score}/10
          </Text>
          <Text style={[styles.scoreEmoji, { color: scoreColor }]}>
            {getScoreEmoji(ingredient.safety_score)}
          </Text>
        </View>
      </View>

      {/* Safety Bar */}
      <View style={styles.safetyBarContainer}>
        <View style={[styles.safetyBarBackground, { backgroundColor: theme.colors.divider }]}>
          <View
            style={[
              styles.safetyBarFill,
              {
                width: `${scorePercent}%`,
                backgroundColor: scoreColor,
              },
            ]}
          />
        </View>
      </View>

      {/* Quick Info Row - Only Purpose (Origin moved to expanded section) */}
      <View style={styles.quickInfo}>
        <View style={[styles.tag, { backgroundColor: theme.colors.inputBackground }]}>
          <Text style={[styles.tagText, { color: theme.colors.textSecondary }]} numberOfLines={1}>
            {ingredient.purpose.split(',')[0]}
          </Text>
        </View>
        <View style={styles.expandIcon}>
          <Text style={[styles.expandIconText, { color: theme.colors.textMuted }]}>{expanded ? '▲' : '▼'}</Text>
        </View>
      </View>

      {/* Expanded Details */}
      {expanded && (
        <View style={[styles.details, { borderTopColor: theme.colors.divider }]}>
          {/* Purpose */}
          <View style={styles.detailSection}>
            <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Purpose</Text>
            <Text style={[styles.detailText, { color: theme.colors.textPrimary }]}>{ingredient.purpose}</Text>
          </View>

          {/* Origin */}
          <View style={styles.detailSection}>
            <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Origin</Text>
            <Text style={[styles.detailText, { color: theme.colors.textPrimary }]}>{ingredient.origin}</Text>
          </View>

          {/* Concerns */}
          {ingredient.concerns && ingredient.concerns !== 'No specific concerns' && (
            <View style={styles.detailSection}>
              <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Concerns</Text>
              <Text style={[styles.detailText, { color: theme.colors.warning }]}>
                {ingredient.concerns}
              </Text>
            </View>
          )}

          {/* Recommendation */}
          {ingredient.recommendation && (
            <View style={styles.detailSection}>
              <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Recommendation</Text>
              <View
                style={[
                  styles.recommendationBadge,
                  {
                    backgroundColor:
                      ingredient.recommendation === 'SAFE'
                        ? '#dcfce7'
                        : ingredient.recommendation === 'CAUTION'
                        ? '#fef9c3'
                        : '#fee2e2',
                  },
                ]}
              >
                <Text
                  style={[
                    styles.recommendationText,
                    {
                      color:
                        ingredient.recommendation === 'SAFE'
                          ? '#166534'
                          : ingredient.recommendation === 'CAUTION'
                          ? '#854d0e'
                          : '#991b1b',
                    },
                  ]}
                >
                  {ingredient.recommendation}
                </Text>
              </View>
            </View>
          )}

          {/* Additional Info Grid */}
          <View style={styles.infoGrid}>
            <View style={styles.infoItem}>
              <Text style={[styles.infoLabel, { color: theme.colors.textMuted }]}>Category</Text>
              <Text style={[styles.infoValue, { color: theme.colors.textPrimary }]}>{ingredient.category}</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={[styles.infoLabel, { color: theme.colors.textMuted }]}>Allergy Risk</Text>
              <Text
                style={[
                  styles.infoValue,
                  {
                    color:
                      ingredient.allergy_risk.toLowerCase() === 'high'
                        ? '#ef4444'
                        : '#22c55e',
                  },
                ]}
              >
                {ingredient.allergy_risk}
              </Text>
            </View>
          </View>

          {/* Alternatives */}
          {ingredient.alternatives && ingredient.alternatives.length > 0 && (
            <View style={styles.detailSection}>
              <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Safer Alternatives</Text>
              <View style={styles.alternativesContainer}>
                {ingredient.alternatives.map((alt, index) => (
                  <View key={index} style={styles.alternativeTag}>
                    <Text style={styles.alternativeText}>{alt}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#f0f0f0',
  },
  allergenCard: {
    borderColor: '#fbbf24',
    borderWidth: 2,
    backgroundColor: '#fffbeb',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  nameContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  allergenBadge: {
    fontSize: 16,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    flex: 1,
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  score: {
    fontSize: 16,
    fontWeight: '700',
  },
  scoreEmoji: {
    fontSize: 16,
    fontWeight: '700',
  },
  safetyBarContainer: {
    marginBottom: 10,
  },
  safetyBarBackground: {
    height: 6,
    backgroundColor: '#e5e7eb',
    borderRadius: 3,
    overflow: 'hidden',
  },
  safetyBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  quickInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  tag: {
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    flex: 1,
  },
  tagText: {
    fontSize: 12,
    color: '#4b5563',
  },
  expandIcon: {
    marginLeft: 'auto',
    padding: 4,
  },
  expandIconText: {
    fontSize: 10,
    color: '#9ca3af',
  },
  details: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  detailSection: {
    marginBottom: 14,
  },
  detailLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  detailText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  concernsText: {
    color: '#b45309',
  },
  recommendationBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  recommendationText: {
    fontSize: 12,
    fontWeight: '600',
  },
  infoGrid: {
    flexDirection: 'row',
    gap: 20,
    marginBottom: 14,
  },
  infoItem: {
    flex: 1,
  },
  infoLabel: {
    fontSize: 11,
    color: '#9ca3af',
    marginBottom: 2,
    textTransform: 'uppercase',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  alternativesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  alternativeTag: {
    backgroundColor: '#dcfce7',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  alternativeText: {
    fontSize: 12,
    color: '#166534',
  },
});
