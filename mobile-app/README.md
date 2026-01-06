# Perisai Bond Bot - Mobile App

React Native mobile application for Indonesian government bond analysis with dual personas (Kei & Kin).

## Features

- 📊 **Real-time Bond Data**: Query yields, prices, and auction forecasts
- 👥 **Dual Personas**: 
  - Kei: Quantitative analyst (tables, statistics)
  - Kin: Strategic interpreter (plots, macro context)
- 📈 **Professional Charts**: Economist-style visualizations
- 💾 **Offline Mode**: Cache recent queries and results
- 🔔 **Push Notifications**: Auction alerts and yield threshold notifications
- 🌙 **Dark Mode**: Easy on the eyes

## Prerequisites

- Node.js 18+
- npm or yarn
- Expo CLI: `npm install -g expo-cli`
- For iOS: Mac with Xcode
- For Android: Android Studio

## Quick Start

```bash
# Install dependencies
cd mobile-app
npm install

# Start development server
npx expo start

# Run on iOS simulator
npx expo start --ios

# Run on Android emulator
npx expo start --android

# Run on physical device
# Scan QR code with Expo Go app
```

## Project Structure

```
mobile-app/
├── app/                    # Expo Router navigation
│   ├── (tabs)/            # Tab navigation
│   │   ├── chat.tsx       # Chat interface
│   │   ├── history.tsx    # Query history
│   │   └── settings.tsx   # App settings
│   ├── _layout.tsx        # Root layout
│   └── index.tsx          # Entry point
├── components/            # Reusable components
│   ├── Message.tsx        # Chat message bubble
│   ├── Chart.tsx          # Bond charts
│   ├── Table.tsx          # Data tables
│   └── PersonaSelector.tsx # Kei/Kin selector
├── services/              # API & storage
│   ├── api.ts             # FastAPI client
│   └── storage.ts         # AsyncStorage wrapper
├── store/                 # Redux state management
│   ├── chatSlice.ts       # Chat state
│   └── personaSlice.ts    # Persona selection
├── types/                 # TypeScript definitions
│   └── index.ts           # Shared types
├── utils/                 # Helper functions
│   ├── formatter.ts       # Data formatting
│   └── theme.ts           # App theme
├── app.json              # Expo configuration
├── package.json          # Dependencies
└── tsconfig.json         # TypeScript config
```

## Environment Variables

Create a `.env` file:

```env
EXPO_PUBLIC_API_URL=https://perisai-api.onrender.com
EXPO_PUBLIC_WS_URL=wss://perisai-api.onrender.com/ws
```

## Building for Production

### iOS

```bash
# Build for iOS (requires Mac)
eas build --platform ios

# Submit to App Store
eas submit --platform ios
```

### Android

```bash
# Build for Android
eas build --platform android

# Submit to Google Play
eas submit --platform android
```

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run linter
npm run lint

# Type check
npm run type-check
```

## Tech Stack

- **Framework**: React Native with Expo
- **Language**: TypeScript
- **Navigation**: Expo Router
- **State**: Redux Toolkit
- **UI**: React Native Paper (Material Design)
- **Charts**: Victory Native
- **Storage**: AsyncStorage + SQLite
- **API**: Axios

## Contributing

1. Create feature branch
2. Make changes
3. Run tests and linter
4. Submit PR

## License

MIT
