# PDF Dataset Integration for Kei Analysis

Convert multiple PDFs from a folder into a knowledge base that Kei can use for contextual analysis.

## Overview

When you have a collection of PDFs (reports, market analysis, policy documents, etc.), this module:
1. ✅ Extracts text from all PDFs in a folder
2. ✅ Stores them in a searchable knowledge base
3. ✅ Automatically injects relevant excerpts into Kei's prompts
4. ✅ Caches extracted text to avoid re-processing

## Use Cases

- **Market Research**: Ingest reports, whitepapers, market analyses
- **Policy Documents**: Load BI policy papers, market regulations
- **Historical Analysis**: Store bond market studies, auction retrospectives
- **Custom Knowledge**: Add domain-specific documents for Kei's context

## Installation

The module requires PyPDF2 (already in requirements.txt). If not installed:

```bash
pip install PyPDF2
```

## Quick Start

### Method 1: Command Line

```bash
# Ingest all PDFs from a folder
python pdf_dataset_ingestion.py --folder /path/to/pdfs --category reports

# With page limits (extract only first 50 pages per PDF)
python pdf_dataset_ingestion.py --folder /path/to/pdfs --max-pages 50

# List all ingested documents
python pdf_dataset_ingestion.py --list
```

### Method 2: Python Script

```python
from pdf_dataset_ingestion import PDFDatasetBuilder

# Create builder
builder = PDFDatasetBuilder(kb_dir="knowledge_base")

# Ingest folder
result = builder.ingest_folder(
    folder_path="/path/to/pdfs",
    category="market_research",
    max_pages_per_file=100,
    exclude_small_files=True
)

print(f"Processed: {result['statistics']['processed']} files")
print(f"Total chars: {result['statistics']['total_chars']:,}")
```

### Method 3: Telegram Command

(See `/pdf` command integration below)

## Features

### Automatic Text Extraction

- Extracts text from all pages of PDF files
- Handles corrupted/scanned PDFs gracefully (with warnings)
- Page markers included (`[Page 1]`, `[Page 2]`, etc.)
- Optional page limit to prevent huge documents

### Intelligent Caching

- Caches extracted text in `.pdf_cache.json`
- Detects file changes (size + modification time)
- Skips re-processing unchanged files
- Manually clear cache if needed

### Knowledge Base Organization

Files stored in `knowledge_base/<category>/` structure:

```
knowledge_base/
├── market_research/
│   ├── bond_market_2024.txt
│   ├── auction_analysis.txt
│   └── policy_outlook.txt
├── reports/
│   ├── annual_report.txt
│   └── quarterly_summary.txt
└── .pdf_cache.json
```

### Statistics Tracking

```python
# Example output
{
  'status': 'success',
  'statistics': {
    'total_files': 5,
    'processed': 5,
    'skipped': 0,
    'failed': 0,
    'total_pages': 342,
    'total_chars': 1250000
  }
}
```

## Kei Integration

### Automatic Context Injection

When Kei processes a query, relevant PDF content is automatically injected:

```python
from pdf_dataset_ingestion import KeiPDFAnalyzer

analyzer = KeiPDFAnalyzer(kb_dir="knowledge_base")

# Get context for a query
context = analyzer.get_pdf_context(
    query="What are the auction trends?",
    top_k=3
)

# Enhance Kei's prompt
enhanced_prompt = analyzer.enhance_prompt(
    query="Analyze bond market trends",
    system_prompt=original_system_prompt
)
```

### In telegram_bot.py

Modify the `kei_command` function to use PDF context:

```python
# Add at top of file
from pdf_dataset_ingestion import KeiPDFAnalyzer

# In kei_command function, before sending query to LLM:
pdf_analyzer = KeiPDFAnalyzer()
context = pdf_analyzer.get_pdf_context(question, top_k=2)
if context:
    # Enhanced prompt with PDF context
    enhanced_system_prompt = system_prompt + "\n\n" + context
else:
    enhanced_system_prompt = system_prompt

# Then send enhanced_system_prompt to OpenAI API
```

## Telegram Command: /pdf

Add this command handler to telegram_bot.py:

