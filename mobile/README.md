# Ingredient Scanner Mobile & Web App

Cross-platform React Native/Expo application for the AI Ingredient Safety Analyzer. Scan product labels, get instant ingredient analysis, and receive personalized safety recommendations.

**Supports:** iOS, Android, and Web browsers

## Live Demos

| Platform | URL |
|----------|-----|
| Web App | Coming Soon |
| API | https://api.zeroleaf.dev |

## Features

### Core Functionality
- **Camera Scanning** - Capture ingredient labels directly from products
- **Gallery Import** - Select existing photos from your device
- **Multi-language OCR** - Automatically detect and translate non-English labels
- **Personalized Analysis** - Configure allergies, skin type, and expertise level
- **Safety Reports** - View detailed safety analysis with risk ratings

### User Experience
- **Dark/Light Theme** - Toggle between themes in profile settings
- **Expandable Cards** - Tap ingredients for detailed safety information
- **Safety Visualization** - Color-coded bars and scores for quick assessment
- **Allergen Warnings** - Prominent alerts for matched allergies
- **Cross-Platform** - Same codebase for mobile and web

### Authentication & User Management
- **Google Sign-In** - Firebase Authentication with OAuth
- **Guest Mode** - Anonymous usage without account
- **Preferences Sync** - Settings sync to Firestore across devices
- **Profile Avatar** - Google photo or colored initial fallback
- **Privacy Policy** - In-app modal (works offline)
- **Account Deletion** - GDPR-compliant with collapsible Danger Zone

### Supported OCR Languages
English, French, Spanish, German, Italian, Korean, Japanese, Chinese, Portuguese

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Node.js | 18+ |
| npm | 9+ |
| Expo CLI | Latest |
| Expo Go app | iOS/Android (optional for mobile testing) |

---

## Quick Start

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Configure API URL (Development Only)

For local development, update the API URL in `src/services/api.ts`.

The app automatically uses:
- **Production** (web builds, native releases): `https://api.zeroleaf.dev`
- **Development** (Expo Go): Local IP address

To find your local IP:

```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'

# Windows
ipconfig | findstr IPv4
```

### 3. Start Development Server

```bash
cd mobile
npx expo start
```

### 4. Run on Platform

**Web Browser:**
```bash
# Press 'w' in Expo CLI, or:
npx expo start --web
```

**Mobile (Expo Go):**
1. Install **Expo Go** from App Store (iOS) or Play Store (Android)
2. Scan the QR code displayed in terminal
3. Ensure phone and computer are on same WiFi network

**Mobile (Development Build):**
```bash
npx expo run:ios     # or run:android
```

---

## Project Structure

```
mobile/
├── App.tsx                         # App entry with Auth, Preferences & Theme providers
├── app.json                        # Expo configuration
├── package.json                    # Dependencies & scripts
├── tsconfig.json                   # TypeScript config
│
├── src/
│   ├── components/
│   │   ├── ImageCapture.tsx        # Camera interface (native)
│   │   ├── ImageCapture.web.tsx    # Camera interface (web)
│   │   ├── IngredientCard.tsx      # Expandable ingredient details
│   │   ├── PrivacyPolicyModal.tsx  # In-app privacy policy display
│   │   ├── ProfileAvatar.tsx       # User avatar (photo or initial)
│   │   ├── ProfileSelector.tsx     # User profile, auth & account settings
│   │   ├── ResultsHeader.tsx       # Analysis summary header
│   │   ├── RiskBadge.tsx           # Risk level indicator
│   │   ├── SafetyBar.tsx           # Safety score bar
│   │   ├── SafetyMeter.tsx         # Overall safety visualization
│   │   └── index.ts                # Component exports
│   │
│   ├── screens/
│   │   ├── HomeScreen.tsx          # Main app screen (navigation hub)
│   │   └── LoginScreen.tsx         # Authentication screen
│   │
│   ├── context/
│   │   ├── AuthContext.tsx         # Firebase authentication state
│   │   ├── PreferencesContext.tsx  # User preferences with Firestore sync
│   │   └── ThemeContext.tsx        # Dark/Light theme state
│   │
│   ├── config/
│   │   └── firebase.ts             # Firebase configuration
│   │
│   ├── services/
│   │   ├── api.ts                  # Backend API client (auto-detects env)
│   │   └── ocr.ts                  # Image processing & OCR
│   │
│   └── types/
│       └── index.ts                # TypeScript definitions
│
├── __tests__/                      # Jest test files
│   ├── api.test.ts
│   ├── components.test.tsx
│   ├── ThemeContext.test.tsx
│   └── types.test.ts
│
└── assets/
    ├── icon.png                    # App icon
    ├── splash-icon.png             # Splash screen
    ├── favicon.png                 # Web favicon
    └── adaptive-icon.png           # Android adaptive icon
```

---

## Component Reference

### ImageCapture
Camera interface for capturing ingredient labels.

```tsx
<ImageCapture
  onCapture={(base64Image) => handleCapture(base64Image)}
  onCancel={() => setShowCamera(false)}
/>
```

### IngredientCard
Expandable card showing ingredient safety details.

```tsx
<IngredientCard ingredient={ingredientDetail} />
```

**Displays:**
- Ingredient name with safety score
- Color-coded safety bar
- Purpose tag
- Expandable details (origin, concerns, recommendation)
- Allergen match warnings

### ProfileAvatar
Displays user's Google profile picture or a colored initial fallback.

