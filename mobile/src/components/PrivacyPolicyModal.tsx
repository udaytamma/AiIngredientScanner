/**
 * Privacy Policy Modal
 *
 * In-app modal displaying the privacy policy content.
 * Keeps users within the app and works offline.
 *
 * @module components/PrivacyPolicyModal
 * @author Uday Tamma
 * @license MIT
 */

import React from 'react';
import {
  View,
  Text,
  Modal,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import { useTheme } from '../context/ThemeContext';

interface PrivacyPolicyModalProps {
  visible: boolean;
  onClose: () => void;
}

/**
 * Privacy Policy Modal component.
 *
 * Displays the full privacy policy in a scrollable modal.
 */
export function PrivacyPolicyModal({
  visible,
  onClose,
}: PrivacyPolicyModalProps): React.JSX.Element {
  const { theme } = useTheme();

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: theme.colors.cardBorder }]}>
          <Text style={[styles.title, { color: theme.colors.textPrimary }]}>
            Privacy Policy
          </Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={[styles.closeButtonText, { color: theme.colors.primary }]}>
              Done
            </Text>
          </TouchableOpacity>
        </View>

        {/* Content */}
        <ScrollView
          style={styles.content}
          contentContainerStyle={styles.contentContainer}
          showsVerticalScrollIndicator={true}
        >
          <Text style={[styles.lastUpdated, { color: theme.colors.textMuted }]}>
            Last Updated: December 25, 2024
          </Text>

          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            This Privacy Policy describes how Zeroleaf ("we", "us", or "our") collects, uses, and protects your personal information when you use our applications and services, including the AI Ingredient Safety Analyzer ("the App").
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Information We Collect
          </Text>

          <Text style={[styles.subSectionTitle, { color: theme.colors.textPrimary }]}>
            Account Information
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            When you sign in with Google, we receive:
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Email address - To identify your account
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Display name - To personalize your experience
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Profile photo - To display in the app
          </Text>

          <Text style={[styles.subSectionTitle, { color: theme.colors.textPrimary }]}>
            User Preferences
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            We store your preferences to provide personalized ingredient analysis:
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Allergies - To flag potential allergens
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Skin type - For cosmetic product recommendations
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Theme preference - Light or dark mode
          </Text>

          <Text style={[styles.subSectionTitle, { color: theme.colors.textPrimary }]}>
            What We Do NOT Collect
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Scanned ingredient images (processed in memory only)
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Precise location data
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Personal health information beyond stated allergies
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            How We Use Your Information
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Account authentication using email and display name
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Personalized analysis using your allergies and skin type
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • App improvements using anonymous usage analytics
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Data Storage and Security
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • All data is stored in Firebase/Google Cloud infrastructure
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Data is encrypted in transit (HTTPS) and at rest
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Access is restricted to authenticated users only
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Third-Party Services
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            We use the following third-party services:
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Firebase Authentication - User sign-in
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Firebase Firestore - Data storage
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Google Gemini API - Ingredient analysis
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Your Rights
          </Text>

          <Text style={[styles.subSectionTitle, { color: theme.colors.textPrimary }]}>
            Access Your Data
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            You can view your profile information directly in the app's Settings section.
          </Text>

          <Text style={[styles.subSectionTitle, { color: theme.colors.textPrimary }]}>
            Update Your Data
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            You can update your preferences (allergies, skin type, theme) at any time in the app.
          </Text>

          <Text style={[styles.subSectionTitle, { color: theme.colors.textPrimary }]}>
            Delete Your Data
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            You can delete your account and all associated data using the "Delete Account" button in Settings. This permanently removes your user profile, scan history, and all associated preferences.
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Data Retention
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Active accounts: Data retained while account is active
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Deleted accounts: All data permanently deleted within 30 days
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Children's Privacy
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            The App is not intended for children under 13. We do not knowingly collect personal information from children under 13.
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Changes to This Policy
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            We may update this Privacy Policy from time to time. We will notify you of significant changes by updating the "Last Updated" date and displaying a notice in the app.
          </Text>

          <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
            Contact Us
          </Text>
          <Text style={[styles.paragraph, { color: theme.colors.textSecondary }]}>
            For privacy-related questions or concerns:
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Email: privacy@zeroleaf.dev
          </Text>
          <Text style={[styles.bulletPoint, { color: theme.colors.textSecondary }]}>
            • Website: https://zeroleaf.dev
          </Text>

          <View style={[styles.summaryBox, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
            <Text style={[styles.summaryTitle, { color: theme.colors.textPrimary }]}>
              Summary
            </Text>
            <Text style={[styles.summaryText, { color: theme.colors.textSecondary }]}>
              We collect only what's needed to provide personalized ingredient analysis. You can update or delete your data anytime. We do not sell your data or share it with advertisers.
            </Text>
          </View>

          <View style={styles.bottomPadding} />
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    ...Platform.select({
      ios: {
        paddingTop: 60,
      },
      android: {
        paddingTop: 16,
      },
      web: {
        paddingTop: 16,
      },
    }),
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
  },
  closeButton: {
    padding: 8,
  },
  closeButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
  },
  lastUpdated: {
    fontSize: 13,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginTop: 24,
    marginBottom: 12,
  },
  subSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 16,
    marginBottom: 8,
  },
  paragraph: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
  },
  bulletPoint: {
    fontSize: 15,
    lineHeight: 24,
    paddingLeft: 8,
  },
  summaryBox: {
    marginTop: 32,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 20,
  },
  bottomPadding: {
    height: 40,
  },
});

export default PrivacyPolicyModal;
