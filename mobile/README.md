# Ingredient Scanner Mobile App

React Native mobile application for the AI Ingredient Safety Analyzer. Scan product labels, get instant ingredient analysis, and receive personalized safety recommendations.

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

### Supported OCR Languages
English, French, Spanish, German, Italian, Korean, Japanese, Chinese, Portuguese

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Node.js | 18+ |
| npm | 9+ |
| Expo CLI | Latest |
| Expo Go app | iOS/Android |

---

## Quick Start

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Configure API URL

Find your machine's IP address:

```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'

# Windows
ipconfig | findstr IPv4
```

Edit `src/services/api.ts`:

```typescript
const API_BASE_URL = 'http://YOUR_IP_ADDRESS:8000';
```

### 3. Start Backend API

In a separate terminal:

```bash
cd /path/to/AiIngredientScanner
source venv/bin/activate
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 4. Launch Mobile App

```bash
cd mobile
npx expo start
```

### 5. Connect Your Device

1. Install **Expo Go** from App Store (iOS) or Play Store (Android)
2. Scan the QR code displayed in terminal
3. App loads on your device

---

## Project Structure

```
mobile/
├── App.tsx                         # App entry with ThemeProvider
├── app.json                        # Expo configuration
├── package.json                    # Dependencies
├── tsconfig.json                   # TypeScript config
│
├── src/
│   ├── components/
│   │   ├── ImageCapture.tsx        # Camera & gallery interface
│   │   ├── IngredientCard.tsx      # Expandable ingredient details
│   │   ├── ProfileSelector.tsx     # User profile & theme settings
│   │   ├── ResultsHeader.tsx       # Analysis summary header
│   │   ├── RiskBadge.tsx           # Risk level indicator
│   │   ├── SafetyBar.tsx           # Safety score bar
│   │   └── SafetyMeter.tsx         # Overall safety visualization
│   │
│   ├── screens/
│   │   └── HomeScreen.tsx          # Main app screen (navigation hub)
│   │
│   ├── context/
│   │   └── ThemeContext.tsx        # Dark/Light theme state
│   │
│   ├── services/
│   │   ├── api.ts                  # Backend API client
│   │   └── ocr.ts                  # Image processing & OCR
│   │
│   └── types/
│       └── index.ts                # TypeScript definitions
│
└── assets/
    ├── icon.png                    # App icon
    ├── splash-icon.png             # Splash screen
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

### ProfileSelector
User profile configuration with theme toggle.

```tsx
<ProfileSelector
  profile={userProfile}
  onProfileChange={setUserProfile}
/>
```

**Settings:**
- Dark/Light mode toggle
- Known allergies (multi-select)
- Skin type selection
- Explanation style (Simple/Technical)

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

### Development Build

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

### Type Checking

```bash
npx tsc --noEmit
```

### Linting

```bash
npm run lint
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
| `expo-camera` | Camera access |
| `expo-image-picker` | Gallery selection |
| `expo-status-bar` | Status bar styling |
| `react-native-safe-area-context` | Safe area handling |

---

## Version History

| Version | Changes |
|---------|---------|
| 2.0.0 | Dark/light theme, multi-language OCR |
| 1.0.0 | Initial mobile app release |

---

## Related Documentation

- [Main Project README](../README.md)
- [Phase 2 PRD](../../Documentation/AI_Ingredient_Scanner_Phase2_PRD.md)
- [API Reference](../README.md#api-reference)
