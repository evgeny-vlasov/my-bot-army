#!/usr/bin/env python3
"""
Test script to verify:
1. RAG retrieval cursor indexing fix
2. API usage column name fix (usage_date → date)
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.database import DatabaseConnection, log_api_usage
from shared.rag import VoyageClient, RAGRetriever

def test_rag_retrieval():
    """Test RAG retrieval with RealDictCursor."""
    print("=" * 60)
    print("TEST 1: RAG Retrieval (Cursor Indexing Fix)")
    print("=" * 60)

    try:
        # Initialize
        voyage = VoyageClient()
        db = DatabaseConnection()
        retriever = RAGRetriever(voyage, db)

        bot_id = "therapist"
        query = "What services does Psyling offer?"

        print(f"\nBot ID: {bot_id}")
        print(f"Query: {query}")
        print(f"Threshold: 0.7")

        # Test search
        results = retriever.search(
            bot_id=bot_id,
            query=query,
            top_k=5,
            similarity_threshold=0.7
        )

        print(f"\n✓ RAG: Found {len(results)} relevant chunks (threshold: 0.7)")

        if results:
            print("\nTop results:")
            for i, result in enumerate(results[:3], 1):
                print(f"\n  [{i}] Similarity: {result['similarity']:.3f}")
                print(f"      Source: {result['document_title']}")
                print(f"      Content: {result['content'][:100]}...")

            # Format context
            context = retriever.format_context(results[:3])
            print("\n" + "=" * 60)
            print("Formatted Context Preview:")
            print("=" * 60)
            print(context[:300] + "...")

            return True
        else:
            print("\n⚠ WARNING: No chunks found. This might indicate:")
            print("  - No documents loaded for this bot")
            print("  - Similarity threshold too high")
            print("  - Embedding mismatch")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_usage_logging():
    """Test API usage logging (usage_date → date fix)."""
    print("\n" + "=" * 60)
    print("TEST 2: API Usage Logging (Column Name Fix)")
    print("=" * 60)

    try:
        # Test logging usage
        bot_id = "therapist"
        input_tokens = 1000
        output_tokens = 500
        cost = 0.0105

        print(f"\nLogging usage:")
        print(f"  Bot ID: {bot_id}")
        print(f"  Input tokens: {input_tokens}")
        print(f"  Output tokens: {output_tokens}")
        print(f"  Cost: ${cost}")

        success = log_api_usage(bot_id, input_tokens, output_tokens, cost)

        if success:
            print("\n✓ API usage logged successfully")
            print("  - Column 'date' recognized (not 'usage_date')")
            print("  - No SQL errors")
            return True
        else:
            print("\n✗ Failed to log API usage")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        if "usage_date" in str(e):
            print("\n  ⚠ ISSUE: Still referencing 'usage_date' column!")
            print("  Expected: Column name should be 'date'")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CRITICAL FIX VERIFICATION")
    print("=" * 60)
    print("\nTesting:")
    print("1. RAG retrieval cursor indexing (bot_row[0] → bot_row['id'])")
    print("2. API usage column name (usage_date → date)")
    print()

    # Run tests
    test1_pass = test_rag_retrieval()
    test2_pass = test_api_usage_logging()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"RAG Retrieval:     {'✓ PASS' if test1_pass else '✗ FAIL'}")
    print(f"API Usage Logging: {'✓ PASS' if test2_pass else '✗ FAIL'}")
    print()

    if test1_pass and test2_pass:
        print("🎉 ALL TESTS PASSED!")
        print("\nExpected behavior:")
        print("  ✓ RAG finds relevant chunks")
        print("  ✓ No KeyError exceptions")
        print("  ✓ No 'column usage_date' errors")
        return 0
    else:
        print("⚠ SOME TESTS FAILED")
        print("\nReview the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
