/**
 * Login Screen
 *
 * Premium welcome screen with Google Sign-In and guest mode options.
 * Features modern gradient design, animated elements, and professional polish.
 *
 * @module screens/LoginScreen
 * @author Uday Tamma
 * @license MIT
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Image,
  Linking,
  Platform,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const { width, height } = Dimensions.get('window');

interface LoginScreenProps {
  onGuestMode?: () => void;
}

/**
 * LoginScreen component.
 *
 * Displays premium welcome experience with Google Sign-In button.
 * Includes feature highlights and privacy policy links.
 */
export function LoginScreen({ onGuestMode }: LoginScreenProps): React.JSX.Element {
  const { signInWithGoogle, loading, error, clearError } = useAuth();
  const { theme, themeMode } = useTheme();
  const isDark = themeMode === 'dark';

  const handlePrivacyPolicy = () => {
    Linking.openURL('https://docs.zeroleaf.dev/privacy');
  };

  const handleSignIn = async () => {
    clearError();
    await signInWithGoogle();
  };

  // Gradient colors based on theme
  const gradientColors = isDark
    ? ['#0f0f23', '#1a1a3e', '#0f0f23'] as const
    : ['#667eea', '#764ba2', '#f093fb'] as const;

  return (
    <View style={styles.container}>
      {/* Background Gradient */}
      <LinearGradient
        colors={gradientColors}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      />

      {/* Decorative Elements */}
      <View style={styles.decorativeContainer}>
        <View style={[styles.decorativeCircle, styles.circle1, isDark && styles.circleDark]} />
        <View style={[styles.decorativeCircle, styles.circle2, isDark && styles.circleDark]} />
        <View style={[styles.decorativeCircle, styles.circle3, isDark && styles.circleDark]} />
      </View>

      {/* Content */}
      <View style={styles.content}>
        {/* Logo Section */}
        <View style={styles.logoSection}>
          <View style={styles.logoContainer}>
            <View style={styles.logoInner}>
              <Text style={styles.logoIcon}>🔬</Text>
            </View>
            <View style={styles.logoPulse} />
          </View>
          <Text style={styles.appName}>Ingredient Analyzer</Text>
          <Text style={styles.tagline}>
            AI-powered safety analysis for{'\n'}food & cosmetic ingredients
          </Text>
        </View>

        {/* Feature Pills */}
        <View style={styles.featurePills}>
          <View style={[styles.pill, isDark && styles.pillDark]}>
            <Text style={styles.pillIcon}>📷</Text>
            <Text style={[styles.pillText, isDark && styles.pillTextDark]}>Scan Labels</Text>
          </View>
          <View style={[styles.pill, isDark && styles.pillDark]}>
            <Text style={styles.pillIcon}>🧠</Text>
            <Text style={[styles.pillText, isDark && styles.pillTextDark]}>AI Analysis</Text>
          </View>
          <View style={[styles.pill, isDark && styles.pillDark]}>
            <Text style={styles.pillIcon}>⚠️</Text>
            <Text style={[styles.pillText, isDark && styles.pillTextDark]}>Allergy Alerts</Text>
          </View>
        </View>

        {/* Error Message */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Auth Buttons */}
        <View style={styles.authSection}>
          {/* Google Sign-In Button */}
          <TouchableOpacity
            style={styles.googleButton}
            onPress={handleSignIn}
            disabled={loading}
            activeOpacity={0.9}
          >
            {loading ? (
              <ActivityIndicator color="#4285F4" size="small" />
            ) : (
              <>
                <View style={styles.googleIconContainer}>
                  <Image
                    source={require('../../assets/google-icon.png')}
                    style={styles.googleIcon}
                    resizeMode="contain"
                  />
                </View>
                <Text style={styles.googleButtonText}>Continue with Google</Text>
              </>
            )}
          </TouchableOpacity>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={[styles.dividerLine, isDark && styles.dividerLineDark]} />
            <Text style={[styles.dividerText, isDark && styles.dividerTextDark]}>or</Text>
            <View style={[styles.dividerLine, isDark && styles.dividerLineDark]} />
          </View>

          {/* Guest Mode Button */}
          <TouchableOpacity
            style={[styles.guestButton, isDark && styles.guestButtonDark]}
            onPress={onGuestMode}
            activeOpacity={0.8}
          >
            <Text style={styles.guestButtonText}>Continue as Guest</Text>
          </TouchableOpacity>

          {/* Benefits note */}
          <Text style={styles.benefitsNote}>
            Sign in to save preferences & scan history
          </Text>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            By continuing, you agree to our{' '}
          </Text>
          <TouchableOpacity onPress={handlePrivacyPolicy}>
            <Text style={styles.linkText}>Privacy Policy</Text>
          </TouchableOpacity>
        </View>

        {/* Brand */}
        <View style={styles.brandContainer}>
          <Text style={styles.brandText}>by</Text>
          <Text style={styles.brandName}>zeroleaf</Text>
        </View>
      </View>
    </View>
  );
}

