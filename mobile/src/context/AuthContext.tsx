/**
 * Authentication Context
 *
 * Provides Firebase authentication state management for the application.
 * Handles Google Sign-In, user session persistence, and Firestore profile sync.
 *
 * Features:
 * - Google Sign-In with popup (web) or redirect flow
 * - Automatic session persistence
 * - User profile sync to Firestore on login
 * - Account deletion with data cleanup
 *
 * @module context/AuthContext
 * @author Uday Tamma
 * @license MIT
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import {
  User,
  signInWithPopup,
  signInWithCredential,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  deleteUser,
  GoogleAuthProvider,
} from 'firebase/auth';
import {
  doc,
  setDoc,
  getDoc,
  deleteDoc,
  serverTimestamp,
  collection,
  getDocs,
  writeBatch,
} from 'firebase/firestore';
import { Platform } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { auth, db, googleProvider } from '../config/firebase';
import { UserProfile } from '../types';

// Complete auth session for Expo
WebBrowser.maybeCompleteAuthSession();

// =============================================================================
// Type Definitions
// =============================================================================

/**
 * User data stored in Firestore.
 */
export interface FirestoreUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  provider: string;
  createdAt: ReturnType<typeof serverTimestamp>;
  lastLoginAt: ReturnType<typeof serverTimestamp>;
  profile?: UserProfile;
}

/**
 * Authentication context value shape.
 */
interface AuthContextType {
  /** Current Firebase user (null if not logged in) */
  user: User | null;
  /** User profile from Firestore */
  userProfile: FirestoreUser | null;
  /** Loading state during auth operations */
  loading: boolean;
  /** Error message from last operation */
  error: string | null;
  /** Sign in with Google */
  signInWithGoogle: () => Promise<void>;
  /** Sign out current user */
  signOut: () => Promise<void>;
  /** Delete user account and all data */
  deleteAccount: () => Promise<void>;
  /** Update user profile in Firestore */
  updateUserProfile: (profile: Partial<UserProfile>) => Promise<void>;
  /** Clear error state */
  clearError: () => void;
}

// =============================================================================
// Context & Provider
// =============================================================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication provider component.
 *
 * Wraps the application to provide auth state and methods to all descendants.
 */
export function AuthProvider({ children }: AuthProviderProps): React.JSX.Element {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<FirestoreUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Expo Google Auth configuration
  const [request, response, promptAsync] = Google.useAuthRequest({
    // Web client ID from Firebase Console
    webClientId: '410617034936-cqd9kv1puvt1e4ti1ij0tr3pburmd0h7.apps.googleusercontent.com',
    // Note: For production, add iOS and Android client IDs
  });

  // Listen for auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);

      if (firebaseUser) {
        // Fetch or create user profile in Firestore
        await syncUserToFirestore(firebaseUser);
      } else {
        setUserProfile(null);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // Handle Expo Google auth response
  useEffect(() => {
    if (response?.type === 'success') {
      const { id_token } = response.params;
      const credential = GoogleAuthProvider.credential(id_token);
      signInWithCredential(auth, credential).catch((err) => {
        setError(err.message);
      });
    }
  }, [response]);

  /**
   * Sync user data to Firestore on login.
   */
  const syncUserToFirestore = async (firebaseUser: User): Promise<void> => {
    try {
      const userRef = doc(db, 'users', firebaseUser.uid);
      const userSnap = await getDoc(userRef);

      if (userSnap.exists()) {
        // Update last login time
        const existingData = userSnap.data() as FirestoreUser;
        await setDoc(userRef, {
          ...existingData,
          lastLoginAt: serverTimestamp(),
        }, { merge: true });
        setUserProfile({ ...existingData, lastLoginAt: serverTimestamp() });
      } else {
        // Create new user profile
        const newUser: FirestoreUser = {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
          photoURL: firebaseUser.photoURL,
          provider: firebaseUser.providerData[0]?.providerId || 'unknown',
          createdAt: serverTimestamp(),
          lastLoginAt: serverTimestamp(),
          profile: {
            allergies: [],
            skinType: 'normal',
            expertise: 'beginner',
          },
        };
        await setDoc(userRef, newUser);
        setUserProfile(newUser);
      }
    } catch (err) {
      console.error('Error syncing user to Firestore:', err);
    }
  };

  /**
   * Sign in with Google.
   * Uses popup on web, Expo auth session on native.
   */
  const signInWithGoogle = async (): Promise<void> => {
    setError(null);
    setLoading(true);

    try {
      if (Platform.OS === 'web') {
        // Web: Use Firebase popup
        await signInWithPopup(auth, googleProvider);
      } else {
        // Native: Use Expo auth session
        await promptAsync();
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Sign in failed';
      setError(errorMessage);
      console.error('Sign in error:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sign out current user.
   */
  const signOut = async (): Promise<void> => {
    setError(null);
    try {
      await firebaseSignOut(auth);
      setUserProfile(null);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Sign out failed';
      setError(errorMessage);
    }
  };

  /**
   * Delete user account and all associated data.
   * This is irreversible and complies with GDPR right to deletion.
   */
  const deleteAccount = async (): Promise<void> => {
    if (!user) {
      setError('No user logged in');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      // Delete user's scan history subcollection
      const scansRef = collection(db, 'users', user.uid, 'scans');
      const scansSnap = await getDocs(scansRef);

      const batch = writeBatch(db);
      scansSnap.docs.forEach((scanDoc) => {
        batch.delete(scanDoc.ref);
      });

      // Delete user document
      batch.delete(doc(db, 'users', user.uid));
      await batch.commit();

      // Delete Firebase auth user
      await deleteUser(user);

      setUserProfile(null);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Account deletion failed';
      setError(errorMessage);
      console.error('Delete account error:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Update user profile in Firestore.
   */
  const updateUserProfile = async (profile: Partial<UserProfile>): Promise<void> => {
    if (!user) {
      setError('No user logged in');
      return;
    }

    try {
      const userRef = doc(db, 'users', user.uid);
      await setDoc(userRef, {
        profile: {
          ...userProfile?.profile,
          ...profile,
        },
      }, { merge: true });

      // Update local state
      if (userProfile) {
        setUserProfile({
          ...userProfile,
          profile: {
            ...userProfile.profile,
            ...profile,
          } as UserProfile,
        });
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Profile update failed';
      setError(errorMessage);
    }
  };

  /**
   * Clear error state.
   */
  const clearError = (): void => {
    setError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        userProfile,
        loading,
        error,
        signInWithGoogle,
        signOut,
        deleteAccount,
        updateUserProfile,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

/**
 * Custom hook for consuming auth context.
 *
 * @returns Auth context value with user state and methods
 * @throws Error if used outside of AuthProvider
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
