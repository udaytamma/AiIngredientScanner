/**
 * User profile selector component.
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Switch,
} from 'react-native';
import { UserProfile, SkinType, ExpertiseLevel } from '../types';
import { useTheme } from '../context/ThemeContext';

interface ProfileSelectorProps {
  profile: UserProfile;
  onProfileChange: (profile: UserProfile) => void;
}

const ALLERGIES = [
  'Fragrance',
  'Sulfates',
  'Parabens',
  'Formaldehyde',
  'Peanut',
  'Tree Nut',
  'Milk/Dairy',
  'Soy',
  'Wheat/Gluten',
  'Egg',
  'Shellfish',
];

const SKIN_TYPES: { value: SkinType; label: string }[] = [
  { value: 'normal', label: 'Normal' },
  { value: 'dry', label: 'Dry' },
  { value: 'oily', label: 'Oily' },
  { value: 'combination', label: 'Combination' },
  { value: 'sensitive', label: 'Sensitive' },
];

const EXPERTISE_LEVELS: { value: ExpertiseLevel; label: string }[] = [
  { value: 'beginner', label: 'Simple' },
  { value: 'expert', label: 'Technical' },
];

export function ProfileSelector({
  profile,
  onProfileChange,
}: ProfileSelectorProps) {
  const { theme, themeMode, toggleTheme } = useTheme();
  const isDark = themeMode === 'dark';

  const toggleAllergy = (allergy: string) => {
    const newAllergies = profile.allergies.includes(allergy)
      ? profile.allergies.filter((a) => a !== allergy)
      : [...profile.allergies, allergy];

    onProfileChange({ ...profile, allergies: newAllergies });
  };

  const setSkinType = (skinType: SkinType) => {
    onProfileChange({ ...profile, skinType });
  };

  const setExpertise = (expertise: ExpertiseLevel) => {
    onProfileChange({ ...profile, expertise });
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Appearance */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>Appearance</Text>
        <View style={[styles.themeToggleRow, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
          <View style={styles.themeTextContainer}>
            <Text style={[styles.themeLabel, { color: theme.colors.textPrimary }]}>
              {isDark ? '🌙 Dark Mode' : '☀️ Light Mode'}
            </Text>
            <Text style={[styles.themeDescription, { color: theme.colors.textSecondary }]}>
              {isDark ? 'Easy on the eyes' : 'Bright and clear'}
            </Text>
          </View>
          <Switch
            value={isDark}
            onValueChange={toggleTheme}
            trackColor={{ false: '#d1d5db', true: '#818cf8' }}
            thumbColor={isDark ? '#6366f1' : '#f4f4f5'}
            ios_backgroundColor="#d1d5db"
          />
        </View>
      </View>

      {/* Allergies */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>Known Allergies</Text>
        <View style={styles.chipContainer}>
          {ALLERGIES.map((allergy) => (
            <TouchableOpacity
              key={allergy}
              style={[
                styles.chip,
                { backgroundColor: theme.colors.inputBackground, borderColor: theme.colors.cardBorder },
                profile.allergies.includes(allergy) && styles.chipSelected,
              ]}
              onPress={() => toggleAllergy(allergy)}
            >
              <Text
                style={[
                  styles.chipText,
                  { color: theme.colors.textSecondary },
                  profile.allergies.includes(allergy) &&
                    styles.chipTextSelected,
                ]}
              >
                {allergy}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Skin Type */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>Skin Type</Text>
        <View style={styles.optionRow}>
          {SKIN_TYPES.map((type) => (
            <TouchableOpacity
              key={type.value}
              style={[
                styles.option,
                { backgroundColor: theme.colors.inputBackground, borderColor: theme.colors.cardBorder },
                profile.skinType === type.value && styles.optionSelected,
              ]}
              onPress={() => setSkinType(type.value)}
            >
              <Text
                style={[
                  styles.optionText,
                  { color: theme.colors.textSecondary },
                  profile.skinType === type.value && styles.optionTextSelected,
                ]}
              >
                {type.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Expertise Level */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>Explanation Style</Text>
        <View style={styles.optionRow}>
          {EXPERTISE_LEVELS.map((level) => (
            <TouchableOpacity
              key={level.value}
              style={[
                styles.option,
                styles.optionWide,
                { backgroundColor: theme.colors.inputBackground, borderColor: theme.colors.cardBorder },
                profile.expertise === level.value && styles.optionSelected,
              ]}
              onPress={() => setExpertise(level.value)}
            >
              <Text
                style={[
                  styles.optionText,
                  { color: theme.colors.textSecondary },
                  profile.expertise === level.value &&
                    styles.optionTextSelected,
                ]}
              >
                {level.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
  },
  themeToggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
  },
  themeTextContainer: {
    flex: 1,
  },
  themeLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  themeDescription: {
    fontSize: 13,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  chipSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  chipText: {
    fontSize: 14,
    color: '#666',
  },
  chipTextSelected: {
    color: '#fff',
  },
  optionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  option: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  optionWide: {
    flex: 1,
    alignItems: 'center',
  },
  optionSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  optionText: {
    fontSize: 14,
    color: '#666',
  },
  optionTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
});
