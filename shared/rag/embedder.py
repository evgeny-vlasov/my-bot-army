"""
Document Embedder

High-level document processing pipeline that:
1. Chunks documents into semantic segments
2. Generates embeddings for each chunk
3. Stores documents and chunks in database

This module ties together the chunker and Voyage client to provide
a complete document ingestion pipeline for RAG.
"""

import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentEmbedder:
    """
    Processes documents for RAG storage.

    Workflow:
    1. Store document in database (get document_id)
    2. Chunk the document content
    3. Generate embeddings for all chunks (batch API call)
    4. Store chunks with embeddings in database

    Example:
        from shared.rag import VoyageClient, TextChunker, DocumentEmbedder
        from shared.database import DatabaseConnection

        voyage = VoyageClient()
        chunker = TextChunker()
        db = DatabaseConnection()
        embedder = DocumentEmbedder(voyage, chunker, db)

        # Look up numeric bot ID from string bot_id
        # (In practice, use the lookup function from add_document.py)
        # bot_id = 1  # Numeric ID from bots.id column

        # Process a document
        doc_id = embedder.process_document(
            bot_id=1,  # Use numeric bot ID, not string!
            title="Services Overview",
            content="We offer landscaping services...",
            source="manual_upload"
        )
    """

    def __init__(self, voyage_client, chunker, db_connection):
        """
        Initialize document embedder.

        Args:
            voyage_client: VoyageClient instance for embeddings
            chunker: TextChunker instance for splitting text
            db_connection: Database connection object (from shared.database)
        """
        self.voyage_client = voyage_client
        self.chunker = chunker
        self.db = db_connection

        logger.info("Initialized DocumentEmbedder")

    def process_document(
        self,
        bot_id: int,
        title: str,
        content: str,
        source: str = "manual_upload",
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Process and store a document with embeddings.

        Args:
            bot_id: Numeric bot ID (bots.id) - NOT the string bot_id!
            title: Document title
            content: Full document text
            source: Source identifier (e.g., "uploaded_pdf", "website", "manual")
            metadata: Optional metadata dict (file_name, url, date, etc.)

        Returns:
            document_id: ID of created document

        Raises:
            Exception: If document processing or storage fails
        """
        try:
            logger.info(f"Processing document: '{title}' for bot '{bot_id}'")

            # Step 1: Store document in database
            document_id = self._store_document(
                bot_id=bot_id,
                title=title,
                content=content,
                source=source,
                metadata=metadata
            )

            logger.info(f"Created document with ID: {document_id}")

            # Step 2: Chunk the content
            chunks = self.chunker.chunk_text(content, metadata=metadata)

            if not chunks:
                logger.warning(f"No chunks created for document {document_id}")
                return document_id

            logger.info(f"Created {len(chunks)} chunks")

            # Step 3: Generate embeddings for all chunks (batch)
            chunk_texts = [chunk['content'] for chunk in chunks]
            embeddings = self.voyage_client.embed_documents(chunk_texts)

            logger.info(f"Generated {len(embeddings)} embeddings")

            # Step 4: Store chunks with embeddings
            self._store_chunks(document_id, chunks, embeddings)

            logger.info(
                f"Successfully processed document {document_id} "
                f"with {len(chunks)} chunks"
            )

            return document_id

        except Exception as e:
            logger.error(f"Failed to process document '{title}': {e}")
            raise

    def reindex_document(self, document_id: int) -> int:
        """
        Regenerate chunks and embeddings for an existing document.

        Useful when:
        - Changing embedding model
        - Updating chunking parameters
        - Fixing corrupted embeddings

        Args:
            document_id: ID of document to reindex

        Returns:
            Number of chunks created

        Raises:
            Exception: If document not found or reindexing fails
        """
        try:
            logger.info(f"Reindexing document {document_id}")

            # Get original document
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT bot_id, title, content, source, metadata "
                        "FROM documents WHERE id = %s",
                        (document_id,)
                    )
                    row = cur.fetchone()

                    if not row:
                        raise ValueError(f"Document {document_id} not found")

                    bot_id, title, content, source, metadata_json = row

            logger.info(f"Found document: '{title}'")

            # Parse metadata if it's a string
            if isinstance(metadata_json, str):
                metadata = json.loads(metadata_json) if metadata_json else {}
            else:
                metadata = metadata_json or {}

            # Delete old chunks
            self._delete_chunks(document_id)

            # Chunk the content
            chunks = self.chunker.chunk_text(content, metadata=metadata)

            if not chunks:
                logger.warning(f"No chunks created for document {document_id}")
                return 0

            # Generate embeddings
            chunk_texts = [chunk['content'] for chunk in chunks]
            embeddings = self.voyage_client.embed_documents(chunk_texts)

            # Store new chunks
            self._store_chunks(document_id, chunks, embeddings)

            logger.info(
                f"Successfully reindexed document {document_id} "
                f"with {len(chunks)} chunks"
            )

            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to reindex document {document_id}: {e}")
            raise

    def delete_document(self, document_id: int) -> bool:
        """
        Delete a document and all its chunks.

        Args:
            document_id: ID of document to delete

        Returns:
            True if successful, False if document not found

        Note:
            Chunks are automatically deleted via CASCADE constraint
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM documents WHERE id = %s",
                        (document_id,)
                    )
                    deleted = cur.rowcount > 0

            if deleted:
                logger.info(f"Deleted document {document_id}")
            else:
                logger.warning(f"Document {document_id} not found")

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    def get_document_info(self, document_id: int) -> Optional[Dict]:
        """
        Get information about a document including chunk count.

        Args:
            document_id: ID of document

        Returns:
            Dictionary with document info or None if not found
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            d.id,
                            d.bot_id,
                            d.title,
                            d.source,
                            d.created_at,
                            d.updated_at,
                            COUNT(dc.id) as chunk_count,
                            SUM(dc.token_count) as total_tokens
                        FROM documents d
                        LEFT JOIN document_chunks dc ON d.id = dc.document_id
                        WHERE d.id = %s
                        GROUP BY d.id
                    """, (document_id,))

                    row = cur.fetchone()

                    if not row:
                        return None

                    return {
                        'id': row[0],
                        'bot_id': row[1],
                        'title': row[2],
                        'source': row[3],
                        'created_at': row[4],
                        'updated_at': row[5],
                        'chunk_count': row[6] or 0,
                        'total_tokens': row[7] or 0
                    }

        except Exception as e:
            logger.error(f"Failed to get document info for {document_id}: {e}")
            raise

    def _store_document(
        self,
        bot_id: int,
        title: str,
        content: str,
        source: str,
        metadata: Optional[Dict]
    ) -> int:
        """
        Store document in database.

        Args:
            bot_id: Numeric bot ID (bots.id)

        Returns:
            document_id
        """
        metadata_json = json.dumps(metadata or {})

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO documents
                        (bot_id, title, content, source, metadata, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    bot_id,
                    title,
                    content,
                    source,
                    metadata_json,
                    datetime.now(),
                    datetime.now()
                ))

                document_id = cur.fetchone()[0]

        return document_id

    def _store_chunks(
        self,
        document_id: int,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> None:
        """
        Store chunks with embeddings in database.

        Args:
            document_id: Parent document ID
            chunks: List of chunk dictionaries from chunker
            embeddings: List of embedding vectors from Voyage
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunk count ({len(chunks)}) doesn't match "
                f"embedding count ({len(embeddings)})"
            )

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Batch insert all chunks
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

        logger.debug(f"Stored {len(chunks)} chunks for document {document_id}")

    def _delete_chunks(self, document_id: int) -> int:
        """
        Delete all chunks for a document.

        Returns:
            Number of chunks deleted
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM document_chunks WHERE document_id = %s",
                    (document_id,)
                )
                deleted_count = cur.rowcount

        logger.debug(f"Deleted {deleted_count} chunks for document {document_id}")
        return deleted_count


