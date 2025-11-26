#!/usr/bin/env python3
"""
Add Document to Bot Knowledge Base

CLI tool for adding documents to a bot's RAG knowledge base.
Handles chunking, embedding generation, and storage.

Usage:
    python scripts/add_document.py \\
        --bot_id keystone-landscaping \\
        --title "Services Overview" \\
        --file path/to/document.txt \\
        --source manual_upload

Dependencies:
    - Voyage AI API key in .env
    - PostgreSQL with pgvector
    - RAG tables created (see migrations/003_rag_tables.sql)
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.rag import VoyageClient, TextChunker, DocumentEmbedder
from shared.database import DatabaseConnection


def validate_file(file_path: str) -> str:
    """
    Validate that file exists and is readable.

    Args:
        file_path: Path to file

    Returns:
        Absolute path to file

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    if not os.access(path, os.R_OK):
        raise PermissionError(f"Cannot read file: {file_path}")

    return str(path)


def read_file_content(file_path: str) -> str:
    """
    Read file content.

    Args:
        file_path: Path to file

    Returns:
        File content as string

    Raises:
        UnicodeDecodeError: If file is not valid text
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            raise ValueError("File is empty")

        return content

    except UnicodeDecodeError:
        raise ValueError(
            f"File appears to be binary or not UTF-8 encoded: {file_path}\n"
            "Only text files are supported."
        )


def parse_metadata(metadata_str: str) -> dict:
    """
    Parse metadata JSON string.

    Args:
        metadata_str: JSON string

    Returns:
        Dictionary

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        metadata = json.loads(metadata_str)

        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a JSON object")

        return metadata

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in metadata: {e}")


def get_available_bot_ids(conn) -> list:
    """
    Get list of available bot_id strings from database.

    Args:
        conn: Database connection

    Returns:
        List of bot_id strings
    """
    with conn.cursor() as cur:
        cur.execute("SELECT bot_id FROM bots ORDER BY bot_id")
        return [row['bot_id'] for row in cur.fetchall()]


