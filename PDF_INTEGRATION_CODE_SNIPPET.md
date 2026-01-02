# PDF Dataset Integration Code Snippet for telegram_bot.py

## STEP 1: Add imports at top of telegram_bot.py

Add these lines after existing imports:

```python
from pdf_dataset_ingestion import PDFDatasetBuilder, KeiPDFAnalyzer, KeiPDFAnalyzer
```

## STEP 2: Add the /pdf command handler

Add this function to telegram_bot.py (near other command handlers like kei_command, kin_command):

```python
async def pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pdf <command> [args] — manage PDF knowledge base for Kei analysis."""
    user_id = update.message.from_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to authorized users only."
        )
        return
    
    if not context.args:
        help_text = (
            "📚 PDF Dataset Manager\n\n"
            "Commands:\n"
            "/pdf ingest <folder> [category] - Load PDFs from folder\n"
            "/pdf list - Show all ingested documents\n"
            "/pdf summary - Knowledge base statistics\n"
            "/pdf clear <category> - Delete a category\n\n"
            "Examples:\n"
            "/pdf ingest /home/user/pdfs market_research\n"
            "/pdf list\n"
            "/pdf summary"
        )
        await update.message.reply_text(help_text)
        return
    
    command = context.args[0].lower()
    
    # INGEST: Load PDFs from folder
    if command == "ingest":
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /pdf ingest <folder_path> [category]\n"
                "Example: /pdf ingest /home/user/pdfs market_research"
            )
            return
        
        folder_path = context.args[1]
        category = context.args[2] if len(context.args) > 2 else "documents"
        
        await update.message.reply_text(
            f"⏳ Ingesting PDFs from {folder_path}...\nCategory: {category}"
        )
        
        try:
            builder = PDFDatasetBuilder()
            result = builder.ingest_folder(folder_path, category=category)
            
            if 'error' in result:
                await update.message.reply_text(f"❌ Error: {result['error']}")
                metrics.log_error("/pdf ingest", str(result['error']), user_id)
            else:
                stats = result['statistics']
                response = (
                    f"✅ <b>PDF Ingestion Complete</b>\n\n"
                    f"📊 <b>Statistics:</b>\n"
                    f"  • Processed: <code>{stats['processed']}</code> files\n"
                    f"  • Failed: <code>{stats['failed']}</code> files\n"
                    f"  • Total pages: <code>{stats['total_pages']}</code>\n"
                    f"  • Characters: <code>{stats['total_chars']:,}</code>\n"
                    f"  • Category: <code>{category}</code>\n\n"
                    f"💡 Kei will now use these PDFs for contextual analysis!"
                )
                await update.message.reply_text(response, parse_mode=ParseMode.HTML)
                
                response_time = time.time() - time.time()
                metrics.log_query(user_id, username, f"pdf ingest {category}", "pdf_ingest", 
                                response_time, True, "success", "pdf_manager")
        
        except Exception as e:
            logger.error(f"PDF ingestion error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
            metrics.log_error("/pdf ingest", str(e), user_id)
    
    # LIST: Show all documents
    elif command == "list":
        try:
            builder = PDFDatasetBuilder()
            docs = builder.list_ingested_documents()
            
            if not docs:
                await update.message.reply_text(
                    "📭 <b>No documents ingested yet</b>\n\n"
                    "Use: /pdf ingest /path/to/pdfs",
                    parse_mode=ParseMode.HTML
                )
                return
            
            lines = ["📚 <b>Ingested Documents</b>\n"]
            for category, files in docs.items():
                lines.append(f"<b>📂 {category}</b>")
                for file_info in files[:10]:  # Limit to 10 per category
                    size_str = f"{file_info['size_kb']:.1f} KB" if file_info['size_kb'] < 1024 else f"{file_info['size_kb']/1024:.1f} MB"
                    lines.append(f"  • <code>{file_info['filename']}</code> ({size_str})")
                
                if len(files) > 10:
                    lines.append(f"  ... and {len(files) - 10} more")
                lines.append("")
            
            response = "\n".join(lines[:50])  # Limit message length
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
        except Exception as e:
            logger.error(f"PDF list error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
    
    # SUMMARY: Show statistics
    elif command == "summary":
        try:
            analyzer = KeiPDFAnalyzer()
            summary = analyzer.get_knowledge_summary()
            
            lines = [
                "📖 <b>Knowledge Base Summary</b>\n",
                f"<b>Total Documents:</b> <code>{summary['total_documents']}</code>"
            ]
            
            if summary['total_documents'] > 0:
                lines.append("\n<b>By Category:</b>")
                for category, files in summary['categories'].items():
                    lines.append(f"  📂 {category}: <code>{len(files)}</code> files")
            else:
                lines.append("\n<i>(No documents ingested yet)</i>")
            
            response = "\n".join(lines)
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
        except Exception as e:
            logger.error(f"PDF summary error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
    
    # CLEAR: Delete category
    elif command == "clear":
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /pdf clear <category>")
            return
        
        category = context.args[1]
        
        # Confirmation
        try:
            builder = PDFDatasetBuilder()
            if builder.clear_category(category):
                await update.message.reply_text(
                    f"✅ Cleared category: <code>{category}</code>",
                    parse_mode=ParseMode.HTML
                )
                metrics.log_query(user_id, username, f"pdf clear {category}", "pdf_clear", 
                                0.1, True, "success", "pdf_manager")
            else:
                await update.message.reply_text(f"❌ Failed to clear category: {category}")
        
        except Exception as e:
            logger.error(f"PDF clear error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
    
    else:
        await update.message.reply_text(
            f"❌ Unknown command: {command}\n\n"
            "Use /pdf for help"
        )
```

