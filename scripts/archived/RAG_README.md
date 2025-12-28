# RAG Implementation for Perisai Bot

## Overview

**Retrieval-Augmented Generation (RAG)** enables the bot to inject custom knowledge into persona prompts. Instead of relying solely on pre-trained model knowledge, RAG allows you to build a knowledge base that gets automatically retrieved and injected into prompts when relevant.

## What is RAG?

```
User Query
    ↓
[Search Knowledge Base] ← RAG System
    ↓
[Retrieve Relevant Docs]
    ↓
[Enhance System Prompt with Context]
    ↓
[Send to LLM (Kei/Kin)]
    ↓
[Return Enhanced Response]
```

## Why Use RAG?

1. **Custom Knowledge**: Teach the bot your proprietary market rules, trading strategies, and institutional knowledge
2. **Live Data**: Update knowledge without retraining models
3. **Factual Accuracy**: Ground responses in your domain expertise
4. **Cost Effective**: No model fine-tuning required
5. **Explainability**: See exactly what knowledge was injected

## Quick Start

### 1. Create Knowledge Documents

Add markdown files to `knowledge_base/` directory:

```bash
knowledge_base/
├── policy/
│   └── bi_policy.md           # Bank Indonesia policy rules
├── market/
│   ├── market_rules.md        # Market microstructure
│   └── liquidity_patterns.md  # Trading hours, spreads, etc.
├── analysis/
│   └── forecast_insights.md   # Your ML model rules
└── trading/
    └── trading_rules.md       # Desk-specific rules
```

### 2. Use RAG in Code

```python
from rag_system import RAGIntegration

rag = RAGIntegration()

# Enhance prompts automatically
enhanced_prompt = rag.enhance_kei_prompt(user_question, original_prompt)
```

### 3. Run Examples

```bash
python rag_examples.py              # See integration examples
python rag_system.py                # See KB demo
```

## File Structure

### `rag_system.py`
Core RAG implementation with:
- **KnowledgeBase**: Load, search, and manage documents
- **RAGIntegration**: Enhance Kei/Kin prompts with context
- **Search Algorithm**: Keyword-based (can upgrade to vector embeddings)

### `rag_examples.py`
Shows how to:
1. Enhance Kei's prompt with BI policy knowledge
2. Enhance Kin's prompt with market analysis
3. Add custom trading rules
4. Integrate into telegram handlers

### `knowledge_base/` (auto-created)
Your custom knowledge documents in markdown/text/JSON format.

## Example Knowledge Documents

### Policy Knowledge (policy/bi_policy.md)
```markdown
# BI Policy Framework

## Current BI Rate
- Level: 5.75% (Dec 2025)
- Stance: Accommodative
- Next decision: Jan 22, 2026

## Policy Implications
- Rate hikes pause if inflation ≤ 3%
- Expected cut in Q2 2026 if CPI stable
- Rupiah level key consideration
```

### Market Rules (market/market_rules.md)
```markdown
# Market Microstructure

## Trading Hours (WIB)
- Auction: 09:00-11:30 (peak liquidity)
- Secondary: 10:00-15:00 (normal trading)
- Post-market: 15:00-16:00 (low liquidity)

## Liquidity Rules
- FR95/FR98 (short tenor): tightest spreads
- FR103/FR104 (long tenor): widest spreads
- Spread typically 2-5 bps on liquid securities
```

### Forecast Rules (analysis/forecast_insights.md)
```markdown
# Auction Demand Forecasting

## Key Drivers
1. Yield level (higher → more demand)
2. Tenor (short tenor → higher demand)
3. Market sentiment (VIX, fund flows)

## BTC Thresholds
- BTC > 4.0x: Strong demand
- BTC 3.0-4.0x: Normal demand
- BTC < 2.5x: Weak demand (caution signal)

## Model Features
- Previous BTC, BI rate, inflation, USD/IDR, VIX
```

## Integration with Telegram Bot

### Option A: Add RAG to ask_kei()

```python
from rag_system import RAGIntegration

async def ask_kei(question: str, dual_mode: bool = False):
    """Ask Kei with RAG-enhanced prompt."""
    
    rag = RAGIntegration()
    
    # Original system prompt
    system_prompt = """You are Kei..."""
    
    # Enhance with RAG
    system_prompt = rag.enhance_kei_prompt(question, system_prompt)
    
    # Continue as before
    messages = [{"role": "system", "content": system_prompt}]
    # ... rest of function
```

### Option B: Add RAG to ask_kin()

```python
async def ask_kin(question: str, dual_mode: bool = False):
    """Ask Kin with RAG-enhanced prompt."""
    
    rag = RAGIntegration()
    
    # Original system prompt
    system_prompt = """You are Kin..."""
    
    # Enhance with RAG
    system_prompt = rag.enhance_kin_prompt(question, system_prompt)
    
    # Continue as before
    messages = [{"role": "system", "content": system_prompt}]
    # ... rest of function
```

## Search & Retrieval

### Simple Keyword Search (Current)
- Fast, lightweight
- Works well for well-structured knowledge
- No external dependencies

### Next Level: Vector Embeddings
For better semantic search, upgrade to embeddings:

