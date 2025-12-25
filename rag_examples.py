"""
RAG Integration Examples for Perisai Bot

Shows how to integrate RAG into Kei and Kin prompts.
"""

from rag_system import RAGIntegration


def example_1_kei_with_rag():
    """Example: Enhance Kei's response with BI policy knowledge."""
    
    rag = RAGIntegration()
    
    # Original system prompt (Kei data-query mode)
    original_prompt = """You are Kei.
Profile: CFA charterholder, PhD (MIT). World-class data scientist with deep expertise in mathematics, statistics, econometrics, and forecasting.

STYLE RULE — HEADLINE-LED CORPORATE UPDATE (HL-CU)
Title: Exactly one line. Format: 📰 TICKER: Key Metric / Event +X% (Timeframe).
Body: exactly 3 paragraphs, max 2 sentences each, ≤140 words total.

Data access:
- Historical bond prices and yields (2023-2025)
- Auction demand forecasts through 2026"""

    # User's question
    question = "What will auction demand be in January 2026?"
    
    # Enhance with RAG
    enhanced_prompt = rag.enhance_kei_prompt(question, original_prompt)
    
    print("=" * 80)
    print("EXAMPLE 1: Kei with RAG Context")
    print("=" * 80)
    print(f"\nQuestion: {question}")
    print(f"\nOriginal prompt length: {len(original_prompt)} chars")
    print(f"Enhanced prompt length: {len(enhanced_prompt)} chars")
    print(f"\nAdded context: {len(enhanced_prompt) - len(original_prompt)} chars")
    print("\n" + "-" * 80)
    print("ENHANCED PROMPT (last 500 chars):")
    print("-" * 80)
    print(enhanced_prompt[-500:])


def example_2_kin_with_rag():
    """Example: Enhance Kin's response with market analysis knowledge."""
    
    rag = RAGIntegration()
    
    # Original system prompt (Kin with data)
    original_prompt = """You are Kin.
Profile: CFA charterholder, PhD (Harvard). World-class economist and data-driven storyteller.

STYLE RULE — HEADLINE-LED CORPORATE UPDATE (HL-CU)
Body (Kin): exactly 3 paragraphs, max 2 sentences each, ≤220 words total.

Available market context:
[Bond data would go here]"""

    # User's question about market implications
    question = "What are the implications of BI rate hold for bond yields?"
    
    # Enhance with RAG
    enhanced_prompt = rag.enhance_kin_prompt(question, original_prompt)
    
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Kin with RAG Context")
    print("=" * 80)
    print(f"\nQuestion: {question}")
    print(f"\nOriginal prompt length: {len(original_prompt)} chars")
    print(f"Enhanced prompt length: {len(enhanced_prompt)} chars")
    print(f"\nAdded context: {len(enhanced_prompt) - len(original_prompt)} chars")
    print("\n" + "-" * 80)
    print("ENHANCED PROMPT (last 600 chars):")
    print("-" * 80)
    print(enhanced_prompt[-600:])


def example_3_add_custom_knowledge():
    """Example: Add custom knowledge to the KB."""
    
    rag = RAGIntegration()
    
    # Custom institutional knowledge
    custom_kb = """
# Perisai Trading Desk Rules

## Key Indicators to Watch
1. BI Rate Decisions (monthly)
   - Rate hikes: +50 bps tightens yield curve
   - Rate cuts: -50 bps steepens yield curve
   - Hold: Market typically already priced in

2. Rupiah Movements
   - IDR strength: Capital inflows → bond demand up
   - IDR weakness: Capital outflows → bond demand down
   - Threshold: USD/IDR > 15,500 = watch for weakness

3. Global Risk Sentiment
   - VIX above 25: Flight to safety → demand for long bonds
   - VIX below 15: Risk-on → favor shorter tenors

## Optimal Trading Times
- Morning (09:00-11:00 WIB): Highest liquidity, tightest spreads
- Afternoon (14:00-15:30 WIB): Lower liquidity, wider spreads
- Post-3pm: Minimal trading, avoid unless urgent

## Portfolio Rules
- Duration target: 5-7 years (FR95/FR98 mix)
- Maximum single security: 15% of portfolio
- Minimum bid-to-cover to buy at auction: 3.0x
"""
    
    # Add to KB
    rag.kb.add_document("trading_rules.md", custom_kb, category="trading")
    
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Add Custom Knowledge")
    print("=" * 80)
    print("\nAdded: trading_rules.md to category 'trading'")
    
    # Show updated KB
    summary = rag.get_kb_summary()
    print(f"\nUpdated KB summary:")
    for cat, files in summary['categories'].items():
        print(f"  {cat}: {len(files)} document(s)")


def example_4_integration_in_handler():
    """Example code for integrating RAG into Telegram handlers."""
    
    code = """
# How to integrate RAG in telegram_bot.py

# In ask_kei() function:
async def ask_kei(question: str, dual_mode: bool = False):
    # ... existing code ...
    
    # Initialize RAG
    rag = RAGIntegration()
    
    # Compute bond summary as before
    data_summary = await try_compute_bond_summary(question)
    
    # NEW: Enhance system prompt with RAG context
    system_prompt = ... # original prompt
    system_prompt = rag.enhance_kei_prompt(question, system_prompt)
    
    # Continue with API call as before
    messages.append({"role": "system", "content": system_prompt})
    # ... rest of function


# In ask_kin() function:
async def ask_kin(question: str, dual_mode: bool = False):
    # ... existing code ...
    
    # NEW: Enhance system prompt with RAG context
    rag = RAGIntegration()
    system_prompt = ... # original prompt
    system_prompt = rag.enhance_kin_prompt(question, system_prompt)
    
    # Continue as before
    messages.append({"role": "system", "content": system_prompt})
    # ... rest of function
    """
    
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Integration Code")
    print("=" * 80)
    print(code)


if __name__ == "__main__":
    example_1_kei_with_rag()
    example_2_kin_with_rag()
    example_3_add_custom_knowledge()
    example_4_integration_in_handler()
    
    print("\n" + "=" * 80)
    print("RAG IMPLEMENTATION COMPLETE")
    print("=" * 80)
    print("""
Next Steps:
1. Review the examples above
2. Add your own knowledge documents to knowledge_base/
3. Integrate RAG into ask_kei() and ask_kin() functions
4. Test with sample queries
5. For production: Replace keyword search with vector embeddings
   - Use OpenAI Embeddings API
   - Or open-source: sentence-transformers
   - Store in vector DB: Chroma, Pinecone, or Weaviate
""")
