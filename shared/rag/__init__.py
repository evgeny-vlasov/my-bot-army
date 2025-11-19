"""
RAG (Retrieval-Augmented Generation) Module

This module provides RAG functionality for Flask-based bots in the My Bot Army system.

Components:
- voyage_client: Voyage AI API wrapper for generating embeddings
- chunker: Text chunking utilities for breaking documents into semantic chunks
- embedder: Document processing pipeline (chunk + embed + store)
- retriever: Vector similarity search and context formatting

Usage:
    from shared.rag import VoyageClient, TextChunker, DocumentEmbedder, RAGRetriever

    # Initialize components
    voyage_client = VoyageClient(api_key="your-key", model="voyage-3-lite")
    chunker = TextChunker(chunk_size=800, chunk_overlap=150)
    embedder = DocumentEmbedder(voyage_client, chunker, db_connection)
    retriever = RAGRetriever(voyage_client, db_connection)

    # Add a document
    doc_id = embedder.process_document(
        bot_id="keystone-landscaping",
        title="Services Overview",
        content="...",
        source="uploaded_pdf"
    )

    # Search for relevant context
    results = retriever.search(
        bot_id="keystone-landscaping",
        query="Do you offer retaining walls?",
        top_k=5
    )

    # Format context for Claude
    context_str = retriever.format_context(results)
"""

from .voyage_client import VoyageClient
from .chunker import TextChunker
from .embedder import DocumentEmbedder
from .retriever import RAGRetriever

__all__ = [
    'VoyageClient',
    'TextChunker',
    'DocumentEmbedder',
    'RAGRetriever',
]

__version__ = '1.0.0'