```python
# Option 1: OpenAI Embeddings (requires API key, ~$0.02 per 1M tokens)
from openai import OpenAI
client = OpenAI()
embedding = client.embeddings.create(input="text", model="text-embedding-3-small")

# Option 2: Open-source Sentence Transformers (free, local)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("text")

# Option 3: Managed Vector DB
# Chroma: pip install chromadb
# Pinecone: https://pinecone.io (serverless, easy scale)
# Weaviate: https://weaviate.io (flexible, open-source)
```

## Knowledge Document Format

### Markdown (.md)
```markdown
# Section Title

## Subsection
- Bullet point 1
- Bullet point 2

Content goes here...
```

### JSON (.json)
```json
{
  "content": "Your knowledge content here...",
  "category": "policy",
  "tags": ["bi", "rate", "policy"],
  "version": "1.0",
  "updated_date": "2025-12-25"
}
```

### Plain Text (.txt)
```
Any plain text format works fine.
Just ensure clear structure for readability.
```

## API Reference

### KnowledgeBase

```python
kb = KnowledgeBase("knowledge_base")

# Search
results = kb.search("query text", top_k=3, min_score=0.1)
# → List[Dict] with filename, category, content, score

# Get category
policy_docs = kb.get_category("policy")
# → List[Dict] with all policy documents

# Add document
kb.add_document("filename.md", "content", category="trading")

# List all
all_docs = kb.list_documents()
# → List[Dict] with id, filename, category, size_kb

# Get context for injection
context = kb.get_context("query", top_k=3)
# → Formatted string ready for prompt injection
```

### RAGIntegration

```python
rag = RAGIntegration("knowledge_base")

# Enhance Kei's prompt
enhanced = rag.enhance_kei_prompt(question, original_prompt)

# Enhance Kin's prompt
enhanced = rag.enhance_kin_prompt(question, original_prompt)

# Get KB summary
summary = rag.get_kb_summary()
# → {"total_documents": N, "categories": {...}, "documents": [...]}
```

## Best Practices

1. **Organize by Category**: Use subdirectories (policy/, market/, trading/)
2. **Keep it Current**: Update knowledge documents when market rules change
3. **Be Specific**: "BI rate cut signals loose policy" > "BI matters"
4. **Document Sources**: Include dates and attribution
5. **Test Coverage**: Ensure knowledge is actually used (check prompts)
6. **Version Control**: Track knowledge base changes in git

## Troubleshooting

### RAG Context Not Being Used?
1. Check search scores: `kb.search(query, min_score=0.0)` to see all matches
2. Lower `min_score` threshold temporarily to debug
3. Verify documents loaded: `len(kb.documents)` should be > 0

### Search Returning Wrong Results?
1. Current implementation uses keyword matching (case-insensitive)
2. Consider upgrading to vector embeddings for semantic similarity
3. Ensure knowledge documents have clear keywords

### Memory Usage?
- File-based KB: ~100KB per 1MB of documents
- Switch to vector DB (Chroma, Pinecone) for larger KBs (>100MB)

## Production Deployment

### Option 1: Keyword Search (Current)
- ✅ Simple, no dependencies, fast
- ❌ Limited semantic understanding
- **Use when**: Well-structured knowledge, specific terminology

### Option 2: Vector Embeddings + Chroma
```bash
pip install chromadb sentence-transformers
```
- ✅ Semantic search, local storage, free
- ❌ Slightly slower, requires embedding model
- **Use when**: Flexible knowledge, natural language queries

### Option 3: Pinecone (Managed)
```bash
pip install pinecone-client
```
- ✅ Scalable, managed, fast
- ❌ Requires API key, small monthly cost
- **Use when**: Large-scale, production system

## Example Workflow

```bash
# 1. Create knowledge documents
mkdir -p knowledge_base/{policy,market,analysis,trading}
echo "# My BI Policy Notes..." > knowledge_base/policy/bi_notes.md

# 2. Test RAG system
python rag_system.py

# 3. Check what gets injected
python rag_examples.py

# 4. Integrate into telegram_bot.py
# Edit ask_kei() and ask_kin() functions

# 5. Test with actual queries
# In Telegram: /kei What will auction demand be?

# 6. Monitor and refine
# Watch if knowledge is being used effectively
```

## Advanced: Custom Search Implementation

Replace `search()` method in `KnowledgeBase` class:

```python
def search(self, query: str, top_k: int = 3) -> List[Dict]:
    """Your custom search implementation."""
    # Option 1: SQL full-text search
    # Option 2: Elasticsearch
    # Option 3: Vector embeddings
    # Option 4: Hybrid BM25 + semantic
    pass
```

## Next Steps

1. ✅ Understand RAG concept (read this doc)
2. ✅ Review examples (`python rag_examples.py`)
3. **TODO**: Create your knowledge base (start with 2-3 documents)
4. **TODO**: Integrate RAG into ask_kei() and ask_kin()
5. **TODO**: Test with sample queries
6. **TODO**: Iterate and refine knowledge base
7. **TODO**: (Optional) Upgrade to vector embeddings for scale

## Support

For vector embedding upgrades or scaling to production:
- OpenAI: https://platform.openai.com/docs/guides/embeddings
- Sentence Transformers: https://www.sbert.net/
- Chroma: https://docs.trychroma.com/
- Pinecone: https://docs.pinecone.io/

---

**Status**: ✅ RAG System Ready for Integration
**Last Updated**: December 25, 2025
