# Phone Testing Setup - Network Configuration

## Problem
Your phone is on a different network than the dev container (172.17.0.2 is internal). The phone can't reach internal IPs.

## Solutions (In Order of Ease)

### Solution 1: Use GitHub Codespaces Port Forwarding (EASIEST) ✅
If you're using GitHub Codespaces:

1. In VS Code, go to **Ports** tab (bottom panel)
2. **Forward these ports**:
   - Port **8000** (FastAPI) → Set to Public
   - Port **8083** (Expo) → Set to Public
3. Copy the forwarded URLs (should look like `https://yourname-xyz.github.dev`)
4. Update `mobile-app/app.json` with your forwarded URL

### Solution 2: Use Localhost with Port Forwarding
If Codespaces port forwarding is enabled:
- Expo: `http://localhost:8083`
- API: `http://localhost:8000`
- Phone should use the public Codespaces URL

### Solution 3: Use Network IP (If on Same WiFi)
If your phone is on the same WiFi as your development machine:

1. Find your machine's IP: `ipconfig getifaddr en0` (Mac) or `hostname -I` (Linux)
2. Update `mobile-app/app.json` with that IP
3. Restart Expo

### Solution 4: Use ngrok Tunnel (More Complex)
1. Install ngrok: `npm install -g ngrok`
2. Expose backend: `ngrok http 8000`
3. Get the public URL and update `app.json`
4. Use Expo tunnel mode

## Current Configuration
- **Expo Server**: Port 8083 (LAN mode)
- **FastAPI Backend**: Port 8000
- **Container IP**: 172.17.0.2 (internal only)

## Try This Now (For Codespaces)
1. Enable port forwarding for ports 8000 and 8083
2. Get the public URLs from the Ports tab
3. Scan the new QR code or use the public Expo URL on your phone

---
**Last Updated**: January 7, 2026
