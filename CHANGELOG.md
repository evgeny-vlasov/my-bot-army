# Changelog

All notable changes to My Bot Army will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-11-29

### Added
- **Psyling Therapist Bot** - Second production bot deployed
  - Port: 5002
  - Bot ID: 2 (therapist)
  - RAG similarity threshold: 0.3 (lower for broader context retrieval)
  - Full knowledge base with therapy practice information

### Fixed
- **Critical RAG Bug**: PostgreSQL query planner issue in vector search
  - **Problem**: Filtering on `d.bot_id` (documents table) combined with ORDER BY on vector distance returned 0 results
  - **Root Cause**: PostgreSQL query planner incorrectly optimized the query when filtering on joined table
  - **Solution**: Changed WHERE clause from `d.bot_id = %s` to `dc.bot_id = %s` (document_chunks table)
  - **Impact**: RAG retrieval now works correctly for all bots
  - **File**: `shared/rag/retriever.py` line 284
  - **Note**: The JOIN with documents table is still required for retrieving document titles and sources

### Changed
- **Documentation Updates**:
  - Updated README.md to include both bots (Keystone and Therapist)
  - Updated ARCHITECTURE.md with dual-bot architecture
  - Updated RAG_INTEGRATION_README.md with bot-specific configurations
  - Added bug fix documentation to code comments
  - Clarified that both bots use voyage-3-lite (512D) embeddings
  - Documented different similarity thresholds per bot

### Technical Details

**Bug Fix - Vector Search Query:**

Before (broken):
```sql
WHERE d.bot_id = %s  -- Filtering on documents table
```

After (working):
```sql
WHERE dc.bot_id = %s  -- Filtering on document_chunks table
```

**Bot Configurations:**
- **Keystone Hardscapes**: SIMILARITY_THRESHOLD = 0.7 (standard precision)
- **Psyling Therapist**: SIMILARITY_THRESHOLD = 0.3 (broader retrieval for therapy context)

Both bots use:
- Embedding model: voyage-3-lite (512 dimensions)
- Top K chunks: 5
- Max context tokens: 2000

---

## [2.0.0] - 2025-11-25

### 🔄 MAJOR ARCHITECTURAL CHANGE: FastAPI → Flask Migration

This release represents a complete migration from FastAPI to Flask to align with the WebGarden infrastructure pattern.

### Changed

**Web Framework:**
- Migrated from FastAPI (async) to Flask 3.x (synchronous)
- Replaced Uvicorn with Gunicorn WSGI server
- Converted async/await patterns to synchronous Python
- Replaced FastAPI routers with Flask Blueprints
- Replaced FastAPI exception handlers with Flask error handlers

**HTTP & API:**
- Replaced Pydantic models with Flask request/response handling
- Replaced `httpx` async HTTP client with `requests` library
- Updated all API endpoints to use Flask decorators (`@app.route()`)
- Maintained identical REST API endpoints (no breaking changes to API contract)

**Database:**
- Replaced async SQLAlchemy with synchronous Flask-SQLAlchemy
- Replaced `asyncpg` with `psycopg2` PostgreSQL adapter
- Updated all database queries to synchronous operations
- No changes to database schema (full backward compatibility)

**Documentation:**
- Updated README.md to reflect Flask architecture
- Added MIGRATION_NOTES.md with detailed migration guide
- Updated all code examples to Flask syntax
- Updated deployment instructions for Gunicorn

### Maintained

**Functionality (100% preserved):**
- ✅ All API endpoints unchanged
- ✅ RAG (Retrieval-Augmented Generation) fully functional
- ✅ Voyage AI embeddings integration
- ✅ pgvector vector search
- ✅ Multi-tenant architecture
- ✅ Conversation management
- ✅ Usage tracking
- ✅ Embeddable chat widget
- ✅ Claude Sonnet 4.5 integration

**Database:**
- ✅ Identical schema
- ✅ Same migrations
- ✅ Full data compatibility

**Features:**
- ✅ All 51 RAG tests still passing
- ✅ Knowledge base management
- ✅ Cost tracking
- ✅ Error handling

### Technical Details

**Before (FastAPI):**
```python
from fastapi import FastAPI
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
    return {"message": response}
```

**After (Flask):**
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    response = requests.post(...)
    return jsonify({"message": response})
```

### Migration Impact

**Benefits:**
- ✅ Seamless integration with WebGarden Flask infrastructure
- ✅ Simpler synchronous code (easier to understand and debug)
- ✅ Proven Flask + Gunicorn + PostgreSQL production pattern
- ✅ Better compatibility with existing Flask-based tools and libraries
- ✅ No async complexity for straightforward CRUD operations

**Trade-offs:**
- ⚠️ Lost async/await concurrency (acceptable for current use case)
- ⚠️ Gunicorn multi-worker model instead of async event loop
- ⚠️ Sequential request handling per worker (mitigated by multiple workers)

### Deployment

**New production deployment:**
```bash
gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 120 app:app
```

**Development (unchanged):**
```bash
python3 app.py
```

### Breaking Changes

**For Developers:**
- Python code must be updated if importing from this codebase
- Async functions converted to sync (breaking change for async callers)
- Import paths remain the same

**For API Consumers:**
- ✅ **NO BREAKING CHANGES** - All REST API endpoints identical
- ✅ Request/response formats unchanged
- ✅ Authentication unchanged (if implemented)

### See Also

- [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) - Detailed migration guide and differences
- [README.md](./README.md) - Updated documentation with Flask examples

---

## [1.1.0] - 2025-11-19

### Added
- Complete RAG integration with Voyage AI embeddings
- Database schema alignment between bots and shared components
- Full integration verification and testing

### Fixed
- RAG system initialization in Flask bots
- Document chunking and embedding storage
- Vector search query alignment

---

## [1.0.0] - 2025-11-18

### Added
- Initial production-ready release
- Keystone Hardscapes bot deployment
- RAG system with pgvector
- Flask-based chat endpoint
- Embeddable JavaScript widget
- Multi-tenant database schema
- Usage tracking and cost monitoring

### Features
- Claude Sonnet 4.5 integration
- PostgreSQL with pgvector extension
- Conversation history
- Knowledge base management
- Test suite (51 RAG tests)

---

## [0.1.0] - 2025-11-15

### Added
- Initial FastAPI prototype (now deprecated)
- Basic bot framework
- Database schema design
- Claude API integration

---

**Note:** This changelog focuses on the Flask migration (v2.0.0) as a critical architectural change. Previous versions represent the FastAPI prototype phase.
