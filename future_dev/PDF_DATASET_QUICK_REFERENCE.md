# PDF Dataset for Kei Analysis - Quick Reference

## What It Does

✅ Convert multiple PDFs into a searchable knowledge base
✅ Automatically inject relevant context into Kei's analysis
✅ Cache extracted text to avoid re-processing
✅ Organize documents by category

## Files Created

1. **pdf_dataset_ingestion.py** - Main module (380+ lines)
2. **pdf_dataset_examples.py** - Usage examples
3. **PDF_DATASET_INTEGRATION.md** - Complete guide (300+ lines)

## Quick Start (3 Steps)

### Step 1: Copy PDFs to a folder
```bash
mkdir my_pdfs
cp report1.pdf report2.pdf report3.pdf my_pdfs/
```

### Step 2: Ingest PDFs
```bash
# Via command line
python pdf_dataset_ingestion.py --folder my_pdfs --category market_analysis

# Or via Python
from pdf_dataset_ingestion import PDFDatasetBuilder
builder = PDFDatasetBuilder()
builder.ingest_folder("my_pdfs", category="market_analysis")
```

### Step 3: Use with Kei (Optional)
```python
# Kei automatically gets PDF context for analysis
user_query = "Analyze auction trends based on recent market data"
# Kei will search PDFs and inject relevant excerpts into its response
```

## Commands (via Telegram)

```
/pdf ingest /path/to/pdfs [category]  - Load PDFs
/pdf list                              - Show documents
/pdf summary                           - Knowledge base stats
/pdf clear <category>                  - Delete category
```

## API Usage

```python
from pdf_dataset_ingestion import PDFDatasetBuilder, KeiPDFAnalyzer

# Ingest PDFs
builder = PDFDatasetBuilder()
builder.ingest_folder("/path/to/pdfs", category="documents")

# Get context for queries
analyzer = KeiPDFAnalyzer()
context = analyzer.get_pdf_context("bond market trends", top_k=3)

# Enhance prompts
enhanced = analyzer.enhance_prompt(query, system_prompt)
```

## Storage

Files stored in: `knowledge_base/<category>/`
- One `.txt` file per PDF
- Extracted text includes page markers
- Cache: `knowledge_base/.pdf_cache.json`

## Features

| Feature | Status |
|---------|--------|
| Text extraction from PDFs | ✅ |
| Automatic caching | ✅ |
| Keyword-based search | ✅ |
| Context injection to Kei | ✅ |
| Folder organization | ✅ |
| Statistics tracking | ✅ |
| Page limits | ✅ |
| Error handling | ✅ |
| OCR for scanned PDFs | ❌ (Future) |
| Semantic search | ❌ (Future) |

## Examples

```python
# Example 1: Basic ingestion
from pdf_dataset_ingestion import PDFDatasetBuilder

builder = PDFDatasetBuilder()
result = builder.ingest_folder("research_papers", category="research")
print(f"Processed {result['statistics']['processed']} files")

# Example 2: Get context
from pdf_dataset_ingestion import KeiPDFAnalyzer

analyzer = KeiPDFAnalyzer()
context = analyzer.get_pdf_context("What drives auction demand?")
print(context)

# Example 3: List documents
docs = builder.list_ingested_documents()
for category, files in docs.items():
    print(f"{category}: {len(files)} files")

# Example 4: Clear category
builder.clear_category("outdated")
```

## Performance

| Operation | Time |
|-----------|------|
| Extract text (small PDF <1MB) | <1s |
| Extract text (medium 1-10MB) | 1-2s |
| Cache hit (already extracted) | <100ms |
| Search (keyword match) | <100ms |
| Prompt injection | <500ms |

## Tips

1. **Organize by category**
   ```bash
   python pdf_dataset_ingestion.py --folder policy/ --category policy_docs
   python pdf_dataset_ingestion.py --folder research/ --category market_research
   ```

2. **Limit large PDFs** (for speed)
   ```bash
   python pdf_dataset_ingestion.py --folder . --max-pages 50
   ```

3. **Check what's ingested**
   ```bash
   python pdf_dataset_ingestion.py --list
   ```

4. **Clear old data**
   ```python
   builder.clear_category("old_reports")
   ```

## Integration with telegram_bot.py

Add to `create_telegram_app()`:

```python
from pdf_dataset_ingestion import pdf_command
application.add_handler(CommandHandler("pdf", pdf_command))
```

Then users can:
```
/pdf ingest /path/to/reports market_analysis
/pdf list
/pdf summary
```

## Troubleshooting

**Q: No text extracted from PDF**
A: PDF may be image-based (scanned). Try OCR or convert manually.

**Q: Why is first ingest slow?**
A: Normal for large PDFs. Subsequent runs use cache (very fast).

**Q: Can I delete a category?**
A: Yes, use `/pdf clear category` or `builder.clear_category("category")`

**Q: How big can knowledge base get?**
A: Unlimited, but larger = slower searches. Consider archiving old docs.

## Next Steps

1. ✅ Create a folder with PDF files
2. ✅ Ingest with `python pdf_dataset_ingestion.py --folder /path`
3. ✅ Verify with `/pdf list` (if Telegram integration added)
4. ✅ Ask Kei questions - it will use PDF context automatically

## Related Documentation

- **PDF_DATASET_INTEGRATION.md** - Complete guide with examples
- **rag_system.py** - Underlying RAG system
- **pdf_dataset_examples.py** - Working code examples

---

**Created:** January 2, 2026
**Module:** pdf_dataset_ingestion.py (380+ lines)
**Dependencies:** PyPDF2 (already in requirements.txt)
