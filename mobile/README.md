# Ingredient Scanner Mobile App

React Native + Expo mobile app for the AI Ingredient Safety Analyzer.

## Features

- **Camera Scanning**: Take photos of ingredient labels
- **Gallery Import**: Select existing photos from your device
- **OCR Text Recognition**: Automatically extract ingredient text using Google ML Kit
- **Personalized Analysis**: Configure allergies, skin type, and expertise level
- **Safety Reports**: View detailed safety analysis with risk ratings

## Prerequisites

1. **Node.js** (v18+)
2. **Expo Go** app installed on your Android phone (from Google Play Store)
3. **Backend API** running on your Mac

## Quick Start

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Configure API URL

Edit `src/services/api.ts` and update the `API_BASE_URL` with your Mac's IP address:

```typescript
// Find your IP with: ipconfig getifaddr en0 (on Mac)
const API_BASE_URL = 'http://YOUR_MAC_IP:8000';
```

### 3. Start the Backend API

In another terminal, from the project root:

```bash
cd /Users/omega/Projects/IngredientScanner
source venv/bin/activate
python api.py
```

The API will be available at `http://0.0.0.0:8000`

### 4. Start the Expo Development Server

```bash
cd mobile
npx expo start
```

### 5. Test on Your Phone

1. Open the **Expo Go** app on your Android phone
2. Scan the QR code shown in the terminal
3. The app will load on your phone

## Project Structure

```
mobile/
├── App.tsx                    # Main app entry point
├── app.json                   # Expo configuration
├── src/
│   ├── components/
│   │   ├── ImageCapture.tsx   # Camera/gallery component
│   │   ├── ProfileSelector.tsx # User profile settings
│   │   ├── RiskBadge.tsx      # Risk level badge
│   │   └── SafetyBar.tsx      # Safety rating bar
│   ├── screens/
│   │   └── HomeScreen.tsx     # Main screen
│   ├── services/
│   │   ├── api.ts             # Backend API client
│   │   └── ocr.ts             # OCR text extraction
│   └── types/
│       └── index.ts           # TypeScript types
└── assets/                    # App icons and images
```

## Troubleshooting

### "Cannot connect to server"

1. Ensure the backend API is running (`python api.py`)
2. Check that your phone and Mac are on the same WiFi network
3. Verify the IP address in `api.ts` is correct
4. Try disabling any firewall temporarily

### Camera not working

1. Grant camera permission when prompted
2. On Android, go to Settings > Apps > Expo Go > Permissions

### OCR not extracting text

1. Ensure good lighting when taking photos
2. Hold the camera steady
3. Make sure the ingredient text is in focus
4. Try selecting a higher quality image from gallery

## Building for Production

To create a standalone APK for Android:

```bash
npx expo prebuild
npx expo run:android
```

Or use EAS Build for cloud builds:

```bash
npm install -g eas-cli
eas build --platform android
```
