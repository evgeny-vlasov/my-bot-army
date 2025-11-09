from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.schemas.document import Document


class RAGService:
    """Service for Retrieval Augmented Generation using pgvector"""

    @staticmethod
    async def search_similar_documents(
        db: AsyncSession,
        bot_id: int,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Document]:
        """
        Search for similar documents using vector similarity.

        Args:
            db: Database session
            bot_id: Bot ID to search documents for
            query_embedding: Vector embedding of the query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar documents
        """
        # Convert embedding to pgvector format
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Query for similar documents using cosine similarity
        query = text("""
            SELECT *, 1 - (embedding <=> :query_embedding::vector) as similarity
            FROM documents
            WHERE bot_id = :bot_id
              AND embedding IS NOT NULL
              AND 1 - (embedding <=> :query_embedding::vector) >= :threshold
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = await db.execute(
            query,
            {
                "query_embedding": embedding_str,
                "bot_id": bot_id,
                "threshold": similarity_threshold,
                "limit": limit,
            }
        )

        documents = []
        for row in result:
            doc = Document(
                id=row.id,
                bot_id=row.bot_id,
                title=row.title,
                content=row.content,
                source=row.source,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            documents.append(doc)

        return documents

    @staticmethod
    async def get_context_for_query(
        db: AsyncSession,
        bot_id: int,
        query: str,
        embedding_service,  # Service to generate embeddings
    ) -> str:
        """
        Get relevant context for a query using RAG.

        Returns:
            Formatted context string to add to prompt
        """
        # Generate embedding for query
        query_embedding = await embedding_service.get_embedding(query)

        # Search for similar documents
        similar_docs = await RAGService.search_similar_documents(
            db=db,
            bot_id=bot_id,
            query_embedding=query_embedding,
            limit=3,  # Top 3 most relevant
        )

        if not similar_docs:
            return ""

        # Format context
        context_parts = []
        for i, doc in enumerate(similar_docs, 1):
            context_parts.append(f"Document {i}: {doc.title or 'Untitled'}\n{doc.content}\n")

        return "\n".join(context_parts)
