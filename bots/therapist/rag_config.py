"""
RAG Configuration for Therapist Bot

This file contains all RAG-specific settings for the Therapist bot.
Modify these values to tune retrieval quality and performance.
"""

# =============================================================================
# Retrieval Settings
# =============================================================================

# Number of most relevant chunks to retrieve
TOP_K_CHUNKS = 5

# Minimum similarity score (0-1) for chunks to be included
# Higher = more strict matching, Lower = more results
# Recommended range: 0.6 - 0.8
SIMILARITY_THRESHOLD = 0.3

# Maximum tokens to include in context sent to Claude
# Claude Sonnet has large context window, but keeping it focused helps quality
MAX_CONTEXT_TOKENS = 2000

# =============================================================================
# Chunking Settings
# =============================================================================

# Target size for each chunk in tokens
# Larger chunks = more context per chunk but fewer total chunks
# Smaller chunks = more granular retrieval but may lose context
CHUNK_SIZE = 800

# Number of tokens to overlap between consecutive chunks
# Prevents information loss at chunk boundaries
CHUNK_OVERLAP = 150

# Minimum chunk size - chunks smaller than this are discarded
MIN_CHUNK_SIZE = 100

# =============================================================================
# Voyage AI Settings
# =============================================================================

# Embedding model to use
# Options:
#   "voyage-3-lite" - 512 dimensions, $0.06/1M tokens (recommended)
#   "voyage-3" - 1024 dimensions, $0.12/1M tokens (higher quality)
VOYAGE_MODEL = "voyage-3-lite"

# Embedding dimension (must match model)
EMBEDDING_DIMENSION = 512  # 512 for voyage-3-lite, 1024 for voyage-3

# =============================================================================
# RAG System Prompt Addition
# =============================================================================

# This instruction is added to the bot's system prompt when RAG context is available
RAG_SYSTEM_INSTRUCTION = """
IMPORTANT - Knowledge Base Usage:

You have access to the therapy practice's knowledge base documents provided below as context.
Follow these rules when using the knowledge base:

1. PRIORITIZE KNOWLEDGE BASE: Always prefer information from the provided context over
   your general knowledge about therapy or mental health practices.

2. CITE SOURCES: When you use information from the knowledge base, cite it naturally:
   - "According to our practice information..."
   - "As outlined in our services guide..."
   - "Our practice offers..."
   - "[Source: Insurance Information]"

3. BE HONEST ABOUT GAPS: If the context doesn't contain the answer to a question,
   be honest and say something like:
   - "I don't see that specific information in our current materials..."
   - "While I don't have exact details on that, let me share what I do know..."
   - "That's a great question! For specific details, I'd recommend contacting the
     practice directly at [contact info]."

4. COMBINE APPROPRIATELY: You can combine knowledge base info with general
   psychoeducational knowledge, but make it clear what comes from where:
   - "Our practice offers CBT for anxiety. Generally speaking, CBT is effective
     because it helps identify and change thought patterns..."

5. DON'T HALLUCINATE: Never make up specific details about the practice:
   - Exact pricing or fees
   - Insurance acceptance beyond what's documented
   - Therapist credentials or specializations not mentioned
   - Specific policies or procedures
   - Availability or scheduling details

6. MAINTAIN BOUNDARIES: Even with knowledge base access, remember:
   - You cannot provide therapy or clinical advice
   - You cannot diagnose conditions
   - Always prioritize crisis resources when appropriate
   - Respect privacy and confidentiality limitations

7. MAINTAIN PERSONALITY: Use the knowledge base to enhance your responses, but
   maintain your warm, empathetic, and professional tone. Don't sound like you're
   just reading from a manual.

Remember: The goal is to be helpful, accurate, and honest while maintaining professional
boundaries. If you're not sure, it's always better to offer to have them contact the
practice directly than to guess.
"""

# =============================================================================
# Feature Flags
# =============================================================================

# Enable/disable RAG globally for this bot
RAG_ENABLED = True

# Whether to include source citations in formatted context
INCLUDE_SOURCE_CITATIONS = True

# Whether to log which chunks were used for each response
# (Stored in messages.context_chunks field)
LOG_CONTEXT_CHUNKS = True

# Whether to fall back to non-RAG mode if no relevant chunks found
FALLBACK_WITHOUT_CONTEXT = True

# =============================================================================
# Performance Settings
# =============================================================================

# Timeout for Voyage API calls (seconds)
VOYAGE_API_TIMEOUT = 30

# Maximum retries for failed API calls
MAX_API_RETRIES = 3

# Cache query embeddings (reduces API calls for repeated queries)
# Note: Requires additional caching implementation
CACHE_EMBEDDINGS = False

# =============================================================================
# Development/Debug Settings
# =============================================================================

# Log detailed RAG operations (useful for debugging)
DEBUG_RAG = False

# Include similarity scores in source citations (for testing)
SHOW_SIMILARITY_SCORES = False


# =============================================================================
# Helper Functions
# =============================================================================

def get_rag_enabled() -> bool:
    """
    Check if RAG is enabled for this bot.

    Returns:
        True if RAG should be used, False otherwise
    """
    import os

    # Can be overridden by environment variable
    env_enabled = os.getenv('THERAPIST_RAG_ENABLED', '').lower()
    if env_enabled in ('false', '0', 'no'):
        return False
    elif env_enabled in ('true', '1', 'yes'):
        return True

    # Default to config value
    return RAG_ENABLED


def get_config_summary() -> str:
    """
    Get a summary of current RAG configuration.

    Returns:
        Formatted configuration summary
    """
    return f"""
Therapist Bot RAG Configuration:
  Enabled: {RAG_ENABLED}
  Model: {VOYAGE_MODEL} ({EMBEDDING_DIMENSION}D)
  Retrieval: Top {TOP_K_CHUNKS} chunks, threshold {SIMILARITY_THRESHOLD}
  Chunking: {CHUNK_SIZE} tokens/chunk, {CHUNK_OVERLAP} overlap
  Context: Max {MAX_CONTEXT_TOKENS} tokens
  Citations: {INCLUDE_SOURCE_CITATIONS}
  Logging: {LOG_CONTEXT_CHUNKS}
    """.strip()


if __name__ == "__main__":
    # Print config when run directly
    print(get_config_summary())
