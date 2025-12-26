/**
 * Profile Avatar Component
 *
 * Displays user profile picture or a fallback initial with colored background.
 * Used in headers and profile sections throughout the app.
 *
 * Features:
 * - Shows Google profile picture when available
 * - Falls back to first letter of name/email in colored circle
 * - Consistent color generation based on user identifier
 * - Configurable size
 *
 * @module components/ProfileAvatar
 * @author Uday Tamma
 * @license MIT
 */

import React from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  ViewStyle,
  ImageStyle,
} from 'react-native';
import { User } from 'firebase/auth';

/**
 * Avatar color palette for fallback initials.
 * Colors are vibrant and accessible.
 */
const AVATAR_COLORS = [
  '#6366f1', // Indigo
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#ef4444', // Red
  '#f97316', // Orange
  '#eab308', // Yellow
  '#22c55e', // Green
  '#14b8a6', // Teal
  '#06b6d4', // Cyan
  '#3b82f6', // Blue
];

interface ProfileAvatarProps {
  /** Firebase user object */
  user: User | null;
  /** Avatar size in pixels */
  size?: number;
  /** Callback when avatar is pressed */
  onPress?: () => void;
  /** Additional container styles */
  style?: ViewStyle;
}

/**
 * Generates a consistent color based on a string identifier.
 * Uses simple hash to always return same color for same input.
 */
function getColorFromString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
}

/**
 * Extracts initial letter from user display name or email.
 */
function getInitial(user: User | null): string {
  if (!user) return '?';

  if (user.displayName) {
    return user.displayName.charAt(0).toUpperCase();
  }

  if (user.email) {
    return user.email.charAt(0).toUpperCase();
  }

  return '?';
}

/**
 * ProfileAvatar component.
 *
 * Renders user's Google profile picture or a colored initial fallback.
 * Tappable when onPress is provided.
 */
export function ProfileAvatar({
  user,
  size = 40,
  onPress,
  style,
}: ProfileAvatarProps): React.JSX.Element {
  const initial = getInitial(user);
  const backgroundColor = getColorFromString(user?.uid || user?.email || 'guest');

  const containerStyle: ViewStyle = {
    width: size,
    height: size,
    borderRadius: size / 2,
  };

  const imageStyle: ImageStyle = {
    width: size,
    height: size,
    borderRadius: size / 2,
  };

  const content = user?.photoURL ? (
    <Image
      source={{ uri: user.photoURL }}
      style={[styles.image, imageStyle]}
    />
  ) : (
    <View style={[styles.fallback, containerStyle, { backgroundColor }]}>
      <Text style={[styles.initial, { fontSize: size * 0.45 }]}>
        {initial}
      </Text>
    </View>
  );

  if (onPress) {
    return (
      <TouchableOpacity
        onPress={onPress}
        style={[containerStyle, style]}
        activeOpacity={0.8}
      >
        {content}
      </TouchableOpacity>
    );
  }

  return (
    <View style={[containerStyle, style]}>
      {content}
    </View>
  );
}

const styles = StyleSheet.create({
  image: {
    resizeMode: 'cover',
  },
  fallback: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  initial: {
    color: '#ffffff',
    fontWeight: '700',
  },
});

export default ProfileAvatar;
