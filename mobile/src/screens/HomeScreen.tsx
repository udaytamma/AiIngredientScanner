/**
 * Home screen - main entry point for ingredient scanning.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { ImageCapture } from '../components/ImageCapture';
import { ProfileSelector } from '../components/ProfileSelector';
import { ResultsHeader } from '../components/ResultsHeader';
import { IngredientCard } from '../components/IngredientCard';
import { extractIngredients } from '../services/ocr';
import { analyzeIngredients } from '../services/api';
import { UserProfile, AnalysisResponse } from '../types';
import { useTheme } from '../context/ThemeContext';

type Screen = 'home' | 'camera' | 'profile' | 'results';

export function HomeScreen() {
  const { theme } = useTheme();
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [productName, setProductName] = useState('');
  const [ingredients, setIngredients] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isProcessingImage, setIsProcessingImage] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(
    null
  );
  const [profile, setProfile] = useState<UserProfile>({
    allergies: [],
    skinType: 'normal',
    expertise: 'beginner',
  });

  const handleImageCaptured = async (uri: string) => {
    setCurrentScreen('home');
    setIsProcessingImage(true);

    try {
      const extractedText = await extractIngredients(uri);

      if (extractedText) {
        setIngredients(extractedText);
        Alert.alert(
          'Ingredients Extracted',
          'Review the extracted ingredients and make any corrections before analyzing.'
        );
      } else {
        Alert.alert(
          'No Ingredients Found',
          'Could not find ingredient list in the image. Try pointing camera directly at the ingredients label or enter manually.'
        );
      }
    } catch (error) {
      console.error('OCR error:', error);
      Alert.alert(
        'Error',
        'Failed to process image. Please try again or enter ingredients manually.'
      );
    } finally {
      setIsProcessingImage(false);
    }
  };

  const handlePickFromGallery = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        await handleImageCaptured(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Gallery error:', error);
      Alert.alert('Error', 'Failed to select image. Please try again.');
    }
  };

  const handleAnalyze = async () => {
    if (!ingredients.trim()) {
      Alert.alert('Error', 'Please enter or scan ingredients first.');
      return;
    }

    setIsAnalyzing(true);

    try {
      const result = await analyzeIngredients({
        product_name: productName || 'Unknown Product',
        ingredients: ingredients,
        allergies: profile.allergies,
        skin_type: profile.skinType,
        expertise: profile.expertise,
      });

      setAnalysisResult(result);
      setCurrentScreen('results');
    } catch (error: any) {
      console.error('Analysis error:', error);
      Alert.alert('Analysis Failed', error.message || 'Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Camera screen
  if (currentScreen === 'camera') {
    return (
      <ImageCapture
        onImageCaptured={handleImageCaptured}
        onCancel={() => setCurrentScreen('home')}
      />
    );
  }

  // Profile screen
  if (currentScreen === 'profile') {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { backgroundColor: theme.colors.card, borderBottomColor: theme.colors.cardBorder }]}>
          <TouchableOpacity onPress={() => setCurrentScreen('home')}>
            <Text style={[styles.backButton, { color: theme.colors.info }]}>← Back</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.colors.textPrimary }]}>Your Profile</Text>
          <View style={{ width: 50 }} />
        </View>
        <View style={[styles.profileContainer, { backgroundColor: theme.colors.background }]}>
          <ProfileSelector profile={profile} onProfileChange={setProfile} />
        </View>
      </View>
    );
  }

  // Results screen
  if (currentScreen === 'results' && analysisResult) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.resultsHeaderBar, { backgroundColor: theme.colors.card, borderBottomColor: theme.colors.cardBorder }]}>
          <TouchableOpacity onPress={() => setCurrentScreen('home')}>
            <Text style={[styles.backButton, { color: theme.colors.info }]}>← Back</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.colors.textPrimary }]}>Analysis Results</Text>
          <View style={{ width: 50 }} />
        </View>

        <ScrollView
          style={styles.resultsScrollView}
          contentContainerStyle={styles.resultsContent}
          showsVerticalScrollIndicator={false}
        >
          <ResultsHeader
            productName={analysisResult.product_name}
            overallRisk={analysisResult.overall_risk}
            averageSafetyScore={analysisResult.average_safety_score}
            ingredientCount={analysisResult.ingredients?.length || 0}
            allergenWarnings={analysisResult.allergen_warnings}
          />

          <View style={styles.ingredientsSection}>
            <Text style={[styles.sectionTitle, { color: theme.colors.textPrimary }]}>
              Ingredients ({analysisResult.ingredients?.length || 0})
            </Text>
            <Text style={[styles.sectionSubtitle, { color: theme.colors.textSecondary }]}>
              Tap any ingredient for detailed information
            </Text>

            {analysisResult.ingredients && analysisResult.ingredients.length > 0 ? (
              analysisResult.ingredients.map((ingredient, index) => (
                <IngredientCard key={index} ingredient={ingredient} />
              ))
            ) : (
              <View style={[styles.noIngredientsCard, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}>
                <Text style={[styles.noIngredientsText, { color: theme.colors.textSecondary }]}>
                  Detailed ingredient breakdown not available.
                </Text>
                <Text style={[styles.summaryFallback, { color: theme.colors.textPrimary }]}>
                  {analysisResult.summary}
                </Text>
              </View>
            )}
          </View>

          <Text style={[styles.timeText, { color: theme.colors.textMuted }]}>
            Analysis completed in {analysisResult.execution_time.toFixed(1)}s
          </Text>
        </ScrollView>

        <View style={[styles.bottomButtonContainer, { backgroundColor: theme.colors.background, borderTopColor: theme.colors.cardBorder }]}>
          <TouchableOpacity
            style={styles.newAnalysisButton}
            onPress={() => {
              setAnalysisResult(null);
              setIngredients('');
              setProductName('');
              setCurrentScreen('home');
            }}
          >
            <Text style={styles.newAnalysisButtonText}>New Analysis</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Home screen - REDESIGNED
  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        style={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Header */}
        <View style={styles.homeHeader}>
          <View>
            <Text style={[styles.title, { color: theme.colors.textPrimary }]}>Ingredient Analyzer</Text>
            <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>AI-powered safety analysis</Text>
          </View>
          <TouchableOpacity
            style={[styles.profileButton, { backgroundColor: theme.colors.card }]}
            onPress={() => setCurrentScreen('profile')}
          >
            <Text style={styles.profileButtonIcon}>👤</Text>
          </TouchableOpacity>
        </View>

        {/* Scan Card - Hero Section */}
        <View style={[styles.scanCard, { backgroundColor: theme.colors.card }]}>
          <View style={styles.scanCardHeader}>
            <Text style={[styles.scanCardTitle, { color: theme.colors.textPrimary }]}>Scan Ingredients</Text>
            <Text style={[styles.scanCardSubtitle, { color: theme.colors.textSecondary }]}>
              Point your camera at the ingredient label
            </Text>
          </View>

          <TouchableOpacity
            style={[styles.cameraButton, { backgroundColor: theme.colors.primary }]}
            onPress={() => setCurrentScreen('camera')}
            disabled={isProcessingImage}
          >
            {isProcessingImage ? (
              <View style={styles.processingContainer}>
                <ActivityIndicator color="#fff" size="small" />
                <Text style={styles.processingText}>Processing...</Text>
              </View>
            ) : (
              <>
                <View style={styles.cameraIconContainer}>
                  <Text style={styles.cameraIcon}>📷</Text>
                </View>
                <Text style={styles.cameraButtonText}>Open Camera</Text>
              </>
            )}
          </TouchableOpacity>

          <View style={styles.dividerContainer}>
            <View style={[styles.dividerLine, { backgroundColor: theme.colors.divider }]} />
            <Text style={[styles.dividerText, { color: theme.colors.textMuted }]}>OR</Text>
            <View style={[styles.dividerLine, { backgroundColor: theme.colors.divider }]} />
          </View>

          <TouchableOpacity
            style={[styles.galleryButton, { backgroundColor: theme.colors.galleryBg, borderColor: theme.colors.galleryBorder }]}
            onPress={handlePickFromGallery}
            disabled={isProcessingImage}
          >
            <Text style={styles.galleryIcon}>📁</Text>
            <Text style={[styles.galleryButtonText, { color: theme.colors.galleryText }]}>Select from Photos</Text>
          </TouchableOpacity>
        </View>

        {/* Input Card */}
        <View style={[styles.inputCard, { backgroundColor: theme.colors.card }]}>
          <View style={styles.inputCardHeader}>
            <Text style={[styles.inputCardTitle, { color: theme.colors.textPrimary }]}>Product Details</Text>
            {(productName.length > 0 || ingredients.length > 0) && (
              <TouchableOpacity
                onPress={() => {
                  setProductName('');
                  setIngredients('');
                }}
              >
                <Text style={[styles.clearAllLink, { color: theme.colors.danger }]}>Clear All</Text>
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.inputGroup}>
            <Text style={[styles.label, { color: theme.colors.textSecondary }]}>Product Name</Text>
            <TextInput
              style={[styles.input, { backgroundColor: theme.colors.inputBackground, borderColor: theme.colors.cardBorder, color: theme.colors.textPrimary }]}
              value={productName}
              onChangeText={setProductName}
              placeholder="e.g., CeraVe Moisturizing Cream"
              placeholderTextColor={theme.colors.textMuted}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={[styles.label, { color: theme.colors.textSecondary }]}>Ingredients</Text>
            <TextInput
              style={[styles.input, styles.textAreaFlexible, { backgroundColor: theme.colors.inputBackground, borderColor: theme.colors.cardBorder, color: theme.colors.textPrimary }]}
              value={ingredients}
              onChangeText={setIngredients}
              placeholder="Scan a label above or paste ingredients here..."
              placeholderTextColor={theme.colors.textMuted}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
              scrollEnabled={true}
            />
            {ingredients.length > 0 && (
              <TouchableOpacity
                style={[styles.clearButton, { backgroundColor: theme.colors.allergyBg }]}
                onPress={() => setIngredients('')}
              >
                <Text style={[styles.clearButtonText, { color: theme.colors.danger }]}>Clear</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Profile Card */}
        <View style={[styles.profileCard, { backgroundColor: theme.colors.card }]}>
          <View style={styles.profileCardHeader}>
            <View style={styles.profileCardTitleRow}>
              <Text style={styles.profileCardIcon}>👤</Text>
              <Text style={[styles.profileCardTitle, { color: theme.colors.textPrimary }]}>Your Profile</Text>
            </View>
            <TouchableOpacity onPress={() => setCurrentScreen('profile')}>
              <Text style={[styles.editLink, { color: theme.colors.info }]}>Edit</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.profileTagsRow}>
            <View style={[styles.profileTag, { backgroundColor: theme.colors.profileTagBg, borderColor: theme.colors.profileTagBorder }]}>
              <Text style={[styles.profileTagLabel, { color: theme.colors.profileTagLabel }]}>Skin Type</Text>
              <Text style={[styles.profileTagValue, { color: theme.colors.profileTagText }]}>
                {profile.skinType.charAt(0).toUpperCase() + profile.skinType.slice(1)}
              </Text>
            </View>
            <View style={[styles.profileTag, { backgroundColor: theme.colors.profileTagBg, borderColor: theme.colors.profileTagBorder }]}>
              <Text style={[styles.profileTagLabel, { color: theme.colors.profileTagLabel }]}>Expertise</Text>
              <Text style={[styles.profileTagValue, { color: theme.colors.profileTagText }]}>
                {profile.expertise.charAt(0).toUpperCase() + profile.expertise.slice(1)}
              </Text>
            </View>
          </View>

          {profile.allergies.length > 0 && (
            <View style={[styles.allergiesContainer, { borderTopColor: theme.colors.divider }]}>
              <Text style={[styles.allergiesLabel, { color: theme.colors.textSecondary }]}>Allergies</Text>
              <View style={styles.allergyTags}>
                {profile.allergies.map((allergy, index) => (
                  <View key={index} style={[styles.allergyTag, { backgroundColor: theme.colors.allergyBg, borderColor: theme.colors.allergyBorder }]}>
                    <Text style={[styles.allergyTagText, { color: theme.colors.allergyText }]}>{allergy}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>

        {/* Analyze Button */}
        <TouchableOpacity
          style={[
            styles.analyzeButton,
            { backgroundColor: theme.colors.success },
            (!ingredients.trim() || isAnalyzing) && styles.analyzeButtonDisabled,
          ]}
          onPress={handleAnalyze}
          disabled={!ingredients.trim() || isAnalyzing}
        >
          {isAnalyzing ? (
            <View style={styles.analyzingContainer}>
              <ActivityIndicator color="#fff" />
              <Text style={styles.analyzingText}>Analyzing ingredients...</Text>
            </View>
          ) : (
            <>
              <Text style={styles.analyzeButtonIcon}>✨</Text>
              <Text style={styles.analyzeButtonText}>Analyze Ingredients</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Footer */}
        <Text style={[styles.footerText, { color: theme.colors.textMuted }]}>
          Powered by AI for accurate ingredient safety analysis
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  resultsHeaderBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  backButton: {
    fontSize: 16,
    color: '#3b82f6',
    fontWeight: '500',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1f2937',
  },
  homeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    marginTop: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1f2937',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 15,
    color: '#6b7280',
    marginTop: 2,
  },
  profileButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  profileButtonIcon: {
    fontSize: 22,
  },

  // Scan Card
  scanCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 24,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 5,
  },
  scanCardHeader: {
    alignItems: 'center',
    marginBottom: 20,
  },
  scanCardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 4,
  },
  scanCardSubtitle: {
    fontSize: 14,
    color: '#6b7280',
  },
  cameraButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#6366f1',
    paddingVertical: 18,
    borderRadius: 14,
    gap: 12,
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 5,
  },
  cameraIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  cameraIcon: {
    fontSize: 18,
  },
  cameraButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '700',
  },
  processingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  processingText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 18,
    gap: 12,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#e5e7eb',
  },
  dividerText: {
    fontSize: 13,
    color: '#9ca3af',
    fontWeight: '600',
  },
  galleryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ecfdf5',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 10,
    borderWidth: 1,
    borderColor: '#a7f3d0',
  },
  galleryIcon: {
    fontSize: 18,
  },
  galleryButtonText: {
    color: '#059669',
    fontSize: 15,
    fontWeight: '600',
  },

  // Input Card
  inputCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 3,
  },
  inputCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  inputCardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f2937',
  },
  clearAllLink: {
    fontSize: 14,
    fontWeight: '600',
  },
  inputGroup: {
    marginBottom: 14,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  input: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: '#1f2937',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  textAreaFlexible: {
    minHeight: 80,
    maxHeight: 300,
    textAlignVertical: 'top',
  },
  clearButton: {
    position: 'absolute',
    right: 12,
    top: 36,
    paddingHorizontal: 10,
    paddingVertical: 4,
    backgroundColor: '#fee2e2',
    borderRadius: 8,
  },
  clearButtonText: {
    fontSize: 12,
    color: '#ef4444',
    fontWeight: '600',
  },

  // Profile Card
  profileCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 3,
  },
  profileCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  profileCardTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  profileCardIcon: {
    fontSize: 18,
  },
  profileCardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f2937',
  },
  editLink: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '600',
  },
  profileTagsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  profileTag: {
    flex: 1,
    backgroundColor: '#f0f9ff',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#bae6fd',
  },
  profileTagLabel: {
    fontSize: 11,
    color: '#0369a1',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  profileTagValue: {
    fontSize: 15,
    color: '#0c4a6e',
    fontWeight: '700',
  },
  allergiesContainer: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  allergiesLabel: {
    fontSize: 11,
    color: '#6b7280',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  allergyTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  allergyTag: {
    backgroundColor: '#fef2f2',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#fecaca',
  },
  allergyTagText: {
    fontSize: 13,
    color: '#dc2626',
    fontWeight: '600',
  },

  // Analyze Button
  analyzeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#22c55e',
    paddingVertical: 20,
    borderRadius: 16,
    gap: 10,
    shadowColor: '#22c55e',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 6,
  },
  analyzeButtonDisabled: {
    backgroundColor: '#d1d5db',
    shadowColor: '#d1d5db',
    shadowOpacity: 0,
    elevation: 0,
  },
  analyzeButtonIcon: {
    fontSize: 20,
  },
  analyzeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '800',
  },
  analyzingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  analyzingText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Footer
  footerText: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: 16,
  },

  // Profile Container
  profileContainer: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f8fafc',
  },

  // Results Screen
  resultsScrollView: {
    flex: 1,
  },
  resultsContent: {
    padding: 20,
    paddingBottom: 100,
  },
  ingredientsSection: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 16,
  },
  noIngredientsCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  noIngredientsText: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 12,
  },
  summaryFallback: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 22,
  },
  timeText: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: 20,
  },
  bottomButtonContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#f8fafc',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  newAnalysisButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  newAnalysisButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
