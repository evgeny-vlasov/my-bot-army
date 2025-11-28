#!/usr/bin/env python3
"""
Reindex Bot Documents

CLI tool for regenerating embeddings for all documents of a bot.

Use cases:
- Switching embedding models (voyage-3-lite → voyage-3)
- Changing chunking parameters
- Fixing corrupted embeddings
- Updating to newer model versions

WARNING: This is a destructive operation that deletes and regenerates
all chunks and embeddings for the bot's documents.

Usage:
    python scripts/reindex_bot.py --bot_id keystone-landscaping

    # With custom parameters
    python scripts/reindex_bot.py \\
        --bot_id keystone-landscaping \\
        --model voyage-3 \\
        --chunk-size 1000 \\
        --chunk-overlap 200
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.rag import VoyageClient, TextChunker, DocumentEmbedder, RAGRetriever
from shared.database import DatabaseConnection


def confirm_reindex(bot_id: str, document_count: int) -> bool:
    """
    Ask user to confirm reindexing operation.

    Args:
        bot_id: Bot identifier
        document_count: Number of documents to reindex

    Returns:
        True if user confirms, False otherwise
    """
    print(f"\n{'!' * 70}")
    print(f"WARNING: DESTRUCTIVE OPERATION")
    print(f"{'!' * 70}\n")

    print(f"This will:")
    print(f"  • Delete all existing chunks for {document_count} document(s)")
    print(f"  • Regenerate chunks with new parameters")
    print(f"  • Generate new embeddings (API calls = costs)")
    print(f"  • Replace all embeddings in database")

    print(f"\nBot: {bot_id}")
    print(f"Documents: {document_count}")

    print(f"\nThis operation cannot be undone!")

    response = input(f"\nProceed with reindexing? (yes/no): ").strip().lower()

    return response in ('yes', 'y')


def reindex_bot(
    bot_id: str,
    voyage_model: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int,
    verbose: bool,
    dry_run: bool
):
    """
    Reindex all documents for a bot.

    Args:
        bot_id: Bot identifier
        voyage_model: Voyage AI model to use
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks
        min_chunk_size: Minimum chunk size
        verbose: Show detailed output
        dry_run: Show what would be done without doing it
    """
    print(f"\n{'=' * 70}")
    print(f"BOT REINDEXING")
    print(f"{'=' * 70}\n")

    print(f"Bot ID: {bot_id}")
    print(f"Embedding model: {voyage_model}")
    print(f"Chunk size: {chunk_size} tokens")
    print(f"Chunk overlap: {chunk_overlap} tokens")
    print(f"Min chunk size: {min_chunk_size} tokens")

    try:
        # Initialize components
        if verbose:
            print(f"\nInitializing components...")

        voyage_client = VoyageClient(model=voyage_model)
        chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size
        )
        db = DatabaseConnection()
        embedder = DocumentEmbedder(voyage_client, chunker, db)
        retriever = RAGRetriever(voyage_client, db)

        if verbose:
            print(f"✓ Components initialized\n")

        # Get documents for bot
        print(f"{'=' * 70}")
        print(f"FETCHING DOCUMENTS")
        print(f"{'=' * 70}\n")

        documents = retriever.get_bot_documents(bot_id)

        if not documents:
            print(f"No documents found for bot '{bot_id}'")
            print(f"\nTo add documents, use:")
            print(f"  python scripts/add_document.py --bot_id {bot_id} ...")
            return 0

        print(f"Found {len(documents)} document(s):\n")

        for i, doc in enumerate(documents, 1):
            print(f"[{i}] {doc['title']}")
            print(f"    Current chunks: {doc['chunk_count']}")
            print(f"    Current tokens: ~{doc['total_tokens']}")

        total_chunks = sum(d['chunk_count'] for d in documents)
        total_tokens = sum(d['total_tokens'] for d in documents)

        print(f"\nCurrent totals: {total_chunks} chunks, ~{total_tokens} tokens")

        # Dry run - estimate new chunks
        if dry_run:
            print(f"\n{'=' * 70}")
            print(f"DRY RUN - ESTIMATING NEW CHUNKS")
            print(f"{'=' * 70}\n")

            for doc in documents:
                # Get document content
                with db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT content FROM documents WHERE id = %s",
                            (doc['id'],)
                        )
                        row = cur.fetchone()
                        content = row['content'] if row else ""

                # Estimate new chunks
                chunks = chunker.chunk_text(content)
                new_tokens = sum(c['token_count'] for c in chunks)

                print(f"Document: {doc['title']}")
                print(f"  Old: {doc['chunk_count']} chunks, ~{doc['total_tokens']} tokens")
                print(f"  New: {len(chunks)} chunks, ~{new_tokens} tokens")
                print()

            print(f"✓ Dry run complete (no changes made)")
            return 0

        # Confirm before proceeding
        if not confirm_reindex(bot_id, len(documents)):
            print(f"\nReindexing cancelled by user")
            return 0

        # Reindex each document
        print(f"\n{'=' * 70}")
        print(f"REINDEXING DOCUMENTS")
        print(f"{'=' * 70}\n")

        start_time = datetime.now()
        success_count = 0
        total_new_chunks = 0

        for i, doc in enumerate(documents, 1):
            print(f"[{i}/{len(documents)}] Reindexing: {doc['title']}")

            try:
                # Reindex document
                chunk_count = embedder.reindex_document(doc['id'])

                print(f"  ✓ Created {chunk_count} chunks")
                success_count += 1
                total_new_chunks += chunk_count

            except Exception as e:
                print(f"  ✗ Failed: {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()

        elapsed = (datetime.now() - start_time).total_seconds()

        # Summary
        print(f"\n{'=' * 70}")
        print(f"REINDEXING COMPLETE")
        print(f"{'=' * 70}\n")

        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Documents processed: {success_count}/{len(documents)}")
        print(f"Total new chunks: {total_new_chunks}")
        print(f"Old chunks: {total_chunks}")
        print(f"Difference: {total_new_chunks - total_chunks:+d} chunks")

        if success_count < len(documents):
            print(f"\n⚠ Warning: {len(documents) - success_count} document(s) failed")
            return 1

        print(f"\n✓ All documents reindexed successfully!")

        # Suggest next step
        print(f"\nNext steps:")
        print(f"  • Test search: python scripts/test_rag.py --bot_id {bot_id}")

        return 0

    except KeyboardInterrupt:
        print(f"\n\nReindexing interrupted by user")
        return 130

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Reindex all documents for a bot (regenerate embeddings)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reindex with default settings
  python scripts/reindex_bot.py --bot_id keystone-landscaping

  # Reindex with different model
  python scripts/reindex_bot.py \\
      --bot_id keystone-landscaping \\
      --model voyage-3

  # Preview what would change (dry run)
  python scripts/reindex_bot.py \\
      --bot_id keystone-landscaping \\
      --chunk-size 1000 \\
      --dry-run

  # Reindex with custom chunking
  python scripts/reindex_bot.py \\
      --bot_id keystone-landscaping \\
      --chunk-size 600 \\
      --chunk-overlap 100 \\
      --verbose

WARNING: This operation:
  • Deletes all existing chunks and embeddings
  • Makes API calls to regenerate embeddings (costs money)
  • Cannot be undone
  • Requires user confirmation (unless --yes flag used)
        """
    )

    parser.add_argument(
        '--bot_id',
        required=True,
        help='Bot identifier (e.g., keystone-landscaping)'
    )
    parser.add_argument(
        '--model',
        default='voyage-3-lite',
        help='Voyage AI model (default: voyage-3-lite)'
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
        '--min-chunk-size',
        type=int,
        default=100,
        help='Minimum chunk size in tokens (default: 100)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt (dangerous!)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    # Override confirmation if --yes flag
    if args.yes:
        # Monkey patch the confirm function
        global confirm_reindex
        confirm_reindex = lambda bot_id, doc_count: True

    try:
        return reindex_bot(
            bot_id=args.bot_id,
            voyage_model=args.model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            min_chunk_size=args.min_chunk_size,
            verbose=args.verbose,
            dry_run=args.dry_run
        )

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