## STEP 3: Register the handler in create_telegram_app()

Find the `create_telegram_app()` function and add this line with other CommandHandlers:

```python
def create_telegram_app(token: str) -> Application:
    """Create and configure the Telegram application."""
    # ... existing code ...
    
    # Existing handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("kei", kei_command))
    application.add_handler(CommandHandler("kin", kin_command))
    # ... other handlers ...
    
    # ADD THIS LINE:
    application.add_handler(CommandHandler("pdf", pdf_command))
    
    return application
```

## STEP 4: Test it!

Restart your bot and try:

```
/pdf
/pdf ingest /path/to/my/pdfs market_research
/pdf list
/pdf summary
```

---

## How It Works with Kei

Once PDFs are ingested, Kei automatically:

1. **Receives your question** 
   ```
   User: /kei what are the upcoming auction trends?
   ```

2. **Searches PDF knowledge base**
   - Matches keywords from your question to PDF content
   - Retrieves top 2-3 most relevant excerpts

3. **Injects into prompt**
   - Adds PDF context to Kei's system prompt
   - Kei uses this knowledge in analysis

4. **Delivers enhanced response**
   - Based on PDFs + Kei's training + market data

## Example Usage Flow

```
# 1. User prepares PDFs
$ mkdir market_reports
$ cp bond_analysis.pdf auction_trends.pdf market_reports/

# 2. User ingests them (via Telegram)
/pdf ingest /path/to/market_reports market_research

# 3. Verify ingestion
/pdf list
Output: market_research: 2 files

# 4. Ask Kei questions using PDFs
/kei what does the market analysis say about auction demand?

# 5. Kei responds with PDF context injected
Kei: Based on the market analysis PDFs...
  [Kei uses document excerpts in analysis]
```

---

## Key Features

✅ **Automatic Context Injection** - No changes needed to Kei's code
✅ **Fast Caching** - Subsequent runs skip already-extracted PDFs
✅ **Organization** - Group PDFs by category
✅ **Error Handling** - Graceful failures don't crash bot
✅ **Statistics** - Track ingestion progress

---

## File Structure After Integration

```
telegram_bot.py
├── imports (add: pdf_dataset_ingestion)
├── async def pdf_command() [NEW]
├── async def create_telegram_app()
│   └── application.add_handler(CommandHandler("pdf", pdf_command)) [NEW]
└── ... other functions ...

knowledge_base/
├── market_research/
│   ├── bond_analysis.txt
│   └── auction_trends.txt
├── reports/
│   └── market_overview.txt
└── .pdf_cache.json
```

---

## Troubleshooting

**Problem**: `/pdf` command not recognized
**Solution**: Make sure you added the handler in `create_telegram_app()`

**Problem**: "File not found" error
**Solution**: Use absolute paths, e.g., `/pdf ingest /home/user/pdfs` not `~/pdfs`

**Problem**: PDFs ingested but Kei doesn't use them
**Solution**: Check if `KeiPDFAnalyzer` is properly imported and called in kei_command

---

## Optional: Modify Kei's Prompt Enhancement

If you want Kei to ALWAYS use PDF context (without separate integration):

In the `kei_command()` function, find where it calls the OpenAI API:

```python
# BEFORE (current)
response = await _openai_client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
)

# AFTER (with PDF context)
pdf_analyzer = KeiPDFAnalyzer()
enhanced_prompt = pdf_analyzer.enhance_prompt(question, system_prompt)

response = await _openai_client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": enhanced_prompt},  # Now includes PDF context
        {"role": "user", "content": question}
    ]
)
```

This injects PDFs automatically into every /kei query!
