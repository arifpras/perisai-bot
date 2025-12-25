# Deployment Sanity Check Guide

## Quick Start

Run the sanity check before every deployment:

```bash
python sanity_check.py
```

The script will:
- ✅ Verify all dependencies are installed
- ✅ Test FastAPI server functionality
- ✅ Validate database queries
- ✅ Test plot generation (single & multi-tenor)
- ✅ Check Telegram bot configuration
- ⚠️  Warn about missing environment variables
- ✅ Verify deployment configuration files
- ✅ Confirm data files exist

## Output

### Terminal Output
- Real-time colored output showing each check
- ✅ Green checkmarks for passed tests
- ✗ Red X marks for failures
- ⚠️  Yellow warnings for non-critical issues

### Report File
Generates `SANITY_CHECK_REPORT.txt` with:
- Timestamp of check
- Detailed results of all tests
- List of warnings and errors
- Deployment readiness status
- Pre-deployment checklist

## Exit Codes

- `0` - All checks passed, ready for deployment
- `1` - One or more critical checks failed

## Checks Performed

### 1. Dependencies
- Verifies all required Python packages installed
- Lists any missing packages

### 2. FastAPI Server
- Tests app imports
- Verifies The Economist styling loaded
- Checks uvicorn can start

### 3. Database
- Loads CSV data file
- Tests single tenor queries
- Tests multi-tenor queries
- Verifies data range and row counts

### 4. Plot Generation
- Tests single tenor plots
- Tests multi-tenor yield plots
- Tests multi-tenor price plots
- Verifies image generation

### 5. Telegram Bot
- Tests bot imports
- Verifies configuration

### 6. Environment Variables
- Checks required vars (TELEGRAM_TOKEN, API keys)
- Warns about missing vars
- Lists optional variables

### 7. Deployment Configuration
- Validates Procfile
- Validates render.yaml
- Checks requirements.txt

### 8. Data Files
- Verifies CSV files exist
- Shows file sizes

## Pre-Deployment Workflow

1. **Run sanity check:**
   ```bash
   python sanity_check.py
   ```

2. **Review report:**
   - Check `SANITY_CHECK_REPORT.txt`
   - Address any errors or warnings

3. **Set environment variables** (in Render/Heroku dashboard):
   - `TELEGRAM_TOKEN` - Your bot token from BotFather
   - `OPENAI_API_KEY` - For Kei persona
   - `PERPLEXITY_API_KEY` - For Kin persona
   - `ALLOWED_USER_IDS` (optional) - Comma-separated user IDs

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "Pre-deployment sanity check passed"
   git push origin main
   ```

5. **Deploy:**
   - Render will auto-deploy from GitHub
   - Or manually trigger deployment

6. **Post-deployment verification:**
   ```bash
   # Check health endpoint
   curl https://your-app.onrender.com/health
   
   # Send test message to bot
   /kei yield 5 year 2025
   ```

## Troubleshooting

### "Missing packages" error
```bash
pip install -r requirements.txt
```

### "CSV file not found" error
Ensure data files are committed:
```bash
git add 20251215_priceyield.csv 20251224_auction_forecast.csv
git commit -m "Add data files"
```

### Plot generation fails
Check matplotlib backend:
```bash
python -c "import matplotlib; print(matplotlib.get_backend())"
```

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run sanity check
  run: python sanity_check.py
```

Or as a pre-commit hook:

```bash
# .git/hooks/pre-push
#!/bin/bash
python sanity_check.py
exit $?
```

## Example Output

```
================================================================================
PERISAI-BOT DEPLOYMENT SANITY CHECK
================================================================================

1. CHECKING DEPENDENCIES
✅ Dependencies
   All 11 packages installed

2. CHECKING FASTAPI SERVER
✅ FastAPI imports
   FastAPI app: FastAPI
   Economist colors: 4 colors loaded

[... more checks ...]

================================================================================
DEPLOYMENT READINESS: ✅ READY
Checks Passed: 15/15
================================================================================
```
