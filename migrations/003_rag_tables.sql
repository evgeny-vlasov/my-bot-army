-- Migration 003: RAG (Retrieval-Augmented Generation) Tables
-- Sprint 3: Implement chunk-based document storage with vector embeddings
-- Dependencies: Requires pgvector extension

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- Table: documents
-- Purpose: Store complete documents for each bot's knowledge base
-- =============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(100) NOT NULL REFERENCES bots(bot_id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255),  -- e.g., 'uploaded_pdf', 'website', 'manual_entry'
    metadata JSONB DEFAULT '{}',  -- Stores {file_name, url, author, date, category, etc}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for documents table
CREATE INDEX IF NOT EXISTS idx_documents_bot_id ON documents(bot_id);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);

-- Comment on documents table
COMMENT ON TABLE documents IS 'Complete documents uploaded to each bot knowledge base';
COMMENT ON COLUMN documents.bot_id IS 'Reference to bots(bot_id) - VARCHAR format';
COMMENT ON COLUMN documents.metadata IS 'JSON metadata: file_name, upload_date, category, tags, etc';

-- =============================================================================
-- Table: document_chunks
-- Purpose: Store individual chunks with embeddings for vector similarity search
-- =============================================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,  -- Position in original document (0, 1, 2...)
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding vector(512),  -- 512 dimensions for voyage-3-lite, change to 1024 for voyage-3
    metadata JSONB DEFAULT '{}',  -- Can store chunk-specific info like section, page, etc
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document_chunks table
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON document_chunks(chunk_index);

-- Vector index for fast similarity search (CRITICAL for performance)
-- Using ivfflat (Inverted File with Flat compression)
-- lists = 100 is good for datasets up to ~100K chunks
-- Adjust based on data size: sqrt(total_rows) is a good rule of thumb
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Comment on document_chunks table
COMMENT ON TABLE document_chunks IS 'Individual chunks of documents with vector embeddings for RAG';
COMMENT ON COLUMN document_chunks.chunk_index IS 'Sequential position of chunk in parent document';
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding from Voyage AI (voyage-3-lite: 512d)';
COMMENT ON COLUMN document_chunks.token_count IS 'Approximate token count for context window management';

-- =============================================================================
-- Table Modification: messages
-- Purpose: Track which document chunks were used in each assistant response
-- =============================================================================
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS context_chunks JSONB DEFAULT '[]';

-- Comment on new column
COMMENT ON COLUMN messages.context_chunks IS 'Array of chunks used: [{chunk_id, similarity, document_title, source}]';

-- =============================================================================
-- Helper Views (Optional - for analytics and debugging)
-- =============================================================================

-- View: Document statistics per bot
CREATE OR REPLACE VIEW v_bot_document_stats AS
SELECT
    b.bot_id,
    b.bot_name,
    COUNT(DISTINCT d.id) as document_count,
    COUNT(dc.id) as chunk_count,
    SUM(dc.token_count) as total_tokens,
    MAX(d.created_at) as last_document_added
FROM bots b
LEFT JOIN documents d ON b.bot_id = d.bot_id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY b.bot_id, b.bot_name;

COMMENT ON VIEW v_bot_document_stats IS 'Summary statistics of documents and chunks per bot';

-- View: Recent documents with chunk counts
CREATE OR REPLACE VIEW v_recent_documents AS
SELECT
    d.id,
    d.bot_id,
    d.title,
    d.source,
    COUNT(dc.id) as chunk_count,
    SUM(dc.token_count) as total_tokens,
    d.created_at
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id, d.bot_id, d.title, d.source, d.created_at
ORDER BY d.created_at DESC;

COMMENT ON VIEW v_recent_documents IS 'Recent documents with aggregated chunk statistics';

-- =============================================================================
-- Functions
-- =============================================================================

-- Function to update document updated_at timestamp
CREATE OR REPLACE FUNCTION update_document_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update document timestamps
DROP TRIGGER IF EXISTS trg_documents_updated_at ON documents;
CREATE TRIGGER trg_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_document_timestamp();

-- Function to get similar chunks (example query function)
CREATE OR REPLACE FUNCTION get_similar_chunks(
    p_bot_id VARCHAR(100),
    p_query_embedding vector(512),
    p_limit INTEGER DEFAULT 5,
    p_similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    chunk_id INTEGER,
    document_id INTEGER,
    document_title VARCHAR(500),
    chunk_content TEXT,
    chunk_index INTEGER,
    similarity FLOAT,
    source VARCHAR(255)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id as chunk_id,
        dc.document_id,
        d.title as document_title,
        dc.content as chunk_content,
        dc.chunk_index,
        1 - (dc.embedding <=> p_query_embedding) as similarity,
        d.source
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE d.bot_id = p_bot_id
      AND dc.embedding IS NOT NULL
      AND (1 - (dc.embedding <=> p_query_embedding)) >= p_similarity_threshold
    ORDER BY dc.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_similar_chunks IS 'Find similar document chunks using vector similarity search';

-- =============================================================================
-- Verification Queries
-- =============================================================================

-- Verify pgvector extension
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Verify tables created
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('documents', 'document_chunks')
ORDER BY table_name;

-- Verify indexes created
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('documents', 'document_chunks')
ORDER BY tablename, indexname;

-- =============================================================================
-- Migration Complete
-- =============================================================================

-- Insert migration record (if you have a migrations tracking table)
-- If not, this serves as documentation

-- Migration: 003_rag_tables.sql
-- Applied: [Timestamp will be added when run]
-- Description: Create RAG tables for chunk-based document storage with vector embeddings
-- Tables created: documents, document_chunks
-- Tables modified: messages (added context_chunks column)
-- Extension required: pgvector
