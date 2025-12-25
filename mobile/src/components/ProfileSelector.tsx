/**
 * User profile selector component.
 *
 * Manages user preferences including:
 * - Theme (light/dark)
 * - Allergies
 * - Skin type
 * - Explanation style
 * - Account settings (sign out, delete account)
 *
 * @module components/ProfileSelector
 * @author Uday Tamma
 * @license MIT
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Switch,
  Alert,
  Image,
  Platform,
} from 'react-native';
import { UserProfile, SkinType, ExpertiseLevel } from '../types';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { PrivacyPolicyModal } from './PrivacyPolicyModal';

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
  const { user, signInWithGoogle, signOut, deleteAccount, loading } = useAuth();
  const isDark = themeMode === 'dark';
  const [isDeleting, setIsDeleting] = useState(false);
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);

  const handleSignOut = async () => {
    if (Platform.OS === 'web') {
      // Web: use native confirm dialog
      const confirmed = window.confirm('Are you sure you want to sign out?');
      if (confirmed) {
        await signOut();
      }
    } else {
      // Native: use React Native Alert
      Alert.alert(
        'Sign Out',
        'Are you sure you want to sign out?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Sign Out',
            onPress: async () => {
              await signOut();
            },
          },
        ]
      );
    }
  };

  const handleDeleteAccount = async () => {
    if (Platform.OS === 'web') {
      // Web: use native confirm dialog
      const confirmed = window.confirm(
        'This will permanently delete your account and all associated data. This action cannot be undone.\n\nAre you sure you want to delete your account?'
      );
      if (confirmed) {
        setIsDeleting(true);
        await deleteAccount();
        setIsDeleting(false);
      }
    } else {
      // Native: use React Native Alert
      Alert.alert(
        'Delete Account',
        'This will permanently delete your account and all associated data. This action cannot be undone.',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Delete',
            style: 'destructive',
            onPress: async () => {
              setIsDeleting(true);
              await deleteAccount();
              setIsDeleting(false);
            },
          },
        ]
      );
    }
  };

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
    <>
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

      {/* Account Section - Only show for authenticated users */}
      {user && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>Account</Text>

          {/* User Info */}
          <View style={[styles.userInfoRow, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
            {user.photoURL && (
              <Image source={{ uri: user.photoURL }} style={styles.userAvatar} />
            )}
            <View style={styles.userTextContainer}>
              <Text style={[styles.userName, { color: theme.colors.textPrimary }]}>
                {user.displayName || 'User'}
              </Text>
              <Text style={[styles.userEmail, { color: theme.colors.textSecondary }]}>
                {user.email}
              </Text>
            </View>
          </View>

          {/* Sign Out Button */}
          <TouchableOpacity
            style={[styles.accountButton, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}
            onPress={handleSignOut}
            disabled={loading}
          >
            <Text style={[styles.accountButtonText, { color: theme.colors.textPrimary }]}>
              Sign Out
            </Text>
          </TouchableOpacity>

          {/* Privacy Policy Link */}
          <TouchableOpacity
            style={[styles.accountButton, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}
            onPress={() => setShowPrivacyPolicy(true)}
          >
            <Text style={[styles.accountButtonText, { color: theme.colors.textPrimary }]}>
              Privacy Policy
            </Text>
          </TouchableOpacity>

          {/* Delete Account Button */}
          <TouchableOpacity
            style={[styles.dangerButton, { backgroundColor: theme.colors.danger + '15', borderColor: theme.colors.danger }]}
            onPress={handleDeleteAccount}
            disabled={loading || isDeleting}
          >
            <Text style={[styles.dangerButtonText, { color: theme.colors.danger }]}>
              {isDeleting ? 'Deleting...' : 'Delete Account'}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Guest Mode Info */}
      {!user && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>Account</Text>
          <View style={[styles.guestInfo, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
            <Text style={[styles.guestInfoText, { color: theme.colors.textSecondary }]}>
              You're using the app as a guest. Sign in with Google to save your preferences and scan history.
            </Text>
          </View>

          {/* Sign In with Google Button */}
          <TouchableOpacity
            style={[styles.googleSignInButton]}
            onPress={signInWithGoogle}
            disabled={loading}
          >
            <Image
              source={require('../../assets/google-icon.png')}
              style={styles.googleSignInIcon}
              resizeMode="contain"
            />
            <Text style={styles.googleSignInText}>
              {loading ? 'Signing in...' : 'Sign in with Google'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.accountButton, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}
            onPress={() => setShowPrivacyPolicy(true)}
          >
            <Text style={[styles.accountButtonText, { color: theme.colors.textPrimary }]}>
              Privacy Policy
            </Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>

      {/* Privacy Policy Modal */}
      <PrivacyPolicyModal
        visible={showPrivacyPolicy}
        onClose={() => setShowPrivacyPolicy(false)}
      />
    </>
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
  userInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  userAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    marginRight: 12,
  },
  userTextContainer: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  userEmail: {
    fontSize: 13,
  },
  accountButton: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 8,
    alignItems: 'center',
  },
  accountButtonText: {
    fontSize: 15,
    fontWeight: '500',
  },
  dangerButton: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginTop: 8,
    alignItems: 'center',
  },
  dangerButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
  guestInfo: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  guestInfoText: {
    fontSize: 14,
    lineHeight: 20,
  },
  googleSignInButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  googleSignInIcon: {
    width: 20,
    height: 20,
    marginRight: 10,
  },
  googleSignInText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1f2937',
  },
});