```python
async def pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pdf <command> [args] — manage PDF knowledge base."""
    user_id = update.message.from_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Access denied")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage:\n"
            "/pdf ingest /path/to/pdfs [category] - Load PDFs from folder\n"
            "/pdf list - Show ingested documents\n"
            "/pdf clear <category> - Delete category\n"
            "/pdf summary - Show knowledge base summary"
        )
        return
    
    command = args[0].lower()
    
    if command == "ingest":
        if len(args) < 2:
            await update.message.reply_text("Usage: /pdf ingest /path/to/pdfs [category]")
            return
        
        folder_path = args[1]
        category = args[2] if len(args) > 2 else "documents"
        
        await update.message.reply_text(f"📂 Ingesting PDFs from {folder_path}...")
        
        try:
            builder = PDFDatasetBuilder()
            result = builder.ingest_folder(folder_path, category=category)
            
            if 'error' in result:
                await update.message.reply_text(f"❌ Error: {result['error']}")
            else:
                stats = result['statistics']
                msg = (
                    f"✅ Ingestion Complete\n\n"
                    f"📊 Statistics:\n"
                    f"  • Processed: {stats['processed']} files\n"
                    f"  • Failed: {stats['failed']} files\n"
                    f"  • Pages: {stats['total_pages']}\n"
                    f"  • Total: {stats['total_chars']:,} chars\n"
                    f"  • Category: {category}\n\n"
                    f"Knowledge base ready for Kei's analysis!"
                )
                await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    elif command == "list":
        try:
            builder = PDFDatasetBuilder()
            docs = builder.list_ingested_documents()
            
            if not docs:
                await update.message.reply_text("📭 No documents ingested yet")
                return
            
            msg_lines = ["📚 Ingested Documents:\n"]
            for category, files in docs.items():
                msg_lines.append(f"📂 {category}")
                for file_info in files:
                    msg_lines.append(
                        f"  • {file_info['filename']} ({file_info['size_kb']:.1f} KB)"
                    )
            
            await update.message.reply_text("\n".join(msg_lines))
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    elif command == "summary":
        try:
            analyzer = KeiPDFAnalyzer()
            summary = analyzer.get_knowledge_summary()
            
            msg_lines = ["📖 Knowledge Base Summary:\n"]
            msg_lines.append(f"Total documents: {summary['total_documents']}")
            for category, files in summary['categories'].items():
                msg_lines.append(f"\n📂 {category}: {len(files)} files")
            
            await update.message.reply_text("\n".join(msg_lines))
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    elif command == "clear":
        if len(args) < 2:
            await update.message.reply_text("Usage: /pdf clear <category>")
            return
        
        category = args[1]
        builder = PDFDatasetBuilder()
        if builder.clear_category(category):
            await update.message.reply_text(f"✅ Cleared category: {category}")
        else:
            await update.message.reply_text(f"❌ Failed to clear category: {category}")
    
    else:
        await update.message.reply_text(f"Unknown command: {command}")
```

Then register in `create_telegram_app()`:

```python
application.add_handler(CommandHandler("pdf", pdf_command))
```

## API Reference

### PDFDatasetBuilder

```python
from pdf_dataset_ingestion import PDFDatasetBuilder

builder = PDFDatasetBuilder(kb_dir="knowledge_base", enable_caching=True)

# Ingest entire folder
result = builder.ingest_folder(
    folder_path="/path/to/pdfs",
    category="documents",
    max_pages_per_file=None,      # None = all pages
    exclude_small_files=True       # Skip files < 1KB
)

# Ingest single file
result = builder.ingest_single_pdf(
    pdf_path="/path/to/file.pdf",
    category="documents"
)

# List all documents
docs = builder.list_ingested_documents()

# Clear a category
builder.clear_category("documents")

# Check stats
print(builder.stats)
```

### KeiPDFAnalyzer

```python
from pdf_dataset_ingestion import KeiPDFAnalyzer

analyzer = KeiPDFAnalyzer(kb_dir="knowledge_base")

# Get context for query
context = analyzer.get_pdf_context(
    query="bond market trends",
    top_k=3
)

# Enhance prompt
enhanced = analyzer.enhance_prompt(
    query="analyze auction demand",
    system_prompt="You are Kei..."
)

# Summary
summary = analyzer.get_knowledge_summary()
```

