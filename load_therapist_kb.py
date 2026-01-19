#!/usr/bin/env python3
"""
Load Therapist Bot Knowledge Base

This script loads the Therapist knowledge base documents into
the database and processes them with RAG embeddings.

Files to load:
- bots/therapist/knowledge_base/insurance_and_fees.txt
- bots/therapist/knowledge_base/services_overview.txt
- bots/therapist/knowledge_base/getting_started.txt

Usage:
    python3 load_therapist_kb.py

Environment:
    VOYAGE_API_KEY must be set
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db_connection, DatabaseConnection
from shared.rag import VoyageClient, TextChunker, DocumentEmbedder

# Configuration
BOT_ID = 2  # Therapist bot
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

# Initialize RAG components
voyage_client = VoyageClient(api_key=VOYAGE_API_KEY, model="voyage-3-lite")
chunker = TextChunker(chunk_size=300, chunk_overlap=50)

# Knowledge base files
KB_DIR = Path("/opt/bot-farm/bots/therapist/knowledge_base")
KB_FILES = [
    {
        "path": KB_DIR / "insurance_and_fees.txt",
        "title": "Insurance, Fees, and Payment",
        "source": "knowledge_base"
    },
    {
        "path": KB_DIR / "services_overview.txt",
        "title": "Psychotherapy Services",
        "source": "knowledge_base"
    },
    {
        "path": KB_DIR / "getting_started.txt",
        "title": "Getting Started with Psychotherapy",
        "source": "knowledge_base"
    },
    {
        "path": KB_DIR / "faq.txt",
        "title": "Frequently Asked Questions",
        "source": "knowledge_base"
    },
]


def main():
    """Load all knowledge base documents."""

    # Validate API key
    if not VOYAGE_API_KEY:
        print("ERROR: VOYAGE_API_KEY environment variable not set")
        print("Set it with: export VOYAGE_API_KEY='your-api-key'")
        sys.exit(1)

    print("=" * 70)
    print("THERAPIST BOT KNOWLEDGE BASE LOADER")
    print("=" * 70)
    print()

    # Check bot exists
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, bot_id, bot_name FROM bots WHERE id = %s", (BOT_ID,))
            bot = cur.fetchone()

            if not bot:
                print(f"ERROR: Bot with id={BOT_ID} not found in database")
                sys.exit(1)

            bot_id_int = bot['id']
            bot_id_str = bot['bot_id']
            bot_name = bot['bot_name']

            print(f"Bot: {bot_name} ({bot_id_str})")
            print()

            # Delete existing documents and chunks for this bot
            print("Deleting existing knowledge base...")
            cur.execute("DELETE FROM document_chunks WHERE document_id IN (SELECT id FROM documents WHERE bot_id = %s)", (bot_id_int,))
            deleted_chunks = cur.rowcount
            cur.execute("DELETE FROM documents WHERE bot_id = %s", (bot_id_int,))
            deleted_docs = cur.rowcount
            print(f"  Deleted {deleted_docs} documents and {deleted_chunks} chunks")
            print()

    total_chunks = 0
    successful_docs = 0

    # Initialize embedder with DatabaseConnection wrapper
    db = DatabaseConnection()
    embedder = DocumentEmbedder(voyage_client, chunker, db)

    # Process each file
    for i, file_info in enumerate(KB_FILES, 1):
        file_path = Path(file_info["path"])

        print(f"[{i}/{len(KB_FILES)}] Processing: {file_path.name}")
        print(f"      Title: {file_info['title']}")

        # Check file exists
        if not file_path.exists():
            print(f"      ⚠ SKIP: File not found")
            print()
            continue

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"      ✗ ERROR reading file: {e}")
            print()
            continue

        print(f"      Size: {len(content)} characters")

        # Process document with RAG (creates document and chunks)
        try:
            document_id = embedder.process_document(
                bot_id=bot_id_int,
                title=file_info["title"],
                content=content,
                source=file_info["source"],
                metadata={"file_name": file_path.name}
            )

            print(f"      Document ID: {document_id}")

            # Get chunk count
            info = embedder.get_document_info(document_id)
            chunk_count = info['chunk_count'] if info else 0

            print(f"      ✓ Created {chunk_count} chunks")
            total_chunks += chunk_count
            successful_docs += 1
        except Exception as e:
            print(f"      ✗ ERROR processing document: {e}")
            import traceback
            traceback.print_exc()

        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {successful_docs}/{len(KB_FILES)}")
    print(f"Total chunks created: {total_chunks}")
    print()

    if successful_docs > 0:
        print("✓ Knowledge base loaded successfully!")
        print()
        print("Next steps:")
        print("  1. Restart the service: sudo systemctl restart bot-therapist.service")
        print("  2. Test the bot with updated content")
    else:
        print("✗ No documents were successfully processed")
        sys.exit(1)


if __name__ == "__main__":
    main()
