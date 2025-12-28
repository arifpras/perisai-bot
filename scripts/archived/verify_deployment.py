#!/usr/bin/env python3
"""
Post-Deployment Verification Script
Run this after deploying b62ae4e to verify all fixes
"""

import sys
import asyncio
sys.path.insert(0, '/workspaces/perisai-bot')

from app_fastapi import chat_endpoint, ChatRequest
import json

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

async def test_query(query: str):
    """Test a single query"""
    req = ChatRequest(q=query, plot=False)
    try:
        result = await chat_endpoint(req)
        data = result.body.decode('utf-8')
        parsed = json.loads(data)
        has_image = 'image' in parsed
        
        if has_image:
            image_size = len(parsed['image'])
            print(f"{GREEN}✅ PASS{RESET}")
            print(f"   Image: {image_size:,} chars (base64)")
            return True
        else:
            print(f"{RED}✗ FAIL{RESET} - No image in response")
            print(f"   Keys in response: {list(parsed.keys())}")
            return False
    except Exception as e:
        print(f"{RED}✗ ERROR{RESET} - {e}")
        return False

async def main():
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}POST-DEPLOYMENT VERIFICATION - Commit b62ae4e{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    test_cases = [
        ("Compare keyword", "compare price 5 year and 10 year in 2025"),
        ("Plot keyword", "plot 5 year and 10 year 2024"),
        ("Chart keyword", "chart yield 10 year 2025"),
        ("Single tenor", "plot yield 5 year 2025"),
        ("Multi-tenor with month", "chart yield 5 year and 10 year June 2025"),
    ]
    
    results = []
    
    for i, (name, query) in enumerate(test_cases, 1):
        print(f"{BOLD}Test {i}/{len(test_cases)}: {name}{RESET}")
        print(f'Query: "{query}"')
        success = await test_query(query)
        results.append((name, success))
        print()
    
    # Summary
    print(f"{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}VERIFICATION SUMMARY{RESET}")
    print(f"{'='*80}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for name, success in results:
        status = f"{GREEN}✅ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ ALL TESTS PASSED - Deployment successful!{RESET}")
        print(f"\n{BOLD}Next steps:{RESET}")
        print("1. Test on Telegram bot:")
        print("   /kei compare price 5 year and 10 year in 2025")
        print("2. Verify plot shows Economist styling:")
        print("   - Red and blue lines")
        print("   - Light gray background")
        print("   - Minimal borders")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ SOME TESTS FAILED - Check errors above{RESET}")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
