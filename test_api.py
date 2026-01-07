#!/usr/bin/env python3
"""
Test PerisAI Mobile App API Connection
"""
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"✅ Health: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health failed: {e}")
        return False

def test_chat():
    """Test chat endpoint"""
    print("\n🔍 Testing /chat endpoint...")
    payload = {
        "q": "Show 5 year yield in 2024",
        "persona": "kei"
    }
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Chat failed: {e}")
        return False

def test_query():
    """Test query endpoint"""
    print("\n🔍 Testing /query endpoint...")
    payload = {
        "q": "Show 5 year yield in 2024"
    }
    try:
        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query response received")
            print(f"   Text: {data.get('text', 'N/A')[:100]}...")
        else:
            print(f"❌ Status {response.status_code}: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PerisAI Mobile App - API Connection Test")
    print(f"API URL: {API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        "health": test_health(),
        "chat": test_chat(),
        "query": test_query(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test.upper():15} {status}")
    
    all_passed = all(results.values())
    print("=" * 60)
    if all_passed:
        print("🚀 All tests passed! App is ready to use.")
    else:
        print("⚠️  Some tests failed. Check logs above.")
    print("=" * 60)
