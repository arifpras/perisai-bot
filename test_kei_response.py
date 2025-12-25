#!/usr/bin/env python3
"""
Simulate Telegram bot response for: /kei plot 5 year and 10 year 2024
"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

import asyncio
import base64
from app_fastapi import chat_endpoint, ChatRequest

async def simulate_kei_command():
    # User input (without /kei prefix)
    question = "plot 5 year and 10 year 2024"
    
    print("=" * 80)
    print("SIMULATING BOT RESPONSE")
    print("=" * 80)
    print(f"\nUser message: /kei {question}\n")
    
    # Step 1: Check if plot is needed
    needs_plot = any(keyword in question.lower() for keyword in ["plot", "chart", "show", "graph", "visualize", "compare"])
    print(f"Plot detection: {'YES' if needs_plot else 'NO'} (keyword found in query)\n")
    
    if needs_plot:
        print("Routing through FastAPI /chat endpoint...\n")
        
        # Step 2: Call /chat endpoint
        payload = {"q": question, "plot": True}
        req = ChatRequest(**payload)
        
        try:
            result = await chat_endpoint(req)
            data_bytes = result.body
            
            import json
            data = json.loads(data_bytes.decode('utf-8'))
            
            analysis = data.get('analysis', '')
            image_b64 = data.get('image', None)
            
            print("=" * 80)
            print("BOT RESPONSE")
            print("=" * 80)
            
            # Step 3: Display what bot would send
            if image_b64:
                print("\n📊 [IMAGE SENT]")
                print(f"Caption: 💹 Kei | Quant Research")
                
                # Decode and save image
                image_bytes = base64.b64decode(image_b64)
                output_file = 'bot_response_plot.png'
                with open(output_file, 'wb') as f:
                    f.write(image_bytes)
                
                print(f"\n✅ Plot saved to: {output_file}")
                print(f"   Size: {len(image_bytes):,} bytes")
                print(f"   Base64 length: {len(image_b64):,} chars")
                
            else:
                print("\n⚠️ No image in response!")
            
            # Step 4: Display analysis text
            if analysis and analysis.strip():
                print("\n" + "-" * 80)
                print("FOLLOW-UP MESSAGE:")
                print("-" * 80)
                print(analysis)
            else:
                print("\n(No analysis text)")
            
            print("\n" + "=" * 80)
            
            # Additional info
            print("\nRESPONSE DETAILS:")
            print(f"  Keys in response: {list(data.keys())}")
            if 'rows' in data:
                print(f"  Data rows: {len(data['rows'])}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(simulate_kei_command())
