#!/bin/bash
# Deployment verification and troubleshooting script

echo "🔍 Checking deployment status..."
echo ""

# Check if Render deployment picked up new code
echo "1️⃣  Checking if Telegram endpoints are deployed:"
curl -s https://perisai-api.onrender.com/health && echo "✅ API is running"
echo ""

echo "2️⃣  Checking for /telegram/webhook_info endpoint:"
RESPONSE=$(curl -s -w "\n%{http_code}" https://perisai-api.onrender.com/telegram/webhook_info)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "404" ]; then
    echo "❌ TELEGRAM ENDPOINTS NOT FOUND (404)"
    echo "   This means Render is running OLD code!"
    echo ""
    echo "   🔧 FIXES TO TRY:"
    echo "   1. Go to https://dashboard.render.com"
    echo "   2. Select 'perisai-api' service"
    echo "   3. Go to 'Environment' tab"
    echo "   4. Add/verify: TELEGRAM_BOT_TOKEN = 8254110780:AAHvw4QJmaM5zzpcNOQGOjbJSdr8YYsZzdI"
    echo "   5. Click 'Save'"
    echo "   6. Go to 'Deploys' tab"
    echo "   7. Click 'Deploy latest commit' (commit 8cc8382)"
    echo "   8. Wait 2-5 minutes for deployment to complete"
    echo ""
elif [ "$HTTP_CODE" = "503" ]; then
    echo "⚠️  TELEGRAM ENDPOINTS FOUND but not configured"
    echo "   Response: $BODY"
    echo ""
    echo "   This means TELEGRAM_BOT_TOKEN is missing!"
    echo "   Add it to Render Environment and redeploy."
    echo ""
else
    echo "✅ TELEGRAM ENDPOINTS ARE WORKING!"
    echo "   Response: $BODY"
fi

echo ""
echo "3️⃣  Checking git status:"
cd /Users/arifpras/Library/CloudStorage/OneDrive-Kemenkeu/01_Kemenkeu/DJPPR_DataAnalytics/perisai-bot
git log --oneline -1
echo ""
echo "✅ Latest commit is pushed to GitHub"
echo ""
echo "📝 SUMMARY:"
echo "   If Telegram endpoints still show 404:"
echo "   - The issue is Render hasn't picked up the new code"
echo "   - Likely cause: TELEGRAM_BOT_TOKEN not set in Render"
echo "   - Solution: Set env var in Render dashboard and manual redeploy"