def get_bot_numeric_id(bot_id_string: str, conn) -> int:
    """
    Look up numeric bot.id from string bots.bot_id.

    Args:
        bot_id_string: String bot identifier (e.g., 'therapist', 'keystone-landscaping')
        conn: Database connection

    Returns:
        Numeric bot ID (bots.id)

    Raises:
        ValueError: If bot not found in database
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM bots WHERE bot_id = %s",
            (bot_id_string,)
        )
        result = cur.fetchone()

        if not result:
            available_bots = get_available_bot_ids(conn)
            raise ValueError(
                f"Bot '{bot_id_string}' not found in database. "
                f"Available bots: {', '.join(available_bots)}"
            )

        return result['id']


def main():
    parser = argparse.ArgumentParser(
        description='Add a document to a bot\'s knowledge base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a simple text file
  python scripts/add_document.py \\
      --bot_id keystone-landscaping \\
      --title "Services Overview" \\
      --file knowledge_base/services.txt

  # Add with custom source and metadata
  python scripts/add_document.py \\
      --bot_id keystone-landscaping \\
      --title "Pricing Guide 2024" \\
      --file docs/pricing.txt \\
      --source website \\
      --metadata '{"category": "pricing", "year": 2024}'

  # Use custom chunking parameters
  python scripts/add_document.py \\
      --bot_id keystone-landscaping \\
      --title "Technical Manual" \\
      --file manuals/tech.txt \\
      --chunk-size 1000 \\
      --chunk-overlap 200
        """
    )

    # Required arguments
    parser.add_argument(
        '--bot_id',
        required=True,
        help='Bot identifier (e.g., keystone-landscaping)'
    )
    parser.add_argument(
        '--title',
        required=True,
        help='Document title'
    )
    parser.add_argument(
        '--file',
        required=True,
        help='Path to document file (text file)'
    )

    # Optional arguments
    parser.add_argument(
        '--source',
        default='manual_upload',
        help='Source identifier (default: manual_upload)'
    )
    parser.add_argument(
        '--metadata',
        default='{}',
        help='JSON metadata (default: {})'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=800,
        help='Target chunk size in tokens (default: 800)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=150,
        help='Overlap between chunks in tokens (default: 150)'
    )
    parser.add_argument(
        '--model',
        default='voyage-3-lite',
        help='Voyage AI model (default: voyage-3-lite)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress'
    )

    args = parser.parse_args()

    # Print header
    print("=" * 70)
    print("ADD DOCUMENT TO KNOWLEDGE BASE")
    print("=" * 70)

    try:
        # Validate file
        print(f"\n1. Validating file...")
        file_path = validate_file(args.file)
        print(f"   ✓ File exists: {file_path}")

        # Read content
        print(f"\n2. Reading file content...")
        content = read_file_content(file_path)
        print(f"   ✓ Read {len(content)} characters")

        # Parse metadata
        print(f"\n3. Parsing metadata...")
        metadata = parse_metadata(args.metadata)
        if metadata:
            print(f"   ✓ Metadata: {json.dumps(metadata, indent=4)}")
        else:
            print(f"   ✓ No metadata provided")

        # Add file_name to metadata
        metadata['file_name'] = Path(file_path).name

        # Look up numeric bot ID
        print(f"\n4. Looking up bot in database...")
        db = DatabaseConnection()

        with db.get_connection() as conn:
            try:
                numeric_bot_id = get_bot_numeric_id(args.bot_id, conn)
                print(f"   ✓ Bot found: '{args.bot_id}' (numeric ID: {numeric_bot_id})")
            except ValueError as e:
                print(f"\n✗ ERROR: {e}")
                return 1

        if args.dry_run:
            print(f"\n5. DRY RUN - Would process document with:")
            print(f"   Bot ID: '{args.bot_id}' (numeric ID: {numeric_bot_id})")
            print(f"   Title: {args.title}")
            print(f"   Source: {args.source}")
            print(f"   Chunk size: {args.chunk_size} tokens")
            print(f"   Chunk overlap: {args.chunk_overlap} tokens")
            print(f"   Model: {args.model}")

            # Estimate chunks
            chunker = TextChunker(
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
            chunks = chunker.chunk_text(content, metadata=metadata)
            print(f"\n   Would create {len(chunks)} chunks")
            total_tokens = sum(c['token_count'] for c in chunks)
            print(f"   Total tokens: ~{total_tokens}")
            print(f"\n✓ Dry run complete (no changes made)")
            return 0

        # Initialize RAG components
        print(f"\n5. Initializing RAG components...")
        voyage_client = VoyageClient(model=args.model)
        print(f"   ✓ Voyage client initialized (model: {args.model})")

        chunker = TextChunker(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        print(f"   ✓ Text chunker initialized")

        embedder = DocumentEmbedder(voyage_client, chunker, db)
        print(f"   ✓ Document embedder initialized")

        # Process document
        print(f"\n6. Processing document...")
        print(f"   Bot ID: '{args.bot_id}' (numeric ID: {numeric_bot_id})")
        print(f"   Title: {args.title}")
        print(f"   Source: {args.source}")

        doc_id = embedder.process_document(
            bot_id=numeric_bot_id,
            title=args.title,
            content=content,
            source=args.source,
            metadata=metadata
        )

        print(f"\n   ✓ Document created with ID: {doc_id}")

        # Get document info
        doc_info = embedder.get_document_info(doc_id)

        print(f"\n7. Document successfully added!")
        print(f"   Document ID: {doc_info['id']}")
        print(f"   Chunks created: {doc_info['chunk_count']}")
        print(f"   Total tokens: ~{doc_info['total_tokens']}")
        print(f"   Created at: {doc_info['created_at']}")

        print(f"\n" + "=" * 70)
        print(f"✓ SUCCESS - Document added to {args.bot_id} knowledge base")
        print(f"=" * 70)

        # Next steps
        print(f"\nNext steps:")
        print(f"  • Test search: python scripts/test_rag.py --bot_id {args.bot_id}")
        print(f"  • View document: Check database table 'documents' (id={doc_id})")

        return 0

    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {e}")
        return 1

    except ValueError as e:
        print(f"\n✗ ERROR: {e}")
        return 1

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
