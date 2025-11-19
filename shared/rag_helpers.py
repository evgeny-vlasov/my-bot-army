"""
RAG Helper Functions

Provides simple functional wrappers around the OOP RAG components for
convenient use in scripts and applications.

These helpers combine VoyageClient, TextChunker, DocumentEmbedder, and
RAGRetriever into easy-to-use functions that match the interface expected
by the test suite.

Usage:
    from shared.rag import process_document, rag_query
    from shared.database import get_db_connection

    # Process a document
    with get_db_connection() as conn:
        chunk_count = process_document(
            conn=conn,
            bot_id=1,
            document_id=123,
            document_text="Your document content here...",
            voyage_api_key="your-api-key",
            chunk_size=800,
            overlap=200
        )

    # Query with RAG
    with get_db_connection() as conn:
        context = rag_query(
            conn=conn,
            bot_id=1,
            user_query="What services do you offer?",
            voyage_api_key="your-api-key",
            top_k=3
        )
"""

import logging
import json
from typing import Optional

from .voyage_client import VoyageClient
from .chunker import TextChunker
from .embedder import DocumentEmbedder
from .retriever import RAGRetriever

logger = logging.getLogger(__name__)


class _DatabaseConnectionWrapper:
    """
    Wrapper to adapt psycopg2 connection to match the interface expected
    by the OOP components (which expect a connection with get_connection()).
    """

    def __init__(self, conn):
        """Initialize with a raw psycopg2 connection."""
        self._conn = conn

    def get_connection(self):
        """Return a context manager that yields the connection."""
        class ConnectionContext:
            def __init__(self, conn):
                self.conn = conn

            def __enter__(self):
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                # Don't close the connection - let the caller manage it
                pass

        return ConnectionContext(self._conn)


def process_document(
    conn,
    bot_id: int,
    document_id: int,
    document_text: str,
    voyage_api_key: str,
    chunk_size: int = 800,
    overlap: int = 200
) -> int:
    """
    Process a document: chunk it, generate embeddings, and store in database.

    This is a high-level function that wraps the OOP components (VoyageClient,
    TextChunker, DocumentEmbedder) into a single convenient call.

    The function assumes the document record already exists in the database
    with the given document_id. It will:
    1. Retrieve the document metadata from the database
    2. Chunk the document text using the specified parameters
    3. Generate embeddings for each chunk using Voyage AI
    4. Store the chunks and embeddings in document_chunks table

    Args:
        conn: psycopg2 database connection object
        bot_id: ID of the bot that owns this document (integer)
        document_id: ID of the document to process (must exist in documents table)
        document_text: Full text content of the document
        voyage_api_key: Voyage AI API key for generating embeddings
        chunk_size: Target size for each chunk in tokens (default: 800)
        overlap: Number of tokens to overlap between chunks (default: 200)

    Returns:
        int: Number of chunks created and stored

    Raises:
        ValueError: If document_id not found in database
        Exception: If processing or storage fails

    Example:
        >>> from shared.database import get_db_connection
        >>> with get_db_connection() as conn:
        ...     chunk_count = process_document(
        ...         conn=conn,
        ...         bot_id=1,
        ...         document_id=42,
        ...         document_text="Long document content...",
        ...         voyage_api_key="pa-..."
        ...     )
        ...     print(f"Created {chunk_count} chunks")
    """
    try:
        logger.info(
            f"Processing document {document_id} for bot {bot_id} "
            f"(chunk_size={chunk_size}, overlap={overlap})"
        )

        # Convert bot_id to string (database uses VARCHAR for bot_id)
        # But first, we need to look up the bot's bot_id string from the integer id
        with conn.cursor() as cur:
            cur.execute("SELECT bot_id FROM bots WHERE id = %s", (bot_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Bot with id={bot_id} not found")
            bot_id_str = row[0] if isinstance(row, tuple) else row['bot_id']

        # Get document information
        with conn.cursor() as cur:
            cur.execute(
                "SELECT title, source, metadata FROM documents WHERE id = %s",
                (document_id,)
            )
            doc_row = cur.fetchone()

            if not doc_row:
                raise ValueError(f"Document {document_id} not found in database")

            title = doc_row[0] if isinstance(doc_row, tuple) else doc_row['title']
            source = doc_row[1] if isinstance(doc_row, tuple) else doc_row.get('source', 'unknown')
            metadata = doc_row[2] if isinstance(doc_row, tuple) else doc_row.get('metadata', {})

        logger.info(f"Found document: '{title}' (source: {source})")

        # Initialize OOP components
        voyage_client = VoyageClient(api_key=voyage_api_key)
        chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            min_chunk_size=100
        )

        # Step 1: Chunk the content
        chunks = chunker.chunk_text(document_text, metadata=metadata)

        if not chunks:
            logger.warning(f"No chunks created for document {document_id}")
            return 0

        logger.info(f"Created {len(chunks)} chunks")

        # Step 2: Generate embeddings for all chunks (batch)
        chunk_texts = [chunk['content'] for chunk in chunks]
        embeddings = voyage_client.embed_documents(chunk_texts)

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Step 3: Delete any existing chunks for this document (reprocessing)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE document_id = %s",
                (document_id,)
            )
            if cur.rowcount > 0:
                logger.info(f"Deleted {cur.rowcount} old chunks")

        # Step 4: Store chunks with embeddings
        with conn.cursor() as cur:
            for chunk, embedding in zip(chunks, embeddings):
                # Convert embedding list to pgvector format
                embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

                # Convert metadata to JSON
                metadata_json = json.dumps(chunk.get('metadata', {}))

                cur.execute("""
                    INSERT INTO document_chunks
                        (document_id, chunk_index, content, token_count, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s::vector, %s)
                """, (
                    document_id,
                    chunk['chunk_index'],
                    chunk['content'],
                    chunk['token_count'],
                    embedding_str,
                    metadata_json
                ))

        logger.info(
            f"Successfully processed document {document_id} with {len(chunks)} chunks"
        )

        return len(chunks)

    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        raise


