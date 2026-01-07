# Deploy to Render - Phone Testing Setup

## 🚀 Deployment Steps

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Deploy mobile app and API to Render"
git push origin main
```

### Step 2: Connect Render to Your Repository
1. Go to [render.com](https://render.com)
2. Sign in (or create account)
3. Click **"New +"** → **"Web Service"**
4. Select **"Deploy from Git"**
5. Connect your GitHub account and select this repository
6. Click **"Deploy"**

### Step 3: Configure Environment Variables (if needed)
In Render dashboard, add these if you have them:
- `TELEGRAM_BOT_TOKEN` (optional)
- `OPENAI_API_KEY` (optional, for LLM features)
- `PERPLEXITY_API_KEY` (optional)

### Step 4: Get Your Public URLs
After deployment completes, you'll have:
- **API**: `https://perisai-api.onrender.com`
- **Web App**: `https://perisai-mobile-web.onrender.com`

---

## 📱 Access on Your Phone

Once deployed, open your phone's browser and visit:
```
https://perisai-mobile-web.onrender.com
```

The app will:
1. Load on your phone
2. Connect to the API at `https://perisai-api.onrender.com`
3. Send/receive bond analytics queries in real-time

---

## 🧪 Test Queries
Try these on your phone:
- "average yield 10 year Q1 2025"
- "5 year bond price 2025"
- "price yield comparison 10 year"

---

## ⚠️ Notes
- **First load may be slow** - Render's free tier spins down inactive services
- **Public URL**: Anyone can access your app (for demo purposes)
- **Upgrade**: For production, consider Render's paid plans for faster performance
- **Custom Domain**: You can add a custom domain in Render settings

---

## 🔗 Useful Links
- Render Dashboard: https://dashboard.render.com
- API Endpoint: https://perisai-api.onrender.com/docs
- Mobile App: https://perisai-mobile-web.onrender.com

---

**Status**: ✅ Ready to deploy
**Last Updated**: January 7, 2026
