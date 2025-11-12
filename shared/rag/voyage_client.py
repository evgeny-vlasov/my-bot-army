"""
Voyage AI Embeddings Client

Wrapper for Voyage AI API to generate text embeddings for RAG.

Voyage AI is optimized for retrieval tasks and is more cost-effective
than alternatives for embeddings-only use cases.

Pricing (as of 2024):
- voyage-3-lite: $0.06/1M tokens, 512 dimensions
- voyage-3: $0.12/1M tokens, 1024 dimensions

API Documentation: https://docs.voyageai.com/
"""

import os
import time
import logging
from typing import List, Union, Optional
import requests

logger = logging.getLogger(__name__)


class VoyageClient:
    """
    Client for Voyage AI embeddings API.

    Example:
        client = VoyageClient(api_key="pa-...", model="voyage-3-lite")

        # Single text
        embedding = client.embed_query("What services do you offer?")

        # Multiple documents
        embeddings = client.embed_texts(["doc1", "doc2", "doc3"])
    """

    # API endpoint
    API_URL = "https://api.voyageai.com/v1/embeddings"

    # Model configurations
    MODEL_DIMENSIONS = {
        "voyage-3-lite": 512,
        "voyage-3": 1024,
        "voyage-2": 1024,
        "voyage-large-2": 1536,
        "voyage-code-2": 1536,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "voyage-3-lite"
    ):
        """
        Initialize Voyage AI client.

        Args:
            api_key: Voyage AI API key. If None, loads from VOYAGE_API_KEY env var
            model: Model name (default: "voyage-3-lite")
                  Options: "voyage-3-lite", "voyage-3", "voyage-2", etc.

        Raises:
            ValueError: If API key not provided and not in environment
        """
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Voyage API key required. Either pass api_key parameter or "
                "set VOYAGE_API_KEY environment variable. "
                "Get your key at: https://www.voyageai.com/"
            )

        self.model = model

        # Validate model
        if model not in self.MODEL_DIMENSIONS:
            logger.warning(
                f"Unknown model '{model}'. Known models: {list(self.MODEL_DIMENSIONS.keys())}. "
                "Proceeding anyway - API will validate."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

        logger.info(f"Initialized VoyageClient with model: {model}")

    def get_embedding_dimension(self) -> int:
        """
        Get embedding dimension for the current model.

        Returns:
            Embedding dimension (e.g., 512 for voyage-3-lite)
        """
        return self.MODEL_DIMENSIONS.get(self.model, 512)

    def embed_texts(
        self,
        texts: Union[str, List[str]],
        input_type: str = "document",
        truncate: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> List[List[float]]:
        """
        Generate embeddings for one or more texts.

        Args:
            texts: Single text string or list of texts
            input_type: "document" or "query"
                       - Use "document" when embedding documents for storage
                       - Use "query" when embedding search queries
            truncate: If True, truncate texts that exceed model limits
            max_retries: Number of retries on failure
            retry_delay: Initial delay between retries (exponential backoff)

        Returns:
            List of embedding vectors (each is List[float])
            If single string input, returns list with one embedding

        Raises:
            requests.HTTPError: If API request fails after retries
        """
        # Normalize input to list
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return []

        # Prepare request payload
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": input_type,
        }

        if truncate:
            payload["truncation"] = True

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.API_URL,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                # Parse response
                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]

                logger.debug(
                    f"Generated {len(embeddings)} embeddings using {self.model}"
                )

                return embeddings

            except requests.exceptions.RequestException as e:
                last_exception = e

                # Check if we should retry
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Voyage API request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Voyage API request failed after {max_retries} attempts: {e}"
                    )

        # If we get here, all retries failed
        raise last_exception

    def embed_query(
        self,
        query: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> List[float]:
        """
        Generate embedding for a search query.

        This is a convenience method that calls embed_texts with input_type="query".

        Args:
            query: Search query text
            max_retries: Number of retries on failure
            retry_delay: Initial delay between retries

        Returns:
            Single embedding vector (List[float])
        """
        embeddings = self.embed_texts(
            texts=query,
            input_type="query",
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        return embeddings[0]

    def embed_documents(
        self,
        documents: List[str],
        batch_size: int = 128,
        max_retries: int = 3
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple documents with batching.

        Voyage AI supports up to 128 texts per request. This method handles
        batching automatically for larger inputs.

        Args:
            documents: List of document texts
            batch_size: Number of documents per API call (max 128)
            max_retries: Number of retries per batch on failure

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            logger.info(
                f"Processing batch {i // batch_size + 1} "
                f"({len(batch)} documents)"
            )

            batch_embeddings = self.embed_texts(
                texts=batch,
                input_type="document",
                max_retries=max_retries
            )

            all_embeddings.extend(batch_embeddings)

        logger.info(f"Generated {len(all_embeddings)} document embeddings")

        return all_embeddings

    def __repr__(self) -> str:
        return f"VoyageClient(model='{self.model}', dimensions={self.get_embedding_dimension()})"


# Convenience function for quick testing
def test_voyage_client():
    """Test Voyage AI client with sample texts."""
    try:
        client = VoyageClient(model="voyage-3-lite")

        print(f"Testing {client}")
        print(f"Embedding dimension: {client.get_embedding_dimension()}")

        # Test single query
        query_embedding = client.embed_query("What is RAG?")
        print(f"\nQuery embedding length: {len(query_embedding)}")
        print(f"First 5 values: {query_embedding[:5]}")

        # Test multiple documents
        docs = [
            "Retrieval-Augmented Generation combines search with LLMs",
            "Vector databases store embeddings for similarity search",
            "Chunking splits long documents into smaller pieces"
        ]
        doc_embeddings = client.embed_documents(docs)
        print(f"\nGenerated {len(doc_embeddings)} document embeddings")

        print("\n✓ Voyage AI client test successful!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise


if __name__ == "__main__":
    # Run test if executed directly
    test_voyage_client()
