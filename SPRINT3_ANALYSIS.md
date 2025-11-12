# Sprint 3 RAG Implementation - Repository Analysis

## Repository Structure Findings

### Key Discrepancies from Sprint Prompt

1. **Base Path**:
   - **Prompt expects**: `/opt/bot-farm/`
   - **Actual path**: `/home/user/my-bot-army/`

2. **Existing RAG Infrastructure**:
   - **FastAPI app** already has partial RAG implementation:
     - `my_bot_army/app/services/rag_service.py` (basic vector search)
     - `my_bot_army/app/services/embedding_service.py` (placeholder)
     - `my_bot_army/app/schemas/document.py` (SQLAlchemy model)
   - **Current approach**: Document-level embeddings (1536 dimensions for OpenAI)
   - **Sprint approach**: Chunk-level embeddings (512/1024 dimensions for Voyage AI)

3. **Database Setup**:
   - Legacy schema in `schema.sql` (8 tables, no documents table)
   - FastAPI has SQLAlchemy schema with documents table
   - **Need to create**: Separate migration for chunk-based RAG tables

## Implementation Plan

### Approach: Dual RAG System

We'll implement the RAG system as specified in Sprint 3 while keeping the existing FastAPI implementation:

1. **Legacy Flask Bot RAG** (Sprint 3 focus):
   - Location: `shared/rag/` (for use by Flask bots like Keystone)
   - Uses Voyage AI embeddings
   - Chunk-based approach
   - Direct psycopg2 database access
   - Target: Keystone bot at `bots/keystone-landscaping/`

2. **Modern FastAPI RAG** (preserve existing):
   - Location: `my_bot_army/app/services/`
   - Keep existing implementation
   - Can upgrade to use Voyage/chunking later

### Directory Structure to Create

```
/home/user/my-bot-army/
├── shared/
│   └── rag/                          # NEW: RAG module for Flask bots
│       ├── __init__.py
│       ├── voyage_client.py          # Voyage AI API wrapper
│       ├── chunker.py                # Text chunking utilities
│       ├── embedder.py               # Document processing + embedding
│       └── retriever.py              # Vector similarity search
├── bots/
│   └── keystone-landscaping/
│       ├── rag_config.py             # NEW: Bot-specific RAG settings
│       ├── knowledge_base/           # NEW: Source documents directory
│       │   ├── README.md
│       │   └── services_overview.txt
│       └── app.py                    # MODIFY: Add RAG integration
├── scripts/
│   ├── add_document.py               # NEW: CLI to add documents
│   ├── test_rag.py                   # NEW: CLI to test RAG
│   └── reindex_bot.py                # NEW: CLI to regenerate embeddings
└── migrations/
    └── 003_rag_tables.sql            # NEW: Database migration
```

### Database Changes

Create new tables in PostgreSQL:

```sql
-- Store complete documents
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(100) NOT NULL REFERENCES bots(bot_id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store document chunks with embeddings
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding vector(512),  -- Voyage-3-lite dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add optional context tracking to messages
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS context_chunks JSONB DEFAULT '[]';

-- Indexes
CREATE INDEX idx_documents_bot_id ON documents(bot_id);
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

Note: References `bots(bot_id)` as VARCHAR since that's the current schema.

### Voyage AI Configuration

**Model**: `voyage-3-lite`
- 512 dimensions
- $0.06/1M tokens
- Optimized for retrieval

**API Endpoint**: `https://api.voyageai.com/v1/embeddings`

Need to add to `.env`:
```bash
VOYAGE_API_KEY=pa-your-voyage-api-key-here
```

### Integration Points

1. **Keystone Bot** (`bots/keystone-landscaping/app.py`):
   - Import RAG modules from `shared.rag`
   - Add RAG search before Claude API call
   - Enhance system prompt with retrieved context
   - Track which chunks were used in responses

2. **Database Access**:
   - Use existing `shared/database.py` patterns
   - Direct psycopg2 queries for vector search
   - Compatible with current bot architecture

3. **Testing**:
   - CLI scripts for manual testing
   - Integration tests via `/api/chat` endpoint
   - Widget testing at `/test`

## Next Steps

1. ✅ Repository analysis complete
2. Create database migration SQL
3. Implement `shared/rag/` modules
4. Integrate into Keystone bot
5. Create CLI tools
6. Test end-to-end with sample documents

## Notes

- PostgreSQL must have pgvector extension installed
- Need Voyage AI API key before testing
- Existing FastAPI RAG can be upgraded separately
- This implementation is backward compatible with existing bots
