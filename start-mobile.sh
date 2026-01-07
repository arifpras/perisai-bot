#!/bin/bash

# PerisAI Mobile App - Quick Start Script

echo "🚀 Starting PerisAI Mobile App..."
echo ""

cd "$(dirname "$0")/mobile-app" || exit

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo ""
echo "✅ Dependencies ready!"
echo ""
echo "📱 Choose an option:"
echo ""
echo "1️⃣  Web Browser (Press 'w' after starting):"
echo "   npm start"
echo ""
echo "2️⃣  Android Emulator (Press 'a' after starting):"
echo "   npm run android"
echo ""
echo "3️⃣  iOS Simulator (Press 'i' after starting - macOS only):"
echo "   npm run ios"
echo ""
echo "4️⃣  Expo Go (Scan QR with Expo Go app):"
echo "   npm start"
echo ""
echo "Starting dev server now..."
echo ""

npm start
