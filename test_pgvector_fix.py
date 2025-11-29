#!/usr/bin/env python3
"""
Test script to verify pgvector type registration fix.

This script tests:
1. Vector type is properly registered with psycopg2
2. RAG retrieval works correctly
3. Embeddings are returned as proper vector types, not strings
"""

import sys
sys.path.insert(0, '/home/user/my-bot-army')

from shared.database import DatabaseConnection
from shared.rag import VoyageClient, RAGRetriever

def test_vector_type_registration():
    """Test that pgvector type is properly registered"""
    print("=" * 60)
    print("TEST 1: Vector Type Registration")
    print("=" * 60)

    db = DatabaseConnection()

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Try to query a document with embedding
                cur.execute("""
                    SELECT id, bot_id, embedding
                    FROM documents
                    LIMIT 1
                """)
                result = cur.fetchone()

                if result:
                    embedding = result['embedding']
                    print(f"✓ Found document: bot_id={result['bot_id']}")
                    print(f"✓ Embedding type: {type(embedding)}")
                    print(f"✓ Embedding value (first 50 chars): {str(embedding)[:50]}...")

                    # Check if it's a string (bad) or proper type
                    if isinstance(embedding, str):
                        print("✗ ERROR: Embedding is a string! pgvector not registered properly.")
                        return False
                    else:
                        print("✓ SUCCESS: Embedding is not a string - pgvector registered!")
                        return True
                else:
                    print("⚠ No documents found in database to test")
                    return None

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_retrieval():
    """Test RAG retrieval functionality"""
    print("\n" + "=" * 60)
    print("TEST 2: RAG Retrieval")
    print("=" * 60)

    try:
        # Initialize RAG components
        voyage = VoyageClient(model="voyage-3-lite")
        db = DatabaseConnection()
        retriever = RAGRetriever(voyage, db)

        # Test retrieval for therapist bot
        print("\nTesting RAG search for 'therapist' bot...")
        results = retriever.search(
            bot_id="therapist",
            query="What services does Psyling offer?",
            top_k=5,
            similarity_threshold=0.3
        )

        print(f"✓ Found {len(results)} chunks")

        if len(results) > 0:
            print("\nTop result:")
            print(f"  Similarity: {results[0].get('similarity', 'N/A')}")
            print(f"  Content (first 100 chars): {results[0]['content'][:100]}...")
            print("\n✓ SUCCESS: RAG retrieval working!")
            return True
        else:
            print("⚠ WARNING: No results found. This could mean:")
            print("  - No documents for 'therapist' bot in database")
            print("  - Similarity threshold too high")
            print("  - Vector search not working properly")
            return None

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "🔍 " * 30)
    print("TESTING PGVECTOR FIX")
    print("🔍 " * 30 + "\n")

    test1_result = test_vector_type_registration()
    test2_result = test_rag_retrieval()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    def format_result(result):
        if result is True:
            return "✓ PASS"
        elif result is False:
            return "✗ FAIL"
        else:
            return "⚠ SKIP"

    print(f"Vector Type Registration: {format_result(test1_result)}")
    print(f"RAG Retrieval:           {format_result(test2_result)}")

    if test1_result is True and test2_result is True:
        print("\n🎉 ALL TESTS PASSED! pgvector fix is working correctly!")
        return 0
    elif test1_result is False or test2_result is False:
        print("\n❌ SOME TESTS FAILED! Please review the errors above.")
        return 1
    else:
        print("\n⚠ Tests completed with warnings. Review output above.")
        return 0

if __name__ == '__main__':
    exit(main())
