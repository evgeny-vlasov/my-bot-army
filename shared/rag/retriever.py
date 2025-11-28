"""
RAG Retriever

Searches for relevant document chunks using vector similarity
and formats them as context for Claude.

This module provides the retrieval component of RAG, taking
user queries and finding the most relevant knowledge base content.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Retrieves relevant document chunks for RAG.

    Workflow:
    1. Embed the user's query using Voyage AI
    2. Search for similar chunks using pgvector cosine similarity
    3. Filter by similarity threshold
    4. Return top K results with metadata

    Example:
        from shared.rag import VoyageClient, RAGRetriever
        from shared.database import DatabaseConnection

        voyage = VoyageClient()
        db = DatabaseConnection()
        retriever = RAGRetriever(voyage, db)

        # Search for relevant chunks
        results = retriever.search(
            bot_id="keystone-landscaping",
            query="Do you offer retaining walls?",
            top_k=5,
            similarity_threshold=0.7
        )

        # Format as context for Claude
        context = retriever.format_context(results)
    """

    def __init__(self, voyage_client, db_connection):
        """
        Initialize RAG retriever.

        Args:
            voyage_client: VoyageClient instance for query embeddings
            db_connection: Database connection object (from shared.database)
        """
        self.voyage_client = voyage_client
        self.db = db_connection

        logger.info("Initialized RAGRetriever")

    def search(
        self,
        bot_id: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search for relevant document chunks.

        Args:
            bot_id: Bot identifier (e.g., "keystone-landscaping")
            query: Search query text
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of result dictionaries containing:
                - chunk_id: Database ID of chunk
                - document_id: Parent document ID
                - document_title: Document title
                - chunk_index: Position in document
                - content: Chunk text
                - similarity: Similarity score (0-1)
                - source: Document source
                - token_count: Approximate tokens
        """
        try:
            logger.info(
                f"Searching for: '{query[:50]}...' (bot={bot_id}, "
                f"top_k={top_k}, threshold={similarity_threshold})"
            )

            # Step 1: Generate query embedding
            query_embedding = self.voyage_client.embed_query(query)

            logger.debug(f"Generated query embedding ({len(query_embedding)} dims)")

            # Step 2: Vector similarity search
            results = self._vector_search(
                bot_id=bot_id,
                query_embedding=query_embedding,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            logger.info(f"Found {len(results)} relevant chunks")

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def format_context(
        self,
        chunks: List[Dict],
        max_tokens: int = 2000,
        include_sources: bool = True
    ) -> str:
        """
        Format retrieved chunks as context string for Claude.

        Args:
            chunks: List of chunk dictionaries from search()
            max_tokens: Maximum total tokens to include
            include_sources: Whether to add source citations

        Returns:
            Formatted context string

        Format:
            RELEVANT CONTEXT:

            [Source: Document Title]
            "Chunk content here..."

            [Source: Another Document, Section 2]
            "More relevant content..."
        """
        if not chunks:
            return ""

        context_parts = ["RELEVANT CONTEXT:\n"]
        total_tokens = 0

        for i, chunk in enumerate(chunks):
            chunk_tokens = chunk.get('token_count', 0)

            # Stop if we'd exceed max tokens
            if total_tokens + chunk_tokens > max_tokens:
                logger.debug(
                    f"Truncating context at chunk {i} "
                    f"(would exceed {max_tokens} tokens)"
                )
                break

            # Add source citation if enabled
            if include_sources:
                doc_title = chunk.get('document_title', 'Unknown')
                chunk_index = chunk.get('chunk_index', '')
                source = chunk.get('source', '')

                source_line = f"[Source: {doc_title}"
                if chunk_index is not None and chunk_index > 0:
                    source_line += f", Part {chunk_index + 1}"
                if source:
                    source_line += f" ({source})"
                source_line += "]"

                context_parts.append(f"\n{source_line}")

            # Add chunk content (quoted)
            content = chunk.get('content', '').strip()
            context_parts.append(f'"{content}"\n')

            total_tokens += chunk_tokens

        result = '\n'.join(context_parts)

        logger.debug(
            f"Formatted context: {len(chunks)} chunks, "
            f"~{total_tokens} tokens"
        )

        return result

    def get_context_for_query(
        self,
        bot_id: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        max_tokens: int = 2000
    ) -> tuple[str, List[Dict]]:
        """
        Convenience method that combines search + format.

        Args:
            bot_id: Bot identifier
            query: Search query
            top_k: Maximum results
            similarity_threshold: Minimum similarity
            max_tokens: Maximum context tokens

        Returns:
            Tuple of (formatted_context, chunks_used)
        """
        # Search for relevant chunks
        chunks = self.search(
            bot_id=bot_id,
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

        # Format as context
        context = self.format_context(chunks, max_tokens=max_tokens)

        return context, chunks

    def _vector_search(
        self,
        bot_id: str,
        query_embedding: List[float],
        top_k: int,
        similarity_threshold: float
    ) -> List[Dict]:
        """
        Perform vector similarity search in database.

        Args:
            bot_id: Bot identifier
            query_embedding: Query embedding vector
            top_k: Maximum results
            similarity_threshold: Minimum similarity (0-1)

        Returns:
            List of result dictionaries
        """
        # Convert embedding to pgvector format
        embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

        # Calculate distance threshold from similarity threshold
        # cosine similarity = 1 - cosine distance
        # So: distance <= (1 - similarity)
        distance_threshold = 1 - similarity_threshold

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # First convert bot_id string to integer ID
                cur.execute("SELECT id FROM bots WHERE bot_id = %s", (bot_id,))
                bot_row = cur.fetchone()
                if not bot_row:
                    raise ValueError(f"Bot {bot_id} not found")
                bot_id_int = bot_row['id']  # RealDictCursor always returns dict

                # Vector similarity query using <=> (cosine distance) operator
                cur.execute("""
                    SELECT
                        dc.id as chunk_id,
                        dc.document_id,
                        d.title as document_title,
                        dc.chunk_index,
                        dc.chunk_text,
                        d.source,
                        1 - (dc.embedding <=> %s::vector) as similarity
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE d.bot_id = %s
                      AND dc.embedding IS NOT NULL
                      AND (dc.embedding <=> %s::vector) <= %s
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s
                """, (
                    embedding_str,
                    bot_id_int,
                    embedding_str,
                    distance_threshold,
                    embedding_str,
                    top_k
                ))

                rows = cur.fetchall()

                # Convert rows to dictionaries (using RealDictCursor)
                results = []
                for row in rows:
                    # Estimate token count from chunk text (roughly 4 chars per token)
                    content = row['chunk_text']
                    estimated_tokens = len(content) // 4 if content else 0

                    result = {
                        'chunk_id': row['chunk_id'],
                        'document_id': row['document_id'],
                        'document_title': row['document_title'] or 'Untitled',
                        'chunk_index': row['chunk_index'],
                        'content': content,
                        'token_count': estimated_tokens,
                        'source': row['source'] or '',
                        'similarity': float(row['similarity']) if row.get('similarity') is not None else 0.0
                    }
                    results.append(result)

        logger.debug(f"Vector search returned {len(results)} results")

        return results

    def get_bot_documents(self, bot_id: str) -> List[Dict]:
        """
        Get all documents for a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            List of document dictionaries
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # First convert bot_id string to integer ID
                cur.execute("SELECT id FROM bots WHERE bot_id = %s", (bot_id,))
                bot_row = cur.fetchone()
                if not bot_row:
                    raise ValueError(f"Bot {bot_id} not found")
                bot_id_int = bot_row['id']  # RealDictCursor always returns dict

                cur.execute("""
                    SELECT
                        d.id,
                        d.bot_id,
                        d.title,
                        d.source,
                        d.created_at,
                        COUNT(dc.id) as chunk_count,
                        SUM(LENGTH(dc.chunk_text) / 4) as total_tokens
                    FROM documents d
                    LEFT JOIN document_chunks dc ON d.id = dc.document_id
                    WHERE d.bot_id = %s
                    GROUP BY d.id
                    ORDER BY d.created_at DESC
                """, (bot_id_int,))

                rows = cur.fetchall()

                documents = []
                for row in rows:
                    doc = {
                        'id': row['id'],
                        'bot_id': row['bot_id'],
                        'title': row['title'],
                        'source': row['source'],
                        'created_at': row['created_at'],
                        'chunk_count': row['chunk_count'] or 0,
                        'total_tokens': int(row['total_tokens'] or 0)
                    }
                    documents.append(doc)

        return documents


# For testing
def test_retriever():
    """Test RAG retriever with sample query."""
    from shared.rag import VoyageClient, RAGRetriever
    from shared.database import DatabaseConnection

    # Initialize
    voyage = VoyageClient()
    db = DatabaseConnection()
    retriever = RAGRetriever(voyage, db)

    # Test search
    bot_id = "keystone-landscaping"

    # Check if bot has documents
    documents = retriever.get_bot_documents(bot_id)
    print(f"Bot '{bot_id}' has {len(documents)} documents")

    if not documents:
        print("No documents found. Add some documents first using add_document.py")
        return

    # Test query
    query = "What services do you offer?"
    results = retriever.search(
        bot_id=bot_id,
        query=query,
        top_k=3,
        similarity_threshold=0.5  # Lower threshold for testing
    )

    print(f"\nSearch results for: '{query}'")
    print(f"Found {len(results)} results\n")

    for i, result in enumerate(results, 1):
        print(f"[{i}] Similarity: {result['similarity']:.3f}")
        print(f"    Source: {result['document_title']}")
        print(f"    Content: {result['content'][:100]}...")
        print()

    # Test context formatting
    if results:
        context = retriever.format_context(results, max_tokens=500)
        print("=" * 60)
        print("FORMATTED CONTEXT:")
        print("=" * 60)
        print(context)

    print("\n✓ Retriever test complete!")


if __name__ == "__main__":
    test_retriever()
