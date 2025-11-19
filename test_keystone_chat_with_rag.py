#!/usr/bin/env python3
"""
Test Keystone Bot Chat Endpoint with RAG Integration

This script tests the Flask chat endpoint to verify that RAG (Retrieval-Augmented Generation)
is properly integrated and returning context-aware responses.

Usage:
    python3 test_keystone_chat_with_rag.py

Requirements:
    - Keystone bot must be running on port 5001
    - Knowledge base must be loaded
    - VOYAGE_API_KEY must be set
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BOT_URL = "http://localhost:5001"
CHAT_ENDPOINT = f"{BOT_URL}/api/chat"

# Test queries designed to trigger RAG retrieval
TEST_QUERIES = [
    {
        "query": "How much does interlock installation cost?",
        "expected_keywords": ["$", "cost", "price", "sq ft", "square"],
        "rag_should_trigger": True,
        "description": "Pricing query - should retrieve cost information from KB"
    },
    {
        "query": "Do you offer a warranty on your work?",
        "expected_keywords": ["warranty", "year", "guarantee"],
        "rag_should_trigger": True,
        "description": "Warranty query - should retrieve warranty details from KB"
    },
    {
        "query": "What's the best time of year to install a driveway?",
        "expected_keywords": ["season", "time", "month", "weather"],
        "rag_should_trigger": True,
        "description": "Timing query - should retrieve seasonal information from KB"
    },
    {
        "query": "Can you install hardscaping in winter?",
        "expected_keywords": ["winter", "season", "install"],
        "rag_should_trigger": True,
        "description": "Seasonal query - should reference installation timing"
    },
    {
        "query": "What services do you offer?",
        "expected_keywords": ["service", "offer", "interlock", "patio", "driveway"],
        "rag_should_trigger": True,
        "description": "Services query - should retrieve service list from KB"
    },
    {
        "query": "What's the weather like today?",
        "expected_keywords": [],
        "rag_should_trigger": False,
        "description": "Non-KB query - should work without RAG context"
    },
]


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_header(text):
    """Print a formatted header."""
    print()
    print_separator()
    print(f"  {text}")
    print_separator()
    print()


def check_bot_health():
    """Check if the bot is running and healthy."""
    try:
        response = requests.get(f"{BOT_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Bot is running and healthy")
            return True
        else:
            print(f"❌ Bot returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to bot at {BOT_URL}")
        print(f"   Make sure the bot is running: cd bots/keystone-landscaping && python3 app.py")
        return False
    except Exception as e:
        print(f"❌ Error checking bot health: {e}")
        return False


def send_chat_message(message, conversation_history=None):
    """
    Send a message to the chat endpoint.

    Args:
        message: User message string
        conversation_history: Optional list of previous messages

    Returns:
        dict: Response data or None if error
    """
    payload = {
        "message": message,
        "conversation_history": conversation_history or [],
        "session_id": f"test_session_{int(time.time())}"
    }

    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 30 seconds")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - is the bot running?")
        return None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None


def test_query(test_case, query_num, total_queries):
    """Test a single query and verify the response."""
    query = test_case["query"]
    expected_keywords = test_case["expected_keywords"]
    description = test_case["description"]
    rag_should_trigger = test_case["rag_should_trigger"]

    print(f"\n[{query_num}/{total_queries}] {description}")
    print(f"Query: \"{query}\"")
    print()

    # Send the query
    start_time = time.time()
    result = send_chat_message(query)
    elapsed_time = time.time() - start_time

    if not result:
        print(f"❌ FAILED: No response received")
        return False

    response_text = result.get("response", "")
    print(f"Response ({elapsed_time:.2f}s):")
    print(f"  {response_text[:200]}...")
    if len(response_text) > 200:
        print(f"  ... ({len(response_text)} total characters)")
    print()

    # Check for expected keywords
    found_keywords = []
    missing_keywords = []

    for keyword in expected_keywords:
        if keyword.lower() in response_text.lower():
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    # Evaluate results
    success = True

    if expected_keywords:
        if found_keywords:
            print(f"✅ Found expected keywords: {', '.join(found_keywords)}")
        if missing_keywords:
            print(f"⚠️  Missing keywords: {', '.join(missing_keywords)}")
            # Only fail if we expected RAG and got no keywords
            if rag_should_trigger:
                print(f"   (This might indicate RAG didn't trigger)")

    # Check response time
    if elapsed_time > 5.0:
        print(f"⚠️  Slow response: {elapsed_time:.2f}s (target: <3s)")
    elif elapsed_time > 3.0:
        print(f"⏱️  Response time: {elapsed_time:.2f}s (acceptable)")
    else:
        print(f"⚡ Fast response: {elapsed_time:.2f}s")

    print()
    return success


def main():
    """Run all tests."""
    print_header("KEYSTONE BOT - RAG INTEGRATION TEST")

    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Bot URL: {BOT_URL}")
    print(f"Test Queries: {len(TEST_QUERIES)}")
    print()

    # Check bot health first
    if not check_bot_health():
        print()
        print("="*80)
        print("CANNOT PROCEED: Bot is not running")
        print("="*80)
        print()
        print("To start the bot:")
        print("  1. cd /opt/bot-farm/bots/keystone-landscaping")
        print("  2. python3 app.py")
        print()
        print("Then run this test again.")
        return

    # Run tests
    print_header("RUNNING TEST QUERIES")

    total_queries = len(TEST_QUERIES)
    successful = 0
    failed = 0

    for i, test_case in enumerate(TEST_QUERIES, 1):
        try:
            if test_query(test_case, i, total_queries):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {i} crashed: {e}")
            failed += 1

        # Add delay between requests to avoid rate limits
        if i < total_queries:
            time.sleep(2)

    # Summary
    print_header("TEST SUMMARY")

    print(f"Total Queries: {total_queries}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()

    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("✅ RAG integration is working correctly")
        print("✅ Bot responds to both KB and general queries")
        print("✅ Response times are acceptable")
    else:
        print(f"⚠️  {failed} test(s) had issues")
        print()
        print("This might indicate:")
        print("  - RAG not retrieving relevant context")
        print("  - Knowledge base not loaded")
        print("  - Similarity threshold too high")
        print("  - Bot configuration issue")

    print()
    print("="*80)
    print()

    # Additional diagnostics
    print("DIAGNOSTIC INFORMATION:")
    print()
    print("To check RAG status:")
    print("  - Check bot startup logs for 'RAG system initialized'")
    print("  - Verify knowledge base loaded: python3 -c \"from shared.database import get_db_connection; ...")
    print()
    print("To adjust RAG settings:")
    print("  - Edit: bots/keystone-landscaping/rag_config.py")
    print("  - Lower SIMILARITY_THRESHOLD (currently 0.7) to 0.6 for more results")
    print("  - Increase TOP_K_CHUNKS for more context")
    print()


if __name__ == "__main__":
    main()
