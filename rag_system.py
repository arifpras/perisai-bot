"""
Retrieval-Augmented Generation (RAG) System for Perisai Bot

Allows injecting custom knowledge base into persona prompts.
Supports multiple backends: simple file-based (MVP), Chroma vector DB, or external APIs.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import re


class KnowledgeBase:
    """Simple file-based knowledge base with semantic search."""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        """
        Initialize knowledge base.
        
        Args:
            kb_dir: Directory containing knowledge documents (markdown/txt/json files)
        """
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(exist_ok=True)
        self.documents: List[Dict[str, Any]] = []
        self._load_documents()
    
    def _load_documents(self):
        """Load all documents from knowledge base directory."""
        self.documents = []
        
        if not self.kb_dir.exists():
            return
        
        # Use rglob for recursive search
        file_paths = list(self.kb_dir.rglob("*.md")) + list(self.kb_dir.rglob("*.txt")) + list(self.kb_dir.rglob("*.json"))
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata if JSON
                metadata = {}
                if file_path.suffix == '.json':
                    try:
                        data = json.loads(content)
                        content = data.get('content', content)
                        metadata = {k: v for k, v in data.items() if k != 'content'}
                    except json.JSONDecodeError:
                        pass
                
                self.documents.append({
                    'id': str(file_path.relative_to(self.kb_dir)),
                    'filename': file_path.name,
                    'category': file_path.parent.name if file_path.parent != self.kb_dir else 'general',
                    'content': content,
                    'length': len(content),
                    'metadata': metadata,
                    'loaded_at': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"⚠️  Failed to load {file_path}: {e}")
    
    def search(self, query: str, top_k: int = 3, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Improved keyword-based search with better scoring.
        For production, use vector embeddings (OpenAI, Sentence-Transformers).
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum relevance score (0-1)
        
        Returns:
            List of relevant documents with scores
        """
        query_lower = query.lower()
        query_terms = set(re.findall(r'\b\w+\b', query_lower))
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'in', 'of', 'to', 'for', 'on', 'at', 'by', 'from', 'with', 'what', 'how', 'will', 'be'}
        query_terms = query_terms - stop_words
        
        results = []
        for doc in self.documents:
            content_lower = doc['content'].lower()
            
            # Count exact term matches (weighted higher)
            exact_matches = sum(1 for term in query_terms if term in content_lower)
            
            # Calculate overlap score
            content_terms = set(re.findall(r'\b\w+\b', content_lower)) - stop_words
            
            if query_terms and content_terms:
                # Weighted scoring: exact matches + Jaccard similarity
                intersection = len(query_terms & content_terms)
                union = len(query_terms | content_terms)
                jaccard = intersection / union if union > 0 else 0
                
                # Boost score for exact term matches
                score = (jaccard * 0.6) + (exact_matches / len(query_terms) * 0.4) if query_terms else 0
                
                if score >= min_score:
                    results.append({
                        'id': doc['id'],
                        'filename': doc['filename'],
                        'category': doc['category'],
                        'content': doc['content'][:500] + ('...' if len(doc['content']) > 500 else ''),
                        'score': score,
                        'metadata': doc['metadata']
                    })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def get_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all documents from a specific category."""
        return [doc for doc in self.documents if doc['category'] == category]
    
    def add_document(self, filename: str, content: str, category: str = "general", 
                     metadata: Optional[Dict] = None):
        """Add a new document to the knowledge base."""
        category_dir = self.kb_dir / category
        category_dir.mkdir(exist_ok=True)
        
        file_path = category_dir / filename
        file_path.write_text(content, encoding='utf-8')
        
        self._load_documents()  # Reload to pick up new doc
        print(f"✅ Added document: {filename} to category: {category}")
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in knowledge base."""
        return [
            {
                'id': doc['id'],
                'filename': doc['filename'],
                'category': doc['category'],
                'size_kb': doc['length'] / 1024,
                'metadata': doc['metadata']
            }
            for doc in self.documents
        ]
    
    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        Get formatted context string for prompt injection.
        
        Args:
            query: User's question/query
            top_k: Number of documents to include
        
        Returns:
            Formatted string ready for prompt injection
        """
        results = self.search(query, top_k=top_k)
        
        if not results:
            return ""
        
        context_lines = ["📚 **Relevant Knowledge Base Context:**"]
        
        for i, result in enumerate(results, 1):
            context_lines.append(f"\n[Source {i}: {result['filename']} ({result['category']})]")
            context_lines.append(result['content'])
        
        return "\n".join(context_lines)


class RAGIntegration:
    """Integration layer for RAG with persona prompts."""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        self.kb = KnowledgeBase(kb_dir)
    
    def enhance_kei_prompt(self, question: str, system_prompt: str) -> str:
        """
        Inject relevant knowledge into Kei's system prompt.
        
        Args:
            question: User's query
            system_prompt: Original system prompt
        
        Returns:
            Enhanced system prompt with RAG context
        """
        context = self.kb.get_context(question, top_k=2)
        
        if not context:
            return system_prompt
        
        # Insert before data access section
        insertion_point = system_prompt.find("Data access:")
        if insertion_point > 0:
            enhanced = (
                system_prompt[:insertion_point] +
                context + "\n\n" +
                system_prompt[insertion_point:]
            )
            return enhanced
        
        return system_prompt + "\n\n" + context
    
    def enhance_kin_prompt(self, question: str, system_prompt: str) -> str:
        """
        Inject relevant knowledge into Kin's system prompt.
        
        Args:
            question: User's query
            system_prompt: Original system prompt
        
        Returns:
            Enhanced system prompt with RAG context
        """
        context = self.kb.get_context(question, top_k=3)
        
        if not context:
            return system_prompt
        
        # Append to end of system prompt
        enhanced = system_prompt + "\n\n" + context
        return enhanced
    
    def get_kb_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge base contents."""
        docs = self.kb.list_documents()
        
        categories = {}
        for doc in docs:
            cat = doc['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(doc['filename'])
        
        return {
            'total_documents': len(docs),
            'categories': categories,
            'documents': docs
        }


# Example usage and setup
def setup_example_kb():
    """Create example knowledge base files for demonstration."""
    kb = KnowledgeBase()
    
    # Example: BI Policy Knowledge
    bi_policy = """
# Bank Indonesia (BI) Policy Framework

## Current Policy Rate (December 2025)
- BI Rate: 5.75% (as of latest decision)
- Policy stance: Accommodative with data dependency
- Next review: January 22, 2026

## Key Policy Principles
1. Inflation targeting: 2-4% (midpoint 3%)
2. Exchange rate stability: Monitor USD/IDR (target 15,000-15,500 range)
3. Financial stability: Monitor credit growth and banking system health

## Market Implications
- Rate hikes likely pause if inflation stabilizes
- Rupiah strength expected if foreign capital inflows continue
- Bond yield compression possible in recovery scenario

## Historical Context
- BI raised rates from 3.0% to 5.75% in 2023-2024
- Inflation peaked at 5.93% in September 2023, now cooling
- Expectations: Rates may start declining in 2026 if inflation remains controlled
"""
    
    # Example: Market Rules
    market_rules = """
# Indonesian Bond Market Trading Rules

## Liquidity Patterns
- Peak trading hours: 09:00-11:30 WIB (opening auction)
- Secondary market: 10:00-15:00 WIB
- Lowest liquidity: 15:00-16:00 WIB (pre-close)
- Higher spreads on FR103/FR104 (long tenor) vs FR95/FR98 (short tenor)

## Auction Dynamics
- Auction frequency: Monthly (scheduled)
- Typical demand/cover ratio: 3.0-4.5x
- Bid-to-cover below 2.5x indicates weak demand
- Average issue size: 3-4 trillion IDR

## Yield Curve Patterns
- Curve typically steep (5Y-10Y spread: 80-150 bps)
- Flattening signals economic slowdown concerns
- Steepening signals growth recovery expectations

## Price-Yield Relationships
- Duration (modified): ~7-8 years for FR104, ~5-6 years for FR98
- 1% yield change → ~7% price change (for 10Y bond)
- Convexity effects most pronounced at extreme yields

## Risk Factors to Monitor
- BI rate decisions (inflation-dependent)
- Global risk sentiment (Fed decisions, emerging market flows)
- Rupiah strength/weakness (impacts capital flows)
- Domestic credit events
"""
    
    # Example: Forecast Rules
    forecast_insights = """
# Auction Demand Forecasting Rules

## Key Demand Drivers
1. **Yields vs alternatives**: Higher yields attract more demand
2. **Maturity structure**: New issues in short tenors (2-5Y) typically see higher demand
3. **Macro backdrop**: Risk-off environment → flight to safety → higher demand for long-dated bonds
4. **Seasonal patterns**: 
   - Q1: Higher demand (CNY effects, year-start portfolio rebalancing)
   - Q2: Moderate demand
   - Q3-Q4: Higher demand (year-end rebalancing, BI policy accommodation)

## Bid-to-Cover Thresholds
- **Strong demand**: BTC > 4.0x → Expect undersubscription unlikely
- **Normal demand**: BTC 3.0-4.0x → Auction likely to succeed
- **Weak demand**: BTC < 2.5x → Watch for acceptance rates, spread widening
- **Very weak**: BTC < 2.0x → Potential demand crisis signal

## ML Model Features (for your ensemble)
Primary drivers for auction forecast:
- Previous auction BTC ratio
- BI rate level and trend
- Inflation rate (YoY)
- Rupiah USD/IDR level
- Market volatility (VIX-like measure)
- Global yields (US 10Y TNX)
- Domestic credit spreads

## Accuracy Notes
- 1-month forward forecasts: ~75-80% accuracy
- 2-3 month forward: ~70-75% accuracy
- Beyond 3 months: Accuracy drops significantly, use with caution
"""
    
    # Write example files
    kb.add_document("bi_policy.md", bi_policy, category="policy")
    kb.add_document("market_rules.md", market_rules, category="market")
    kb.add_document("forecast_insights.md", forecast_insights, category="analysis")
    
    return kb


if __name__ == "__main__":
    # Setup example KB
    print("Setting up example knowledge base...")
    kb = setup_example_kb()
    
    # Show summary
    print("\n" + "="*60)
    print("KNOWLEDGE BASE SUMMARY")
    print("="*60)
    summary = kb.list_documents()
    for doc in summary:
        print(f"\n📄 {doc['filename']} ({doc['category']})")
        print(f"   Size: {doc['size_kb']:.1f} KB")
    
    # Demo search
    print("\n" + "="*60)
    print("DEMO: RAG Search")
    print("="*60)
    
    test_queries = [
        "What is the current BI rate policy?",
        "How does auction demand work?",
        "What are the yield curve patterns?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = kb.search(query, top_k=2)
        for i, result in enumerate(results, 1):
            print(f"   [{i}] {result['filename']} (relevance: {result['score']:.2f})")
            print(f"       {result['content'][:100]}...")
    
    # Demo context injection
    print("\n" + "="*60)
    print("DEMO: Context for Prompt Injection")
    print("="*60)
    
    rag = RAGIntegration()
    context = rag.kb.get_context("What will auction demand be next month?", top_k=2)
    print(context[:300] + "...")