## Example Workflow

### 1. Prepare PDFs

```
/home/user/market_docs/
├── bond_analysis_2024.pdf
├── auction_trends_q4.pdf
├── policy_outlook.pdf
└── regulatory_framework.pdf
```

### 2. Ingest via Command Line

```bash
python pdf_dataset_ingestion.py --folder /home/user/market_docs --category market_analysis
```

Output:
```
============================================================
INGESTION SUMMARY
============================================================
Total files: 4
Processed: 4
Skipped (cached): 0
Failed: 0
Total pages: 287
Total chars: 892,345
Knowledge base: knowledge_base/market_analysis
```

### 3. Query Kei with PDF Context

```
User: /kei what are the upcoming auction trends based on the market analysis?

Kei's prompt now includes:
📚 **Relevant Knowledge Base Context:**

[Source 1: auction_trends_q4.txt (market_analysis)]
[Page 1]
Q4 2025 Auction Analysis:
- Demand indicators suggest strong institutional interest
- Yield curves expected to steepen in 2026...
```

## Performance Considerations

### File Size Limits

- **Small files** (< 1MB): Processed instantly
- **Medium files** (1-10MB): ~1-2 seconds per file
- **Large files** (> 10MB): ~5-10 seconds, consider page limits

### Page Limits

For faster processing of large documents:

```python
# Only extract first 50 pages per PDF
builder.ingest_folder(
    "/path/to/pdfs",
    max_pages_per_file=50
)
```

### Cache Strategy

- Cache hits: < 100ms (no re-processing)
- Cache misses: Depends on file size
- Cache persists across bot restarts
- Invalidated if file size or modification time changes

## Troubleshooting

### "No text extracted from PDF"

The PDF may contain only images/scans. Solutions:
1. Use OCR before ingestion (preprocess PDFs)
2. Convert PDF to text manually
3. Re-save PDF in text-based format

### "Access denied" on folder

Check directory permissions:
```bash
chmod -R 755 /path/to/pdfs
```

### Cache inconsistencies

Clear cache manually:
```bash
rm knowledge_base/.pdf_cache.json
```

Or rebuild programmatically:
```python
builder.cache = {}
builder._save_cache()
result = builder.ingest_folder("/path/to/pdfs")
```

### Memory issues with huge PDFs

Use page limits:
```bash
python pdf_dataset_ingestion.py --folder /path --max-pages 100
```

## Best Practices

1. **Organize by category**: Group related documents
   ```bash
   python pdf_dataset_ingestion.py --folder research/ --category "market_research"
   python pdf_dataset_ingestion.py --folder policy/ --category "policy_documents"
   ```

2. **Limit large PDFs**: Set max pages for processing speed
   ```bash
   python pdf_dataset_ingestion.py --folder research/ --max-pages 50
   ```

3. **Monitor knowledge base size**: Remove old/unused categories
   ```bash
   python pdf_dataset_ingestion.py --list  # Check size
   # Then delete if needed
   ```

4. **Keep PDFs updated**: Re-ingest when new PDFs are added
   - Cache detects changes automatically
   - Modified files re-processed
   - Unchanged files skip processing

5. **Use descriptive filenames**: Better context in searches
   - ✅ `bond_market_analysis_q4_2025.pdf`
   - ❌ `document.pdf`

## Advanced: Custom Search Ranking

For fine-tuned context retrieval, modify search scores in `rag_system.py`:

```python
# In KnowledgeBase.search():
score = (jaccard * 0.6) + (exact_matches / len(query_terms) * 0.4)
# Adjust weights for your use case
```

## Limitations

- ✅ Supports PDF text extraction only (not images/scans)
- ✅ Context limited to top-K matching documents
- ✅ Keyword-based search (not semantic/embedding-based)
- 🔄 Future: Vector embeddings for semantic search

## Future Enhancements

- [ ] OCR support for scanned PDFs
- [ ] Semantic search using embeddings (OpenAI, Hugging Face)
- [ ] Multi-language support
- [ ] Table extraction and structured data
- [ ] Document versioning and diff tracking
- [ ] Web scraping integration
- [ ] Automatic document summarization
