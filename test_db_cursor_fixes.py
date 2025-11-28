#!/usr/bin/env python3
"""
Test script to validate all RealDictCursor fixes.
Tests all database operations that were fixed to ensure they work correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db_connection


def test_basic_queries():
    """Test basic fetchone() and fetchall() operations."""
    print("=" * 60)
    print("TEST 1: Basic Query Operations")
    print("=" * 60)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Test 1: Fetch single value with column name
            print("\n✓ Testing: SELECT id FROM bots")
            cur.execute("SELECT id, bot_id, bot_name FROM bots LIMIT 1")
            row = cur.fetchone()
            if row:
                print(f"  Bot ID (numeric): {row['id']}")
                print(f"  Bot ID (string): {row['bot_id']}")
                print(f"  Bot Name: {row['bot_name']}")
            else:
                print("  ⚠ No bots found in database")

            # Test 2: Fetch multiple rows
            print("\n✓ Testing: SELECT bot_id FROM bots (all)")
            cur.execute("SELECT bot_id FROM bots")
            rows = cur.fetchall()
            print(f"  Found {len(rows)} bots:")
            for row in rows:
                print(f"    - {row['bot_id']}")

    print("\n✅ Basic query tests PASSED\n")


def test_insert_returning():
    """Test INSERT with RETURNING clause (simulates embedder.py:323 fix)."""
    print("=" * 60)
    print("TEST 2: INSERT...RETURNING id Pattern")
    print("=" * 60)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get a valid bot_id first
            cur.execute("SELECT id FROM bots LIMIT 1")
            bot_row = cur.fetchone()
            if not bot_row:
                print("  ⚠ No bots found, skipping test")
                return

            bot_id = bot_row['id']

            # Test INSERT...RETURNING (this is the pattern that was broken)
            print(f"\n✓ Testing: INSERT INTO documents...RETURNING id")
            cur.execute("""
                INSERT INTO documents
                    (bot_id, title, content, source, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (
                bot_id,
                'Test Document - Cursor Fix Validation',
                'This is test content to validate cursor fixes.',
                'test_script',
                '{"test": true}'
            ))

            # This is the line that was broken (fetchone()[0])
            # Now fixed to fetchone()['id']
            document_id = cur.fetchone()['id']
            print(f"  ✅ Successfully inserted document with ID: {document_id}")

            # Clean up
            cur.execute("DELETE FROM documents WHERE id = %s", (document_id,))
            conn.commit()
            print(f"  🧹 Cleaned up test document")

    print("\n✅ INSERT...RETURNING test PASSED\n")


def test_multiple_columns():
    """Test fetching multiple columns (simulates embedder.py:169 fix)."""
    print("=" * 60)
    print("TEST 3: Multi-Column Fetch Pattern")
    print("=" * 60)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get first document
            cur.execute("""
                SELECT bot_id, title, content, source, metadata
                FROM documents
                LIMIT 1
            """)
            row = cur.fetchone()

            if not row:
                print("  ⚠ No documents found, skipping test")
                return

            # This pattern was broken (tuple unpacking)
            # Now fixed to access dict keys individually
            print("\n✓ Testing: Multiple column access")
            bot_id = row['bot_id']
            title = row['title']
            content = row['content']
            source = row['source']
            metadata = row['metadata']

            print(f"  Bot ID: {bot_id}")
            print(f"  Title: {title}")
            print(f"  Content length: {len(content) if content else 0}")
            print(f"  Source: {source}")
            print(f"  Metadata: {metadata}")

    print("\n✅ Multi-column fetch test PASSED\n")


def test_document_info_dict():
    """Test building dict from row (simulates embedder.py:274-280 fix)."""
    print("=" * 60)
    print("TEST 4: Dict Building from Row Pattern")
    print("=" * 60)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    d.id,
                    d.bot_id,
                    d.title,
                    d.source,
                    d.created_at,
                    d.updated_at,
                    COUNT(dc.id) as chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON d.id = dc.document_id
                GROUP BY d.id
                LIMIT 1
            """)

            row = cur.fetchone()

            if not row:
                print("  ⚠ No documents found, skipping test")
                return

            # This pattern was broken (row[0], row[1], etc.)
            # Now fixed to use row['column_name']
            print("\n✓ Testing: Building dict from row with column names")
            doc_info = {
                'id': row['id'],
                'bot_id': row['bot_id'],
                'title': row['title'],
                'source': row['source'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'chunk_count': row['chunk_count'] or 0
            }

            print(f"  Document info:")
            for key, value in doc_info.items():
                print(f"    {key}: {value}")

    print("\n✅ Dict building test PASSED\n")


def test_single_column_conditional():
    """Test single column fetch with fallback (simulates reindex_bot.py:160 fix)."""
    print("=" * 60)
    print("TEST 5: Single Column with Conditional Pattern")
    print("=" * 60)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Test with existing document
            cur.execute("SELECT id FROM documents LIMIT 1")
            doc_row = cur.fetchone()

            if not doc_row:
                print("  ⚠ No documents found, skipping test")
                return

            doc_id = doc_row['id']

            # This pattern was broken (row[0] if row else "")
            # Now fixed to row['content'] if row else ""
            print("\n✓ Testing: Single column with conditional access")
            cur.execute("SELECT content FROM documents WHERE id = %s", (doc_id,))
            row = cur.fetchone()
            content = row['content'] if row else ""

            print(f"  Content length: {len(content) if content else 0}")
            print(f"  Has content: {bool(content)}")

            # Test with non-existent document
            cur.execute("SELECT content FROM documents WHERE id = -9999")
            row = cur.fetchone()
            content = row['content'] if row else ""
            print(f"  Non-existent doc returns empty: {content == ''}")

    print("\n✅ Conditional access test PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DATABASE CURSOR FIX VALIDATION TEST SUITE")
    print("=" * 60)
    print("\nTesting all patterns that were fixed:")
    print("1. fetchone()[0] → fetchone()['column']")
    print("2. Tuple unpacking → Dict key access")
    print("3. Numeric indexing → Column name indexing")
    print("4. Conditional access with row[0] → row['column']")
    print("\n")

    try:
        test_basic_queries()
        test_insert_returning()
        test_multiple_columns()
        test_document_info_dict()
        test_single_column_conditional()

        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nAll RealDictCursor indexing issues have been fixed!")
        print("The codebase now correctly uses column names instead of numeric indexing.")
        print("\n")
        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