# For testing
def test_embedder():
    """Test document embedder with sample data."""
    from shared.rag import VoyageClient, TextChunker
    from shared.database import DatabaseConnection

    # Initialize components
    voyage = VoyageClient()
    chunker = TextChunker(chunk_size=300, chunk_overlap=50)
    db = DatabaseConnection()
    embedder = DocumentEmbedder(voyage, chunker, db)

    # Sample document
    sample_content = """
    Keystone Hardscapes is Calgary's premier landscaping company.

    We specialize in:
    - Custom patios and walkways
    - Retaining walls
    - Outdoor kitchens
    - Fire pits and features

    Service Areas:
    Calgary, Airdrie, Cochrane, Okotoks and surrounding areas.

    All work comes with a 5-year warranty.
    """

    # Process document
    # NOTE: In real usage, look up numeric bot ID from bots table
    # For test purposes, using 1 (assumes bot with id=1 exists)
    doc_id = embedder.process_document(
        bot_id=1,  # Use numeric bot ID
        title="Test Services Document",
        content=sample_content,
        source="test",
        metadata={'test': True}
    )

    print(f"✓ Created document ID: {doc_id}")

    # Get document info
    info = embedder.get_document_info(doc_id)
    print(f"✓ Document info: {info}")

    # Cleanup
    embedder.delete_document(doc_id)
    print(f"✓ Deleted test document")


if __name__ == "__main__":
    test_embedder()