```tsx
<ProfileAvatar
  user={user}
  size={48}
  onPress={() => setCurrentScreen('profile')}
/>
```

**Behavior:**
- Shows Google profile photo if available
- Falls back to colored circle with user's initial
- Consistent color generation from user ID

### ProfileSelector
User profile configuration with authentication and account management.

```tsx
<ProfileSelector
  profile={userProfile}
  onProfileChange={setUserProfile}
/>
```

**Settings:**
- User profile display (ProfileAvatar, name, email)
- Dark/Light mode toggle
- Known allergies (multi-select)
- Skin type selection
- Explanation style (Simple/Technical)
- Privacy Policy (in-app modal)
- Collapsible Danger Zone with account deletion

### ResultsHeader
Analysis summary with overall risk assessment.

```tsx
<ResultsHeader
  productName="CeraVe Moisturizer"
  overallRisk="low"
  averageSafetyScore={8.2}
  ingredientCount={12}
  allergenWarnings={[]}
/>
```

---

## API Integration

### Services

**api.ts** - Backend communication:
```typescript
// Analyze ingredients
const result = await analyzeIngredients({
  product_name: 'Product Name',
  ingredients: 'Water, Glycerin...',
  allergies: ['Fragrance'],
  skin_type: 'sensitive',
  expertise: 'beginner'
});
```

**ocr.ts** - Image processing:
```typescript
// Extract ingredients from image
const ingredients = await extractIngredients(base64Image);
// Returns English text (auto-translated if needed)
```

---

## Theme System

The app supports dark and light themes via React Context:

```typescript
// Access theme in components
const { theme, themeMode, toggleTheme } = useTheme();

// Apply theme colors
<View style={{ backgroundColor: theme.colors.background }}>
  <Text style={{ color: theme.colors.textPrimary }}>
    Content
  </Text>
</View>
```

**Color Tokens:**
- `background`, `card`, `cardBorder`
- `textPrimary`, `textSecondary`, `textMuted`
- `primary`, `success`, `warning`, `danger`
- `divider`, `inputBackground`

---

## Troubleshooting

### "Cannot connect to server"

1. Verify backend is running: `curl http://YOUR_IP:8000/health`
2. Ensure phone and computer are on same WiFi network
3. Check IP address in `api.ts`
4. Temporarily disable firewall

### Camera not working

1. Grant camera permission when prompted
2. iOS: Settings > Expo Go > Camera
3. Android: Settings > Apps > Expo Go > Permissions

### OCR not extracting text

1. Ensure good lighting
2. Hold camera steady
3. Frame the ingredient list clearly
4. Try selecting a clearer image from gallery

### App crashes on launch

1. Clear Expo Go cache: shake device > "Reload"
2. Restart Expo development server
3. Check terminal for error messages

---

## Building for Production

### Web Build

```bash
# Build static web files
npm run build:web

# Test locally
npm run serve:web
# Opens at http://localhost:3000

# Deploy to hosting (Cloudflare Pages, Vercel, Netlify)
# Upload the 'dist' folder
```

### Development Build (Native)

```bash
npx expo prebuild
npx expo run:ios     # or run:android
```

### EAS Build (Cloud)

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Build for Android
eas build --platform android --profile preview

# Build for iOS
eas build --platform ios --profile preview
```

### App Store Submission

```bash
# Production builds
eas build --platform android --profile production
eas build --platform ios --profile production

# Submit to stores
eas submit --platform android
eas submit --platform ios
```

---

## Development

### NPM Scripts

```bash
# Start development server
npm start                 # or: npx expo start

# Run on specific platform
npm run web              # Web browser
npm run ios              # iOS Simulator
npm run android          # Android Emulator

# Build web app
npm run build:web        # Build static files
npm run serve:web        # Serve locally

# Testing
npm test                 # Run all tests
npm run test:watch       # Watch mode
npm run test:coverage    # Coverage report

# Code quality
npm run typecheck        # TypeScript check
npm run lint             # ESLint check
```

### Type Checking

```bash
npm run typecheck
# or: npx tsc --noEmit
```

### Testing

```bash
# Run all tests
npm test

# Watch mode for development
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Testing on Device

```bash
# Start with tunnel (for network issues)
npx expo start --tunnel

# Clear cache
npx expo start --clear
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `expo` | Development framework |
| `expo-camera` | Camera access (native) |
| `expo-image-picker` | Gallery selection |
| `expo-status-bar` | Status bar styling |
| `react-native-safe-area-context` | Safe area handling |
| `react-native-web` | Web platform support |
| `react-dom` | Web DOM rendering |
| `axios` | HTTP client |

### Dev Dependencies

| Package | Purpose |
|---------|---------|
| `jest` | Test runner |
| `jest-expo` | Expo Jest preset |
| `@testing-library/react-native` | Component testing |
| `typescript` | Type checking |

---

## Version History

| Version | Changes |
|---------|---------|
| 3.0.0 | Firebase Auth, PreferencesContext, ProfileAvatar, Danger Zone, Privacy Modal |
| 2.1.1 | Fixed web camera/gallery flow, improved UX |
| 2.1.0 | Web platform support, comprehensive tests |
| 2.0.0 | Dark/light theme, multi-language OCR |
| 1.0.0 | Initial mobile app release |

---

## Related Documentation

- [Main Project README](../README.md)
- [API Documentation](https://api.zeroleaf.dev/docs)
- [Portfolio](https://zeroleaf.dev)
