# File Upload Handler Integration Guide

This guide explains how to integrate the file upload handlers into your existing telegram_bot.py.

## Files Created

1. **file_handlers.py** - Contains all handler functions for photos and documents
2. **file_requirements.txt** - Contains pip dependencies needed
3. **INTEGRATION_GUIDE.md** - This file

## What's Supported

### Image Files (JPG, PNG)
- Automatic OCR text extraction using Tesseract
- Send with caption: `/kei analyze this chart` or `/kin what's in this image`
- Extracts text and sends to specified persona

### PDF Files
- Text extraction from all pages
- Send with caption: `/kei summarize this report`
- Combines document content with your question

### Excel Spreadsheets (.xlsx, .xls)
- Extracts data from all sheets
- Formatted as pipe-separated tables
- Send with caption: `/kei analyze this data`

### Text Files (.txt)
- Direct reading and processing
- Send with caption: `/kin review this text`

## Installation Steps

### Step 1: Install Dependencies

```bash
pip install -r file_requirements.txt
```

**Note:** Also need to install system dependency for OCR:
```bash
# On Ubuntu/Debian
sudo apt-get install tesseract-ocr

# On macOS
brew install tesseract

# On Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Step 2: Add File to Project

The `file_handlers.py` file should be in the same directory as `telegram_bot.py`.

### Step 3: Update telegram_bot.py

#### 3a. Add import at the top:
```python
from file_handlers import handle_photo, handle_document
```

#### 3b. Update `create_telegram_app()` function:

Find this section:
```python
def create_telegram_app(token: str) -> Application:
    """Create and configure the Telegram application with extended HTTPX timeouts."""
    from telegram.request import HTTPXRequest
    
    request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=30.0,
        write_timeout=10.0,
        pool_timeout=15.0
    )
    
    application = Application.builder().token(token).request(request).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("examples", examples_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("activity", activity_command))
    # Personas
    application.add_handler(CommandHandler("kei", kei_command))
    application.add_handler(CommandHandler("kin", kin_command))
    application.add_handler(CommandHandler("both", both_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application
```

Add these two lines before `return application`:
```python
    # File upload handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    return application
```

Full updated section:
```python
def create_telegram_app(token: str) -> Application:
    """Create and configure the Telegram application with extended HTTPX timeouts."""
    from telegram.request import HTTPXRequest
    
    request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=30.0,
        write_timeout=10.0,
        pool_timeout=15.0
    )
    
    application = Application.builder().token(token).request(request).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("examples", examples_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("activity", activity_command))
    # Personas
    application.add_handler(CommandHandler("kei", kei_command))
    application.add_handler(CommandHandler("kin", kin_command))
    application.add_handler(CommandHandler("both", both_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # File upload handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    return application
```

## Usage Examples

### Image Analysis
1. User sends an image with caption: `/kei analyze this bond chart`
2. Bot extracts text via OCR
3. Sends extracted text + question to Kei persona
4. Returns analysis

### Document Summary
1. User sends PDF with caption: `/kin summarize this report`
2. Bot extracts all text from PDF
3. Sends document + question to Kin persona
4. Returns summary

### Data Analysis
1. User sends Excel file with caption: `/kei analyze this auction data`
2. Bot extracts sheet data as formatted text
3. Sends to Kei for analysis
4. Returns insights

## Configuration Options

Edit these in `file_handlers.py`:

```python
MAX_FILE_SIZE_MB = 10  # Maximum file size in MB
MAX_TEXT_LENGTH = 8000  # Maximum characters to send to LLM
```

## Graceful Degradation

If dependencies aren't installed:
- OCR unavailable → Bot tells user "OCR not available"
- PDF support unavailable → Bot tells user "PDF support not installed"
- Excel support unavailable → Bot tells user "Excel support not installed"

The bot continues working without crashing.

## Troubleshooting

### "pytesseract not found" error
Install: `pip install pytesseract` and system tesseract-ocr

### "No module named 'PyPDF2'"
Install: `pip install PyPDF2`

### "No module named 'openpyxl'"
Install: `pip install openpyxl`

### OCR returns empty text
- Tesseract not installed on system
- Image has no readable text
- Image quality too poor

### File size error
- Check MAX_FILE_SIZE_MB setting
- Default limit is 10MB

## Features

✅ Automatic authorization checking (uses existing `is_user_authorized()`)
✅ Metrics logging (integrates with existing `metrics.log_query()`)
✅ Typing indicators while processing
✅ Error handling with user-friendly messages
✅ HTML/Markdown formatting fallback
✅ Text truncation to respect LLM context limits
✅ Per-file-type specialized handlers
✅ Graceful degradation if dependencies missing

## Notes

- Extracted text is truncated to 8000 chars to avoid LLM context overflow
- Files > 10MB are rejected automatically
- All operations are async and non-blocking
- Metrics are automatically logged if metrics module available
- Persona routing via caption prefix: `/kei` or `/kin`
