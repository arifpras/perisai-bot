#!/usr/bin/env python3
"""
Full simulation of /kei plot command with AI analysis
"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

import asyncio
import base64
import os

# Set fake API key for testing
os.environ['OPENAI_API_KEY'] = 'test-key-for-simulation'

from app_fastapi import chat_endpoint, ChatRequest

async def simulate_full_kei_response():
    question = "plot 5 year and 10 year 2024"
    
    print("=" * 80)
    print("FULL BOT RESPONSE SIMULATION (WITH AI ANALYSIS)")
    print("=" * 80)
    print(f"\nUser message: /kei {question}\n")
    
    # Step 1: Get plot from FastAPI
    print("Step 1: Getting plot from FastAPI /chat endpoint...")
    payload = {"q": question, "plot": True}
    req = ChatRequest(**payload)
    
    try:
        result = await chat_endpoint(req)
        data_bytes = result.body
        
        import json
        data = json.loads(data_bytes.decode('utf-8'))
        
        data_summary = data.get('analysis', '')
        image_b64 = data.get('image', None)
        
        print("=" * 80)
        print("MESSAGE 1: PLOT IMAGE")
        print("=" * 80)
        
        if image_b64:
            print("\n📊 [IMAGE SENT]")
            print(f"Caption: 💹 Kei | Quant Research")
            
            image_bytes = base64.b64decode(image_b64)
            output_file = 'bot_with_ai_analysis.png'
            with open(output_file, 'wb') as f:
                f.write(image_bytes)
            
            print(f"\n✅ Plot saved to: {output_file}")
            print(f"   Size: {len(image_bytes):,} bytes")
        
        # Step 2: Generate AI analysis (simulation)
        print("\n" + "=" * 80)
        print("MESSAGE 2: AI-GENERATED ANALYSIS")
        print("=" * 80)
        print("\n[Bot shows typing indicator...]")
        
        # Simulate what the AI would receive
        ai_prompt = f"{question}\\n\\nData: {data_summary}"
        
        print(f"\nPrompt to OpenAI GPT:")
        print("-" * 80)
        print(ai_prompt)
        print("-" * 80)
        
        # Simulated AI response (what Kei would actually generate)
        simulated_ai_analysis = """The bond yield data for 2024 reveals several key insights:

**5-Year vs 10-Year Spread Analysis:**
- The yield curve maintained a positive slope throughout 2024, with the 10-year consistently trading above the 5-year
- Average 5-year yield: ~6.5%, Average 10-year yield: ~6.6%
- The spread widened in Q2, suggesting market expectations of sustained higher rates

**Volatility Patterns:**
- Peak volatility occurred in March-April 2024, coinciding with Fed policy uncertainty
- Both tenors moved in tandem, indicating systematic risk factors dominating
- The 262 trading days captured show relatively tight range-bound behavior

**Trading Implications:**
- Curve steepening opportunities emerged during periods of spread widening
- The positive term premium suggests compensation for duration risk
- Multi-year comparison would reveal whether this represents normalization post-2023"""

        print("\n💹 Kei | Quant Research")
        print(simulated_ai_analysis)
        
        print("\n" + "=" * 80)
        print("SIMULATION COMPLETE")
        print("=" * 80)
        
        print("\n✅ Users will now receive:")
        print("   1. Plot image with Economist styling")
        print("   2. AI-generated insights analyzing the data")
        print("\n⚠️  Note: Actual AI response will vary based on GPT output")
        print("   This simulation shows the expected flow and format")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(simulate_full_kei_response())
