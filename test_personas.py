#!/usr/bin/env python3
"""
Local test script for persona functions.
Tests /kei, /kin, and /both without running the full Telegram bot.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from telegram_bot import ask_kei, ask_kin, ask_kei_then_kin


async def test_personas():
    """Test all three persona functions with sample questions."""
    
    # Check if API keys are configured
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Kei persona will not work.")
    
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("⚠️  PERPLEXITY_API_KEY not set. Kin persona will not work.")
    
    print("\n" + "="*70)
    print("🧪 Testing Persona Functions Locally")
    print("="*70 + "\n")
    
    # Test questions
    questions = [
        "What is fiscal policy?",
        "How's Indonesia's economy in 2025?",
        "yield 5 year in feb 2025"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'─'*70}")
        print(f"📝 Question {i}: {question}")
        print('─'*70)
        
        # Test Kei (OpenAI)
        print("\n🔬 Testing Kei (OpenAI)...")
        kei_answer = await ask_kei(question)
        print(f"\nKei's response:\n{kei_answer}")
        
        # Test Kin (Perplexity)
        print(f"\n{'─'*70}")
        print("💡 Testing Kin (Perplexity)...")
        kin_answer = await ask_kin(question)
        print(f"\nKin's response:\n{kin_answer}")
        
        # Test Both (chained)
        print(f"\n{'─'*70}")
        print("🔗 Testing Both (chained Kei → Kin)...")
        both_result = await ask_kei_then_kin(question)
        print(f"\nKei's analysis:\n{both_result['kei']}")
        print(f"\n{'─'*35}")
        print(f"Kin's interpretation:\n{both_result['kin']}")
        
        print(f"\n{'='*70}\n")
        
        # Pause between questions
        if i < len(questions):
            await asyncio.sleep(2)
    
    print("\n✅ All persona tests completed!\n")


if __name__ == "__main__":
    asyncio.run(test_personas())