def rag_query(
    conn,
    bot_id: int,
    user_query: str,
    voyage_api_key: str,
    top_k: int = 3
) -> str:
    """
    Perform RAG query: embed question, search similar chunks, format context.

    This high-level function takes a user query, finds the most relevant
    document chunks using vector similarity search, and returns them formatted
    as context for an LLM.

    The function:
    1. Generates an embedding for the user query using Voyage AI
    2. Searches for the most similar chunks using pgvector cosine similarity
    3. Formats the results as a context string suitable for Claude

    Args:
        conn: psycopg2 database connection object
        bot_id: ID of the bot to search within (integer)
        user_query: User's question or query text
        voyage_api_key: Voyage AI API key for generating query embedding
        top_k: Number of top results to return (default: 3)

    Returns:
        str: Formatted context string containing the most relevant chunks

    Format:
        RELEVANT CONTEXT:

        [Source: Document Title]
        "Chunk content here..."

        [Source: Another Document]
        "More relevant content..."

    Example:
        >>> from shared.database import get_db_connection
        >>> with get_db_connection() as conn:
        ...     context = rag_query(
        ...         conn=conn,
        ...         bot_id=1,
        ...         user_query="What services do you offer?",
        ...         voyage_api_key="pa-...",
        ...         top_k=5
        ...     )
        ...     print(context)
    """
    try:
        logger.info(
            f"RAG query for bot {bot_id}: '{user_query[:50]}...' (top_k={top_k})"
        )

        # Convert bot_id integer to bot_id string
        with conn.cursor() as cur:
            cur.execute("SELECT bot_id FROM bots WHERE id = %s", (bot_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Bot with id={bot_id} not found")
            bot_id_str = row[0] if isinstance(row, tuple) else row['bot_id']

        # Initialize OOP components
        voyage_client = VoyageClient(api_key=voyage_api_key)
        db_wrapper = _DatabaseConnectionWrapper(conn)
        retriever = RAGRetriever(voyage_client, db_wrapper)

        # Search for relevant chunks
        # Use a lower similarity threshold (0.6) to ensure we get results
        chunks = retriever.search(
            bot_id=bot_id_str,
            query=user_query,
            top_k=top_k,
            similarity_threshold=0.6
        )

        logger.info(f"Found {len(chunks)} relevant chunks")

        # Format as context
        context = retriever.format_context(
            chunks,
            max_tokens=2000,
            include_sources=True
        )

        return context

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise
