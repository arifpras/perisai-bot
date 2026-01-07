# 📱 PerisAI Mobile App - Testing Guide

## Quick Start (Choose One Option)

### Option 1: Test on Web Browser (Easiest - 2 mins)
```bash
cd /workspaces/perisai-bot/mobile-app
npm start
# Then press 'w' to open web version
# Or visit http://localhost:8081
```

### Option 2: Test on Your Phone (Requires Expo Go App)
1. **Install Expo Go** on your phone:
   - iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

2. **Start the dev server**:
   ```bash
   cd /workspaces/perisai-bot/mobile-app
   npm start
   ```

3. **Scan QR Code** from your phone camera or Expo Go app

### Option 3: Build Native APK (Android Only - 10 mins)
```bash
cd /workspaces/perisai-bot/mobile-app

# Install EAS CLI
npm install -g eas-cli

# Build APK
eas build --platform android --local

# Download and install on phone
```

---

## What to Test

### ✅ Features Implemented
1. **Chat Interface**
   - Send messages
   - Get responses from Kei (quantitative) and Kin (narrative)
   - Persona selector (/kei, /kin, /both)

2. **Database Queries**
   - Ask for bond data
   - View tables with results
   - See charts/analytics

3. **Storage**
   - Chat history saved locally
   - Works offline (cached data)

4. **UI/UX**
   - Dark/light mode
   - Responsive design
   - Smooth animations

---

## File Structure
```
mobile-app/
├── app/                    # Navigation & screens
│   ├── (tabs)/            # Tab-based navigation
│   └── chat/              # Main chat screen
├── services/              # API & storage services
│   ├── api.ts            # FastAPI backend connection
│   └── storage.ts        # Local data storage
├── app.json               # Project config
└── package.json           # Dependencies
```

---

## Configuration

### Connect to Your Backend
Edit `services/api.ts`:
```typescript
const API_BASE_URL = 'http://YOUR_SERVER:8000';
```

Default: `http://localhost:8000` (FastAPI backend)

---

## Running Tests

```bash
# Install test dependencies
npm install --save-dev jest @testing-library/react-native

# Run tests
npm test

# Type check
npm run type-check

# Lint code
npm run lint
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 8081 already in use | `kill $(lsof -t -i :8081)` |
| Expo Go QR not working | Connect to same WiFi network |
| Black screen | Press 'r' to reload |
| TypeScript errors | Run `npm run type-check` |
| Dependencies missing | Run `npm install` |

---

## Environment Variables

Create `.env` from `.env.example`:
```bash
cp .env.example .env
```

Edit `.env`:
```
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_API_TIMEOUT=30000
```

---

## Next Steps

1. ✅ Test the web version first (no setup needed)
2. 📱 If working, test on phone with Expo Go
3. 🔧 Customize colors, fonts, API endpoints
4. 🚀 Deploy to App Store / Google Play

---

## Support

- **Expo Docs**: https://docs.expo.dev
- **React Native**: https://reactnative.dev
- **FastAPI**: http://localhost:8000/docs

Enjoy testing! 🚀
