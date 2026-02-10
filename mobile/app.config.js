// Load environment variables
import 'dotenv/config';

export default {
  expo: {
    name: "Ingredient Scanner",
    slug: "ingredient-scanner",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "automatic",
    newArchEnabled: true,
    splash: {
      image: "./assets/splash-icon.png",
      resizeMode: "contain",
      backgroundColor: "#6366f1"
    },
    ios: {
      supportsTablet: true,
      bundleIdentifier: "dev.zeroleaf.ingredientscanner",
      infoPlist: {
        NSCameraUsageDescription: "This app needs camera access to scan ingredient labels.",
        NSPhotoLibraryUsageDescription: "This app needs photo library access to select ingredient label images."
      }
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#6366f1"
      },
      edgeToEdgeEnabled: true,
      permissions: [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE"
      ],
      package: "dev.zeroleaf.ingredientscanner"
    },
    web: {
      favicon: "./assets/favicon.png",
      bundler: "metro",
      output: "single",
      name: "AI Ingredient Scanner",
      shortName: "Scanner",
      description: "AI-powered ingredient safety analyzer for food and cosmetic products",
      backgroundColor: "#f8fafc",
      themeColor: "#6366f1"
    },
    plugins: [
      [
        "expo-camera",
        {
          cameraPermission: "Allow Ingredient Scanner to access your camera to scan ingredient labels."
        }
      ],
      [
        "expo-image-picker",
        {
          photosPermission: "Allow Ingredient Scanner to access your photos to select ingredient label images."
        }
      ]
    ],
    extra: {
      eas: {
        projectId: "ingredient-scanner"
      },
      firebase: {
        apiKey: process.env.FIREBASE_API_KEY,
        authDomain: process.env.FIREBASE_AUTH_DOMAIN,
        projectId: process.env.FIREBASE_PROJECT_ID,
        storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
        messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
        appId: process.env.FIREBASE_APP_ID,
        measurementId: process.env.FIREBASE_MEASUREMENT_ID
      }
    }
  }
};
