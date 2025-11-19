"""
Text Chunking Utilities

Splits long documents into smaller, semantically meaningful chunks
for embedding and retrieval.

Strategy:
- Respects paragraph and sentence boundaries
- Configurable chunk size with overlap
- Maintains context across chunk boundaries
- Filters out chunks that are too small
"""

import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Chunks text into overlapping segments for RAG.

    Example:
        chunker = TextChunker(chunk_size=800, chunk_overlap=150)
        chunks = chunker.chunk_text(long_document)

        for chunk in chunks:
            print(f"Chunk {chunk['chunk_index']}: {chunk['token_count']} tokens")
            print(chunk['content'][:100])
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        min_chunk_size: int = 100
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target size for each chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
            min_chunk_size: Minimum tokens for a chunk to be kept
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        logger.info(
            f"Initialized TextChunker: size={chunk_size}, "
            f"overlap={chunk_overlap}, min={min_chunk_size}"
        )

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.

        Uses a simple heuristic: ~4 characters per token.
        This is a rough approximation but works well for chunking.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Remove extra whitespace for better estimate
        cleaned = re.sub(r'\s+', ' ', text.strip())
        char_count = len(cleaned)

        # ~4 characters per token (varies by language and content)
        return max(1, char_count // 4)

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text.

        - Normalizes whitespace
        - Removes excessive newlines
        - Preserves paragraph structure

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Normalize line endings
        text = text.replace('\r\n', '\n')

        # Collapse multiple spaces (but preserve newlines)
        text = re.sub(r' +', ' ', text)

        # Reduce multiple newlines to maximum of 2 (paragraph breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into sentences using basic punctuation rules.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Split on sentence-ending punctuation followed by space or newline
        # Handles: . ! ? followed by space/newline
        # Avoids splitting on: Mr. Dr. etc.
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)

        # Clean up each sentence
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    @staticmethod
    def split_into_paragraphs(text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Text to split

        Returns:
            List of paragraphs
        """
        # Split on double newlines (paragraph boundaries)
        paragraphs = text.split('\n\n')

        # Clean up each paragraph
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Chunk text into overlapping segments.

        Process:
        1. Clean text
        2. Split into paragraphs
        3. Combine paragraphs into chunks of target size
        4. Add overlap between chunks
        5. Filter chunks that are too small

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with keys:
                - content: The chunk text
                - chunk_index: Position in sequence (0, 1, 2...)
                - token_count: Estimated tokens
                - metadata: Copy of input metadata (if provided)
        """
        # Clean text
        cleaned_text = self.clean_text(text)

        if not cleaned_text:
            logger.warning("Empty text provided for chunking")
            return []

        # Estimate total tokens
        total_tokens = self.estimate_tokens(cleaned_text)
        logger.debug(f"Chunking text with ~{total_tokens} tokens")

        # If text is smaller than chunk size, return as single chunk
        if total_tokens <= self.chunk_size:
            chunk = {
                'content': cleaned_text,
                'chunk_index': 0,
                'token_count': total_tokens,
                'metadata': metadata or {}
            }
            logger.debug("Text fits in single chunk")
            return [chunk]

        # Split into paragraphs
        paragraphs = self.split_into_paragraphs(cleaned_text)
        logger.debug(f"Split into {len(paragraphs)} paragraphs")

        # Build chunks by combining paragraphs
        chunks = []
        current_chunk = []
        current_token_count = 0

        for paragraph in paragraphs:
            para_tokens = self.estimate_tokens(paragraph)

            # If paragraph alone exceeds chunk size, split into sentences
            if para_tokens > self.chunk_size:
                # Flush current chunk if it has content
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_token_count = 0

                # Split large paragraph into sentences
                sentences = self.split_into_sentences(paragraph)
                sentence_chunk = []
                sentence_token_count = 0

                for sentence in sentences:
                    sentence_tokens = self.estimate_tokens(sentence)

                    if sentence_token_count + sentence_tokens > self.chunk_size:
                        if sentence_chunk:
                            chunks.append(' '.join(sentence_chunk))
                            sentence_chunk = []
                            sentence_token_count = 0

                    sentence_chunk.append(sentence)
                    sentence_token_count += sentence_tokens

                # Add remaining sentences
                if sentence_chunk:
                    chunks.append(' '.join(sentence_chunk))

            # If adding paragraph would exceed chunk size, start new chunk
            elif current_token_count + para_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [paragraph]
                    current_token_count = para_tokens

            # Otherwise, add paragraph to current chunk
            else:
                current_chunk.append(paragraph)
                current_token_count += para_tokens

        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        logger.debug(f"Created {len(chunks)} preliminary chunks")

        # Add overlap between chunks
        overlapped_chunks = self._add_overlap(chunks)

        # Format output
        result = []
        for i, chunk_text in enumerate(overlapped_chunks):
            token_count = self.estimate_tokens(chunk_text)

            # Filter out chunks that are too small
            if token_count < self.min_chunk_size:
                logger.debug(
                    f"Skipping chunk {i} (only {token_count} tokens, "
                    f"min is {self.min_chunk_size})"
                )
                continue

            chunk_dict = {
                'content': chunk_text,
                'chunk_index': len(result),  # Re-index after filtering
                'token_count': token_count,
                'metadata': metadata or {}
            }
            result.append(chunk_dict)

        logger.info(
            f"Chunked text into {len(result)} chunks "
            f"(~{sum(c['token_count'] for c in result)} total tokens)"
        )

        return result

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """
        Add overlap between consecutive chunks.

        Takes the last N tokens from chunk[i] and prepends to chunk[i+1].

        Args:
            chunks: List of chunk texts

        Returns:
            List of overlapped chunk texts
        """
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks

        overlapped = [chunks[0]]  # First chunk has no prefix

        for i in range(1, len(chunks)):
            previous_chunk = chunks[i - 1]
            current_chunk = chunks[i]

            # Get overlap from previous chunk
            # Simple approach: take last N characters (roughly N/4 tokens)
            overlap_chars = self.chunk_overlap * 4
            overlap_text = previous_chunk[-overlap_chars:].strip()

            # Try to start overlap at a sentence boundary if possible
            # Find the first '. ' or '? ' or '! ' in overlap text
            sentence_match = re.search(r'[.!?]\s+', overlap_text)
            if sentence_match:
                overlap_text = overlap_text[sentence_match.end():]

            # Combine overlap + current chunk
            if overlap_text:
                overlapped_chunk = overlap_text + ' ' + current_chunk
            else:
                overlapped_chunk = current_chunk

            overlapped.append(overlapped_chunk)

        logger.debug(f"Added overlap to {len(chunks) - 1} chunks")

        return overlapped


def test_chunker():
    """Test the text chunker with sample text."""
    sample_text = """
    Keystone Hardscapes is Calgary's premier landscaping company, specializing in
    outdoor living spaces that transform your property into a beautiful oasis.

    Our Services:
    We offer a comprehensive range of landscaping services including:
    - Custom patio design and installation
    - Retaining walls and terracing
    - Outdoor kitchens and fire pits
    - Decorative concrete and stamped patterns
    - Complete landscape design

    Service Area:
    We proudly serve Calgary, Airdrie, Cochrane, Okotoks, and surrounding areas
    within 50km of Calgary. Our team is familiar with local soil conditions,
    climate considerations, and municipal regulations.

    Quality Guarantee:
    All our work comes with a 5-year warranty on materials and workmanship.
    We use only premium materials from trusted suppliers and our team consists
    of certified landscaping professionals with an average of 10+ years experience.

    Pricing:
    Our pricing is competitive and transparent. We provide detailed quotes that
    break down materials, labor, and timeline. Typical patio projects range from
    $5,000 to $25,000 depending on size and complexity. Retaining walls start at
    $45 per square foot.
    """ * 3  # Repeat to make it longer

    chunker = TextChunker(chunk_size=300, chunk_overlap=50, min_chunk_size=50)

    chunks = chunker.chunk_text(sample_text, metadata={'source': 'test'})

    print(f"Created {len(chunks)} chunks:\n")
    for chunk in chunks:
        print(f"Chunk {chunk['chunk_index']}:")
        print(f"  Tokens: {chunk['token_count']}")
        print(f"  Preview: {chunk['content'][:100]}...")
        print()

    print(f"✓ Chunker test complete!")


if __name__ == "__main__":
    test_chunker()
