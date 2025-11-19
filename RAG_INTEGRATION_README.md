# RAG Integration for Keystone Hardscapes

This document describes the RAG (Retrieval-Augmented Generation) integration completed for the My Bot Army platform.

## Files Added

### Core Components

1. **shared/rag_helpers.py** - Helper functions wrapping OOP RAG components
   - `process_document(conn, bot_id, document_id, document_text, voyage_api_key, ...)` 
   - `rag_query(conn, bot_id, user_query, voyage_api_key, top_k=3)`

2. **load_keystone_kb.py** - Knowledge base loader script
   - Loads Keystone Hardscapes documentation into database
   - Processes documents with Voyage AI embeddings
   - Creates searchable chunks for RAG

3. **test_keystone_rag.py** - RAG system test script
   - Tests RAG queries with sample questions
   - Verifies knowledge base is working correctly

### Manual Step Required

**Update shared/rag/__init__.py** to export helper functions.

Apply the changes from `rag_init_update.patch` OR manually add these lines:

```python
# After the existing imports, add:
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rag_helpers import process_document, rag_query
sys.path.pop(0)

# Update __all__ to include:
__all__ = [
    'VoyageClient',
    'TextChunker',
    'DocumentEmbedder',
    'RAGRetriever',
    'process_document',  # Add this
    'rag_query',         # Add this
]
```

## Usage

### Step 1: Ensure Database Tables Exist

The RAG tables should already be created from migration `003_rag_tables.sql`.

Verify:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('documents', 'document_chunks');
```

### Step 2: Load Knowledge Base

```bash
export VOYAGE_API_KEY='your-voyage-api-key'
python3 load_keystone_kb.py
```

This will:
- Load keystone_company.txt
- Load keystone_faq.txt  
- Load any files in knowledge_base/ directory
- Create embeddings for all content
- Store chunks in database

### Step 3: Test RAG System

```bash
python3 test_keystone_rag.py
```

This runs 5 test queries and displays the retrieved context.

### Step 4: Update Bot System Prompt

Modify the Keystone bot's system prompt to include RAG context retrieval.

Example integration:
```python
from shared.rag_helpers import rag_query
from shared.database import get_db_connection

# In your bot handler:
with get_db_connection() as conn:
    context = rag_query(
        conn=conn,
        bot_id=1,  # Keystone bot
        user_query=user_message,
        voyage_api_key=os.getenv('VOYAGE_API_KEY'),
        top_k=3
    )

# Add context to system prompt or user message
```

## Architecture

### Helper Functions

The helper functions bridge the gap between the functional interface (used by tests) and the OOP components (VoyageClient, TextChunker, DocumentEmbedder, RAGRetriever).

**process_document():**
1. Looks up bot_id string from integer ID
2. Retrieves document metadata from database  
3. Chunks the text using TextChunker
4. Generates embeddings with VoyageClient
5. Stores chunks in document_chunks table

**rag_query():**
1. Looks up bot_id string from integer ID
2. Generates query embedding with VoyageClient
3. Searches for similar chunks using RAGRetriever
4. Formats results as context string

### Database Schema

**documents table:**
- Stores complete documents
- Links to bot via bot_id (VARCHAR)

**document_chunks table:**
- Stores individual chunks with embeddings
- Links to documents via document_id
- Uses pgvector for similarity search
- Embedding dimension: 512 (voyage-3-lite) or 1024 (voyage-3)

## Testing

### Unit Tests

Existing tests in `tests/test_rag.py` (51 tests) cover:
- Text chunking
- Voyage AI API calls (mocked)
- Document processing pipeline (mocked)
- RAG query pipeline (mocked)

Run tests:
```bash
pytest tests/test_rag.py -v
```

### Integration Tests

The `test_keystone_rag.py` script performs end-to-end testing with real database and API calls.

## Cost Estimates

**Voyage AI Pricing (voyage-3-lite):**
- $0.06 per 1M tokens
- Typical knowledge base: ~50,000 tokens
- Cost per indexing: ~$0.003
- Cost per query: ~$0.0001

**Total for Keystone KB:**
- Initial indexing: <$0.01
- 1000 queries/month: ~$0.10

## Troubleshooting

**"No chunks found"**
- Run `load_keystone_kb.py` to load the knowledge base

**"Permission denied" on database**
- Check DB_PASSWORD environment variable
- Verify database.py can connect

**"VOYAGE_API_KEY not set"**
- Export the API key: `export VOYAGE_API_KEY='pa-...'`

**"No relevant context found"**
- Check similarity threshold (default: 0.6)
- Verify documents are loaded for the correct bot_id
- Check query matches document content

## Next Steps

1. ✅ Create helper functions (shared/rag_helpers.py)
2. ✅ Create loader script (load_keystone_kb.py)
3. ✅ Create test script (test_keystone_rag.py)
4. ⏳ Update shared/rag/__init__.py (manual step required)
5. ⏳ Load Keystone knowledge base
6. ⏳ Test RAG system
7. ⏳ Integrate with bot system prompt
8. ⏳ Deploy to production

## Files

```
/opt/bot-farm/
├── shared/
│   ├── rag/                      # OOP RAG package
│   │   ├── __init__.py           # Needs manual update
│   │   ├── voyage_client.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   └── retriever.py
│   ├── rag_helpers.py            # ✅ NEW: Helper functions
│   └── database.py
├── load_keystone_kb.py           # ✅ NEW: KB loader
├── test_keystone_rag.py          # ✅ NEW: RAG tester
├── rag_init_update.patch         # Patch for __init__.py
├── keystone_company.txt          # KB: Company info
├── keystone_faq.txt              # KB: FAQ
└── knowledge_base/               # KB: Additional docs
```