// =============================================================================
// Styles
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    ...StyleSheet.absoluteFillObject,
  },
  decorativeContainer: {
    ...StyleSheet.absoluteFillObject,
    overflow: 'hidden',
  },
  decorativeCircle: {
    position: 'absolute',
    borderRadius: 999,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
  },
  circleDark: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
  },
  circle1: {
    width: width * 0.8,
    height: width * 0.8,
    top: -width * 0.3,
    right: -width * 0.2,
  },
  circle2: {
    width: width * 0.6,
    height: width * 0.6,
    bottom: height * 0.15,
    left: -width * 0.3,
  },
  circle3: {
    width: width * 0.4,
    height: width * 0.4,
    bottom: -width * 0.1,
    right: -width * 0.1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 28,
    paddingTop: height * 0.08,
    paddingBottom: 24,
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoContainer: {
    width: 100,
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  logoInner: {
    width: 88,
    height: 88,
    borderRadius: 28,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.25,
        shadowRadius: 16,
      },
      android: {
        elevation: 12,
      },
      web: {
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
      },
    }),
  },
  logoPulse: {
    position: 'absolute',
    width: 100,
    height: 100,
    borderRadius: 32,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  logoIcon: {
    fontSize: 42,
  },
  appName: {
    fontSize: 32,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 12,
    textAlign: 'center',
    letterSpacing: -0.5,
  },
  tagline: {
    fontSize: 17,
    color: 'rgba(255, 255, 255, 0.85)',
    textAlign: 'center',
    lineHeight: 24,
  },
  featurePills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 10,
    marginBottom: 40,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.25)',
  },
  pillDark: {
    backgroundColor: 'rgba(99, 102, 241, 0.25)',
    borderColor: 'rgba(99, 102, 241, 0.4)',
  },
  pillIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  pillText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  pillTextDark: {
    color: 'rgba(255, 255, 255, 0.95)',
  },
  errorContainer: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.4)',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    marginBottom: 20,
  },
  errorText: {
    fontSize: 14,
    color: '#fca5a5',
    textAlign: 'center',
  },
  authSection: {
    alignItems: 'center',
    marginBottom: 24,
  },
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 16,
    width: '100%',
    maxWidth: 340,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.15,
        shadowRadius: 12,
      },
      android: {
        elevation: 6,
      },
      web: {
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
      },
    }),
  },
  googleIconContainer: {
    width: 24,
    height: 24,
    marginRight: 12,
  },
  googleIcon: {
    width: 24,
    height: 24,
  },
  googleButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1f2937',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    maxWidth: 340,
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
  },
  dividerLineDark: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
  },
  dividerText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    paddingHorizontal: 16,
    fontWeight: '500',
  },
  dividerTextDark: {
    color: 'rgba(255, 255, 255, 0.5)',
  },
  guestButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.4)',
    width: '100%',
    maxWidth: 340,
  },
  guestButtonDark: {
    borderColor: 'rgba(99, 102, 241, 0.5)',
  },
  guestButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#ffffff',
  },
  benefitsNote: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 16,
    textAlign: 'center',
  },
  footer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 'auto',
  },
  footerText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  linkText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  brandContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    gap: 6,
  },
  brandText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.5)',
  },
  brandName: {
    fontSize: 14,
    fontWeight: '700',
    color: 'rgba(255, 255, 255, 0.75)',
    letterSpacing: 0.5,
  },
});

export default LoginScreen;
