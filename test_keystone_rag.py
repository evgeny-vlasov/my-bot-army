#!/usr/bin/env python3
"""
Test Keystone Hardscapes RAG System

This script tests the RAG system with sample queries to verify that
the knowledge base is loaded correctly and returns relevant context.

Usage:
    python3 test_keystone_rag.py

Environment:
    VOYAGE_API_KEY must be set
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db_connection
from shared.rag_helpers import rag_query

# Configuration
BOT_ID = 1  # Keystone Hardscapes bot
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

# Test queries
TEST_QUERIES = [
    "What services does Keystone Hardscapes offer?",
    "How much does a patio cost?",
    "What areas do you serve?",
    "Do you offer warranties?",
    "How do I get a quote?",
]


def print_separator(char="=", length=70):
    """Print a separator line."""
    print(char * length)


def test_query(query_text, top_k=3):
    """Test a single RAG query."""
    print()
    print_separator()
    print(f"QUERY: {query_text}")
    print_separator()
    print()
    
    try:
        with get_db_connection() as conn:
            context = rag_query(
                conn=conn,
                bot_id=BOT_ID,
                user_query=query_text,
                voyage_api_key=VOYAGE_API_KEY,
                top_k=top_k
            )
        
        if context and context.strip():
            print(context)
            print()
            print(f"✓ Retrieved {context.count('[Source:')} context chunks")
        else:
            print("⚠ No relevant context found")
            print()
            print("This might indicate:")
            print("  - Knowledge base not loaded")
            print("  - Query doesn't match any documents")
            print("  - Similarity threshold too high")
        
        return True
    
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test queries."""
    
    # Validate API key
    if not VOYAGE_API_KEY:
        print("ERROR: VOYAGE_API_KEY environment variable not set")
        print("Set it with: export VOYAGE_API_KEY='your-api-key'")
        sys.exit(1)
    
    print()
    print_separator("=", 70)
    print("KEYSTONE HARDSCAPES RAG SYSTEM TEST")
    print_separator("=", 70)
    
    # Check bot exists and has documents
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get bot info
            cur.execute("SELECT bot_id, bot_name FROM bots WHERE id = %s", (BOT_ID,))
            bot = cur.fetchone()
            
            if not bot:
                print(f"\n✗ ERROR: Bot with id={BOT_ID} not found in database")
                sys.exit(1)
            
            bot_id_str = bot[0] if isinstance(bot, tuple) else bot['bot_id']
            bot_name = bot[1] if isinstance(bot, tuple) else bot['bot_name']
            
            # Get document count
            cur.execute("""
                SELECT COUNT(*) FROM documents WHERE bot_id = %s
            """, (bot_id_str,))
            doc_count = cur.fetchone()[0]
            
            # Get chunk count
            cur.execute("""
                SELECT COUNT(*) FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.bot_id = %s
            """, (bot_id_str,))
            chunk_count = cur.fetchone()[0]
    
    print()
    print(f"Bot: {bot_name} ({bot_id_str})")
    print(f"Documents: {doc_count}")
    print(f"Chunks: {chunk_count}")
    print()
    
    if doc_count == 0:
        print("⚠ WARNING: No documents found for this bot")
        print("Run: python3 load_keystone_kb.py")
        print()
    
    if chunk_count == 0:
        print("⚠ WARNING: No chunks found for this bot")
        print("Documents may not be processed yet")
        print()
    
    # Run test queries
    print_separator("=", 70)
    print(f"RUNNING {len(TEST_QUERIES)} TEST QUERIES")
    print_separator("=", 70)
    
    successful_queries = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print()
        print(f"[{i}/{len(TEST_QUERIES)}]", end=" ")
        
        if test_query(query, top_k=3):
            successful_queries += 1
    
    # Summary
    print()
    print_separator("=", 70)
    print("SUMMARY")
    print_separator("=", 70)
    print(f"Successful queries: {successful_queries}/{len(TEST_QUERIES)}")
    
    if successful_queries == len(TEST_QUERIES):
        print()
        print("✓ All queries completed successfully!")
        print()
        print("The RAG system is working correctly. You can now:")
        print("  1. Update the bot's system prompt to use RAG")
        print("  2. Test with the live bot interface")
    elif successful_queries > 0:
        print()
        print("⚠ Some queries failed")
        print("Check the error messages above for details")
    else:
        print()
        print("✗ All queries failed")
        print("Check that:")
        print("  1. Knowledge base is loaded (python3 load_keystone_kb.py)")
        print("  2. VOYAGE_API_KEY is set correctly")
        print("  3. Database connection is working")


if __name__ == "__main__":
    main()
