# Changelog

All notable changes to My Bot Army will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
