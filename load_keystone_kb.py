#!/usr/bin/env python3
"""
Load Keystone Hardscapes Knowledge Base

This script loads the Keystone Hardscapes knowledge base documents into
the database and processes them with RAG embeddings.

Files to load:
- keystone_company.txt: Company information and process
- keystone_faq.txt: Frequently asked questions
- knowledge_base/keystone_services.txt: Services, pricing, technical details (if exists)

Usage:
    python3 load_keystone_kb.py

Environment:
    VOYAGE_API_KEY must be set
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from shared.database import get_db_connection
from shared.rag import process_document

# Configuration
BOT_ID = 1  # Keystone Hardscapes bot
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

# Knowledge base files
KB_FILES = [
    {
        "path": "/opt/bot-farm/keystone_company.txt",
        "title": "Keystone Hardscapes - Company Information",
        "source": "knowledge_base"
    },
    {
        "path": "/opt/bot-farm/keystone_faq.txt",
        "title": "Keystone Hardscapes - FAQ",
        "source": "knowledge_base"
    },
]

# Check for knowledge_base directory
kb_dir = Path("/opt/bot-farm/knowledge_base")
if kb_dir.exists():
    for kb_file in kb_dir.glob("*.txt"):
        KB_FILES.append({
            "path": str(kb_file),
            "title": f"Keystone Hardscapes - {kb_file.stem.replace('_', ' ').title()}",
            "source": "knowledge_base"
        })


def main():
    """Load all knowledge base documents."""
    
    # Validate API key
    if not VOYAGE_API_KEY:
        print("ERROR: VOYAGE_API_KEY environment variable not set")
        print("Set it with: export VOYAGE_API_KEY='your-api-key'")
        sys.exit(1)
    
    print("=" * 70)
    print("KEYSTONE HARDSCAPES KNOWLEDGE BASE LOADER")
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
    
    total_chunks = 0
    successful_docs = 0
    
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
        
        # Insert document into database
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO documents (bot_id, title, content, source, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        bot_id_int,
                        file_info["title"],
                        content,
                        file_info["source"],
                        '{"file_name": "' + file_path.name + '"}'
                    ))
                    document_id = cur.fetchone()['id']

            print(f"      Document ID: {document_id}")
        except Exception as e:
            print(f"      ✗ ERROR inserting document: {e}")
            print()
            continue
        
        # Process document with RAG
        try:
            with get_db_connection() as conn:
                chunk_count = process_document(
                    conn=conn,
                    bot_id=BOT_ID,
                    document_id=document_id,
                    document_text=content,
                    voyage_api_key=VOYAGE_API_KEY,
                    chunk_size=800,
                    overlap=200
                )
            
            print(f"      ✓ Created {chunk_count} chunks")
            total_chunks += chunk_count
            successful_docs += 1
        except Exception as e:
            print(f"      ✗ ERROR processing document: {e}")
        
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
        print("  1. Test RAG queries: python3 test_keystone_rag.py")
        print("  2. Update bot system prompt to use RAG")
    else:
        print("✗ No documents were successfully processed")
        sys.exit(1)


if __name__ == "__main__":
    main()
