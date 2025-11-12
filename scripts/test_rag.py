#!/usr/bin/env python3
"""
Test RAG System

CLI tool for testing RAG search and retrieval.
Useful for debugging and evaluating knowledge base quality.

Usage:
    # Test a query
    python scripts/test_rag.py \\
        --bot_id keystone-landscaping \\
        --query "Do you offer retaining walls?"

    # List all documents
    python scripts/test_rag.py \\
        --bot_id keystone-landscaping \\
        --list

    # Test with custom parameters
    python scripts/test_rag.py \\
        --bot_id keystone-landscaping \\
        --query "What is your warranty?" \\
        --top_k 10 \\
        --threshold 0.5
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.rag import VoyageClient, RAGRetriever
from shared.database import DatabaseConnection


def list_documents(retriever, bot_id: str):
    """
    List all documents for a bot.

    Args:
        retriever: RAGRetriever instance
        bot_id: Bot identifier
    """
    print(f"\n{'=' * 70}")
    print(f"DOCUMENTS FOR BOT: {bot_id}")
    print(f"{'=' * 70}\n")

    documents = retriever.get_bot_documents(bot_id)

    if not documents:
        print("No documents found for this bot.")
        print("\nTo add documents, use:")
        print(f"  python scripts/add_document.py --bot_id {bot_id} --title \"...\" --file \"...\"")
        return

    print(f"Found {len(documents)} document(s):\n")

    for i, doc in enumerate(documents, 1):
        print(f"[{i}] {doc['title']}")
        print(f"    ID: {doc['id']}")
        print(f"    Source: {doc['source']}")
        print(f"    Chunks: {doc['chunk_count']}")
        print(f"    Tokens: ~{doc['total_tokens']}")
        print(f"    Created: {doc['created_at']}")
        print()

    total_chunks = sum(d['chunk_count'] for d in documents)
    total_tokens = sum(d['total_tokens'] for d in documents)

    print(f"{'=' * 70}")
    print(f"Total: {len(documents)} documents, {total_chunks} chunks, ~{total_tokens} tokens")
    print(f"{'=' * 70}")


def test_query(
    retriever,
    bot_id: str,
    query: str,
    top_k: int,
    threshold: float,
    max_tokens: int,
    verbose: bool
):
    """
    Test a RAG query.

    Args:
        retriever: RAGRetriever instance
        bot_id: Bot identifier
        query: Search query
        top_k: Number of results
        threshold: Similarity threshold
        max_tokens: Max context tokens
        verbose: Show verbose output
    """
    print(f"\n{'=' * 70}")
    print(f"RAG SEARCH TEST")
    print(f"{'=' * 70}\n")

    print(f"Bot ID: {bot_id}")
    print(f"Query: \"{query}\"")
    print(f"Parameters:")
    print(f"  • Top K: {top_k}")
    print(f"  • Similarity threshold: {threshold}")
    print(f"  • Max context tokens: {max_tokens}")

    print(f"\n{'-' * 70}")
    print(f"SEARCHING...")
    print(f"{'-' * 70}\n")

    try:
        # Perform search
        start_time = datetime.now()
        results = retriever.search(
            bot_id=bot_id,
            query=query,
            top_k=top_k,
            similarity_threshold=threshold
        )
        elapsed = (datetime.now() - start_time).total_seconds()

        if not results:
            print("⚠ No results found")
            print(f"\nPossible reasons:")
            print(f"  • No documents added to knowledge base")
            print(f"  • Similarity threshold too high ({threshold})")
            print(f"  • Query doesn't match document content")
            print(f"\nTry:")
            print(f"  • Lower threshold: --threshold 0.5")
            print(f"  • List documents: --list")
            print(f"  • Add documents: python scripts/add_document.py ...")
            return

        print(f"✓ Found {len(results)} result(s) in {elapsed:.2f}s\n")

        # Display results
        for i, result in enumerate(results, 1):
            sim_pct = result['similarity'] * 100
            print(f"[{i}] Similarity: {result['similarity']:.4f} ({sim_pct:.1f}%)")
            print(f"    Document: {result['document_title']}")
            print(f"    Source: {result['source']}")
            print(f"    Chunk: {result['chunk_index'] + 1}")
            print(f"    Tokens: {result['token_count']}")

            if verbose:
                print(f"    Chunk ID: {result['chunk_id']}")
                print(f"    Document ID: {result['document_id']}")

            print(f"\n    Content Preview:")
            content_preview = result['content'][:200]
            if len(result['content']) > 200:
                content_preview += "..."
            print(f"    \"{content_preview}\"\n")

        # Format context
        print(f"{'-' * 70}")
        print(f"FORMATTED CONTEXT (as sent to Claude)")
        print(f"{'-' * 70}\n")

        context = retriever.format_context(results, max_tokens=max_tokens)
        print(context)

        print(f"\n{'-' * 70}")

        # Context stats
        context_tokens = sum(r['token_count'] for r in results)
        print(f"\nContext Statistics:")
        print(f"  • Chunks used: {len(results)}")
        print(f"  • Total tokens: ~{context_tokens}")
        print(f"  • Avg similarity: {sum(r['similarity'] for r in results) / len(results):.4f}")
        print(f"  • Min similarity: {min(r['similarity'] for r in results):.4f}")
        print(f"  • Max similarity: {max(r['similarity'] for r in results):.4f}")

        if context_tokens > max_tokens:
            print(f"\n⚠ Warning: Context would be truncated (limit: {max_tokens} tokens)")

        print(f"\n{'=' * 70}")
        print(f"✓ TEST COMPLETE")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\n✗ ERROR during search: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Test RAG search and retrieval',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a simple query
  python scripts/test_rag.py \\
      --bot_id keystone-landscaping \\
      --query "Do you offer retaining walls?"

  # Test with custom parameters
  python scripts/test_rag.py \\
      --bot_id keystone-landscaping \\
      --query "What areas do you serve?" \\
      --top_k 10 \\
      --threshold 0.6

  # List all documents for a bot
  python scripts/test_rag.py \\
      --bot_id keystone-landscaping \\
      --list

  # Verbose output with low threshold
  python scripts/test_rag.py \\
      --bot_id keystone-landscaping \\
      --query "pricing" \\
      --threshold 0.4 \\
      --verbose
        """
    )

    # Required (unless using --list)
    parser.add_argument(
        '--bot_id',
        required=True,
        help='Bot identifier (e.g., keystone-landscaping)'
    )

    # Mutually exclusive: query or list
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--query',
        help='Search query to test'
    )
    group.add_argument(
        '--list',
        action='store_true',
        help='List all documents for the bot'
    )

    # Optional parameters
    parser.add_argument(
        '--top_k',
        type=int,
        default=5,
        help='Number of results to return (default: 5)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.7,
        help='Minimum similarity threshold 0-1 (default: 0.7)'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=2000,
        help='Maximum context tokens (default: 2000)'
    )
    parser.add_argument(
        '--model',
        default='voyage-3-lite',
        help='Voyage AI model (default: voyage-3-lite)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    try:
        # Initialize components
        if args.verbose:
            print("Initializing RAG components...")

        voyage_client = VoyageClient(model=args.model)
        db = DatabaseConnection()
        retriever = RAGRetriever(voyage_client, db)

        if args.verbose:
            print(f"✓ Initialized with model: {args.model}\n")

        # Handle list or query
        if args.list:
            list_documents(retriever, args.bot_id)
        else:
            test_query(
                retriever=retriever,
                bot_id=args.bot_id,
                query=args.query,
                top_k=args.top_k,
                threshold=args.threshold,
                max_tokens=args.max_tokens,
                verbose=args.verbose
            )

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
