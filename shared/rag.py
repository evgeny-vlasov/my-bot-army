"""
RAG (Retrieval-Augmented Generation) utilities for Bot Army platform.

This module provides functions for:
- Text chunking with overlap
- Getting embeddings from Voyage AI
- Storing document chunks with embeddings in PostgreSQL
- Similarity search using pgvector cosine distance

Usage:
    from shared.rag import process_document, rag_query

    # High-level API (recommended):
    # Process a document
    with get_db_connection() as conn:
        num_chunks = process_document(conn, bot_id, doc_id, doc_text, api_key)

    # Query with RAG
    with get_db_connection() as conn:
        context = rag_query(conn, bot_id, "user question", api_key, top_k=3)

    # Low-level API (for custom workflows):
    from shared.rag import chunk_text, get_voyage_embedding, store_document_chunks, search_similar_chunks

    chunks = chunk_text(document_text, chunk_size=800, overlap=200)
    embeddings = [get_voyage_embedding(chunk, api_key) for chunk in chunks]
    store_document_chunks(conn, bot_id, document_id, chunks, embeddings)
    query_emb = get_voyage_embedding("user question", api_key)
    results = search_similar_chunks(conn, bot_id, query_emb, top_k=5)
"""

import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Voyage AI configuration
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-3"
EMBEDDING_DIMENSIONS = 1024


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks, preferring sentence boundaries.

    This function breaks text into chunks of approximately chunk_size characters,
    with overlap between consecutive chunks. It attempts to break at sentence
    boundaries (. ! ? or double newlines) for better semantic coherence.

    Args:
        text: The text to split into chunks
        chunk_size: Target size of each chunk in characters (default: 800)
        overlap: Number of characters to overlap between chunks (default: 200)

    Returns:
        List of text chunks. Returns empty list for empty input.

    Examples:
        >>> chunks = chunk_text("This is sentence one. This is sentence two.", chunk_size=30, overlap=10)
        >>> len(chunks)
        2

        >>> chunk_text("")
        []

        >>> chunk_text("Short text")
        ['Short text']
    """
    # Handle edge cases
    if not text or len(text.strip()) == 0:
        logger.debug("Empty text provided, returning empty list")
        return []

    if len(text) <= chunk_size:
        logger.debug(f"Text length ({len(text)}) <= chunk_size ({chunk_size}), returning single chunk")
        return [text]

    chunks = []
    start = 0

    # Sentence boundary markers
    sentence_endings = ['. ', '! ', '? ', '\n\n']

    while start < len(text):
        # Determine end position for this chunk
        end = start + chunk_size

        # If this is the last chunk, take everything remaining
        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to find a sentence boundary near the end of the chunk
        # Look in the last 20% of the chunk for a good break point
        search_start = end - int(chunk_size * 0.2)
        best_break = -1

        for ending in sentence_endings:
            # Find the last occurrence of this ending in the search range
            pos = text.rfind(ending, search_start, end)
            if pos != -1 and pos > best_break:
                best_break = pos + len(ending)

        # If we found a good sentence boundary, use it
        if best_break != -1:
            end = best_break
        # Otherwise, just split at chunk_size

        chunks.append(text[start:end])

        # Move start position with overlap
        start = end - overlap

        # Make sure we're making progress (avoid infinite loop)
        if start <= len(chunks[-1]) - overlap:
            start = end

    logger.info(f"Split text of length {len(text)} into {len(chunks)} chunks")
    return chunks


def get_voyage_embedding(text: str, api_key: str) -> List[float]:
    """
    Get embedding vector from Voyage AI API.

    Calls the Voyage AI embeddings API to convert text into a 1024-dimensional
    vector representation suitable for semantic search.

    Args:
        text: The text to embed
        api_key: Voyage AI API key

    Returns:
        List of 1024 floats representing the embedding vector

    Raises:
        ValueError: If API key is missing or text is empty
        requests.exceptions.RequestException: If API call fails

    Examples:
        >>> embedding = get_voyage_embedding("Hello world", "your-api-key")
        >>> len(embedding)
        1024
    """
    if not api_key:
        logger.error("Voyage API key is required")
        raise ValueError("Voyage API key is required")

    if not text or len(text.strip()) == 0:
        logger.error("Cannot embed empty text")
        raise ValueError("Text cannot be empty")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": [text],
        "model": VOYAGE_MODEL
    }

    try:
        logger.debug(f"Calling Voyage AI API for text of length {len(text)}")
        response = requests.post(VOYAGE_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract embedding from response
        # Expected format: {"data": [{"embedding": [...]}]}
        if "data" not in data or len(data["data"]) == 0:
            logger.error(f"Unexpected API response format: {data}")
            raise ValueError("Unexpected API response format")

        embedding = data["data"][0]["embedding"]

        if len(embedding) != EMBEDDING_DIMENSIONS:
            logger.warning(f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(embedding)}")

        logger.debug(f"Successfully retrieved embedding with {len(embedding)} dimensions")
        return embedding

    except requests.exceptions.Timeout:
        logger.error("Voyage AI API request timed out")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"Voyage AI API HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Voyage AI API request failed: {str(e)}")
        raise
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Error parsing Voyage AI API response: {str(e)}")
        raise


def store_document_chunks(
    conn,
    bot_id: int,
    document_id: int,
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Store document chunks with embeddings in the database.

    Performs a batch insert of document chunks and their embeddings into the
    document_chunks table. This function uses execute_values for efficient
    batch insertion.

    Args:
        conn: psycopg2 database connection object
        bot_id: ID of the bot that owns this document
        document_id: ID of the parent document
        chunks: List of text chunks
        embeddings: List of embedding vectors (must match length of chunks)
        metadata: Optional metadata dictionary to store with each chunk

    Returns:
        Number of chunks successfully inserted

    Raises:
        ValueError: If chunks and embeddings lists have different lengths
        psycopg2.Error: If database operation fails

    Examples:
        >>> from shared.database import get_db_connection
        >>> with get_db_connection() as conn:
        ...     count = store_document_chunks(conn, 1, 123, chunks, embeddings)
        >>> print(f"Inserted {count} chunks")
    """
    # Validate inputs
    if len(chunks) != len(embeddings):
        error_msg = f"Chunks count ({len(chunks)}) must match embeddings count ({len(embeddings)})"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if len(chunks) == 0:
        logger.warning("No chunks to store")
        return 0

    try:
        cursor = conn.cursor()

        # Prepare data for batch insert
        # Format: (document_id, bot_id, chunk_text, chunk_index, embedding, metadata)
        import json
        metadata_json = json.dumps(metadata) if metadata else None

        values = [
            (
                document_id,
                bot_id,
                chunk,
                idx,
                embedding,  # Will be cast to vector type in SQL
                metadata_json
            )
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        # Batch insert using execute_values
        query = """
            INSERT INTO document_chunks
            (document_id, bot_id, chunk_text, chunk_index, embedding, metadata)
            VALUES %s
        """

        # Use execute_values with template that casts embedding to vector
        template = "(%s, %s, %s, %s, %s::vector, %s)"

        logger.info(f"Inserting {len(values)} chunks for document_id={document_id}, bot_id={bot_id}")
        execute_values(cursor, query, values, template=template)

        rows_inserted = cursor.rowcount
        logger.info(f"Successfully inserted {rows_inserted} document chunks")

        return rows_inserted

    except Exception as e:
        logger.error(f"Error storing document chunks: {str(e)}")
        # Let the error propagate so the context manager can rollback
        raise


def search_similar_chunks(
    conn,
    bot_id: int,
    query_embedding: List[float],
    top_k: int = 5
) -> List[Tuple[str, float]]:
    """
    Search for similar document chunks using cosine similarity.

    Uses pgvector's cosine distance operator (<=>) to find the most similar
    chunks to a query embedding. Returns chunks with similarity scores where
    higher scores indicate better matches.

    Args:
        conn: psycopg2 database connection object
        bot_id: ID of the bot to search within
        query_embedding: Query embedding vector (1024 dimensions)
        top_k: Number of top results to return (default: 5)

    Returns:
        List of tuples (chunk_text, similarity_score) ordered by similarity
        where similarity_score is between 0 and 1 (higher = more similar)

    Raises:
        ValueError: If query_embedding is empty or top_k < 1
        psycopg2.Error: If database operation fails

    Examples:
        >>> from shared.database import get_db_connection
        >>> query_emb = get_voyage_embedding("What is your return policy?", api_key)
        >>> with get_db_connection() as conn:
        ...     results = search_similar_chunks(conn, bot_id=1, query_embedding=query_emb, top_k=3)
        >>> for text, score in results:
        ...     print(f"Score: {score:.3f} - {text[:100]}...")
    """
    # Validate inputs
    if not query_embedding or len(query_embedding) == 0:
        logger.error("Query embedding cannot be empty")
        raise ValueError("Query embedding cannot be empty")

    if top_k < 1:
        logger.error(f"top_k must be >= 1, got {top_k}")
        raise ValueError("top_k must be >= 1")

    try:
        cursor = conn.cursor()

        # Query using pgvector's cosine distance operator
        # <=> is cosine distance (0 = identical, 2 = opposite)
        # We order by distance (ascending) to get most similar first
        # Convert distance to similarity: 1 - distance
        query = """
            SELECT
                chunk_text,
                1 - (embedding <=> %s::vector) AS similarity
            FROM document_chunks
            WHERE bot_id = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        logger.debug(f"Searching for {top_k} similar chunks for bot_id={bot_id}")
        cursor.execute(query, (query_embedding, bot_id, query_embedding, top_k))

        results = cursor.fetchall()

        # Convert RealDictRow to tuples (chunk_text, similarity_score)
        result_tuples = [(row['chunk_text'], float(row['similarity'])) for row in results]

        logger.info(f"Found {len(result_tuples)} similar chunks for bot_id={bot_id}")
        return result_tuples

    except Exception as e:
        logger.error(f"Error searching similar chunks: {str(e)}")
        raise


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
    Complete pipeline to process a document: chunk, embed, and store.

    This high-level function combines chunking, embedding generation, and
    database storage into a single operation with progress logging.

    Args:
        conn: psycopg2 database connection object
        bot_id: ID of the bot that owns this document
        document_id: ID of the document being processed
        document_text: Full text content of the document
        voyage_api_key: Voyage AI API key for embeddings
        chunk_size: Target size of each chunk in characters (default: 800)
        overlap: Number of characters to overlap between chunks (default: 200)

    Returns:
        Number of chunks successfully created and stored

    Raises:
        ValueError: If document_text is empty or API key is missing
        requests.exceptions.RequestException: If embedding API fails
        psycopg2.Error: If database operation fails

    Examples:
        >>> from shared.database import get_db_connection
        >>> with get_db_connection() as conn:
        ...     num_chunks = process_document(
        ...         conn, bot_id=1, document_id=123,
        ...         document_text=doc_text, voyage_api_key=api_key
        ...     )
        >>> print(f"Created {num_chunks} chunks")
    """
    if not document_text or len(document_text.strip()) == 0:
        logger.error("Cannot process empty document")
        raise ValueError("Document text cannot be empty")

    if not voyage_api_key:
        logger.error("Voyage API key is required")
        raise ValueError("Voyage API key is required")

    logger.info(f"Processing document_id={document_id} for bot_id={bot_id}, "
                f"text_length={len(document_text)} chars")

    # Step 1: Chunk the text
    logger.info("Step 1/3: Chunking text...")
    chunks = chunk_text(document_text, chunk_size=chunk_size, overlap=overlap)
    logger.info(f"Created {len(chunks)} chunks")

    # Step 2: Generate embeddings for all chunks
    logger.info("Step 2/3: Generating embeddings...")
    embeddings = []
    for i, chunk in enumerate(chunks):
        logger.debug(f"Embedding chunk {i+1}/{len(chunks)}")
        embedding = get_voyage_embedding(chunk, voyage_api_key)
        embeddings.append(embedding)
    logger.info(f"Generated {len(embeddings)} embeddings")

    # Step 3: Store chunks and embeddings in database
    logger.info("Step 3/3: Storing chunks in database...")
    num_stored = store_document_chunks(
        conn, bot_id, document_id, chunks, embeddings
    )

    logger.info(f"Successfully processed document_id={document_id}: "
                f"{num_stored} chunks stored")
    return num_stored


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
    document chunks using similarity search, and returns them formatted
    as context for an LLM.

    Args:
        conn: psycopg2 database connection object
        bot_id: ID of the bot to search within
        user_query: User's question or query text
        voyage_api_key: Voyage AI API key for embeddings
        top_k: Number of top results to return (default: 3)

    Returns:
        Formatted context string wrapped in <relevant_information> XML tags
        with numbered sources. Returns empty tags if no results found.

    Raises:
        ValueError: If user_query is empty or API key is missing
        requests.exceptions.RequestException: If embedding API fails
        psycopg2.Error: If database operation fails

    Examples:
        >>> from shared.database import get_db_connection
        >>> with get_db_connection() as conn:
        ...     context = rag_query(
        ...         conn, bot_id=1,
        ...         user_query="What is your return policy?",
        ...         voyage_api_key=api_key, top_k=3
        ...     )
        >>> print(context)
        <relevant_information>
        [Source 1]: Returns are accepted within 30 days...
        [Source 2]: Refunds are processed within 5-7 business days...
        [Source 3]: Items must be in original packaging...
        </relevant_information>
    """
    if not user_query or len(user_query.strip()) == 0:
        logger.error("Cannot query with empty text")
        raise ValueError("User query cannot be empty")

    if not voyage_api_key:
        logger.error("Voyage API key is required")
        raise ValueError("Voyage API key is required")

    logger.info(f"RAG query for bot_id={bot_id}: '{user_query[:100]}...'")

    # Step 1: Embed the user query
    logger.debug("Embedding user query...")
    query_embedding = get_voyage_embedding(user_query, voyage_api_key)

    # Step 2: Search for similar chunks
    logger.debug(f"Searching for top {top_k} similar chunks...")
    results = search_similar_chunks(conn, bot_id, query_embedding, top_k)

    # Step 3: Format results as context
    if not results:
        logger.info("No relevant chunks found")
        return "<relevant_information>\nNo relevant information found.\n</relevant_information>"

    logger.info(f"Found {len(results)} relevant chunks")

    # Format as numbered sources
    formatted_chunks = []
    for i, (chunk_text, similarity) in enumerate(results, 1):
        formatted_chunks.append(f"[Source {i}]: {chunk_text}")
        logger.debug(f"Source {i} similarity: {similarity:.3f}")

    context = "<relevant_information>\n" + "\n\n".join(formatted_chunks) + "\n</relevant_information>"

    return context


if __name__ == '__main__':
    """Test basic functionality"""
    print("Testing RAG utilities...")

    # Test chunking
    test_text = "This is sentence one. This is sentence two. This is sentence three. " * 50
    chunks = chunk_text(test_text, chunk_size=100, overlap=20)
    print(f"✓ Chunking works: created {len(chunks)} chunks from {len(test_text)} chars")

    # Test edge cases
    assert chunk_text("") == []
    assert chunk_text("short") == ["short"]
    print("✓ Edge cases handled correctly")

    print("\n✓ Basic tests completed!")
