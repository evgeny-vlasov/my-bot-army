# FastAPI → Flask Migration Guide

**Version:** 2.0.0
**Migration Date:** November 25, 2025
**Status:** ✅ Complete

This document explains the architectural migration from FastAPI to Flask and provides guidance for understanding the differences.

---

## 📋 Table of Contents

1. [Why Migrate?](#why-migrate)
2. [High-Level Changes](#high-level-changes)
3. [Technology Mapping](#technology-mapping)
4. [Code Examples](#code-examples)
5. [Database Changes](#database-changes)
6. [Deployment Changes](#deployment-changes)
7. [Performance Considerations](#performance-considerations)
8. [Migration Checklist](#migration-checklist)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Why Migrate?

### Business Reasons

**Integration with WebGarden Infrastructure:**
- My Bot Army now integrates with the WebGarden Flask infrastructure
- WebGarden uses the proven Flask + SQLAlchemy + PostgreSQL + Gunicorn pattern
- Consistency across the infrastructure reduces maintenance overhead
- Shared libraries and patterns across WebGarden projects

### Technical Reasons

**Simplicity over Complexity:**
- The bot application doesn't require async/await complexity
- Most operations are I/O-bound to external APIs (Claude, Voyage)
- Synchronous code is easier to understand, debug, and maintain
- No concurrent request processing needed within a single worker

**Proven Production Pattern:**
- Flask + Gunicorn is battle-tested for production deployments
- Multi-worker process model handles concurrency effectively
- Better tooling and ecosystem support for Flask in our stack

---

## 🔄 High-Level Changes

### Architecture Shift

```
FastAPI (Async)                    Flask (Sync)
├── Async event loop               ├── Synchronous WSGI
├── Single process, many tasks     ├── Multiple workers, one request per worker
├── async/await throughout         ├── Standard synchronous Python
└── Uvicorn ASGI server            └── Gunicorn WSGI server
```

### Key Differences

| Aspect | FastAPI | Flask |
|--------|---------|-------|
| **Concurrency Model** | Async/await (event loop) | Multi-process workers |
| **Server** | Uvicorn (ASGI) | Gunicorn (WSGI) |
| **Database** | async SQLAlchemy | sync SQLAlchemy |
| **HTTP Client** | httpx (async) | requests (sync) |
| **Route Definition** | `@app.post()` decorators | `@app.route(methods=["POST"])` |
| **Request Validation** | Pydantic models | Flask request parsing |
| **Response** | Auto JSON serialization | `jsonify()` or dict |
| **Error Handling** | Exception handlers | `@app.errorhandler()` |
| **OpenAPI/Swagger** | Built-in, automatic | Manual (flask-swagger) |

---

## 🔀 Technology Mapping

### Web Framework

**FastAPI → Flask**

```python
# FastAPI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
    return {"response": "Hello"}
```

```python
# Flask
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")
    session_id = data.get("session_id")
    return jsonify({"response": "Hello"})
```

### HTTP Client

**httpx (async) → requests (sync)**

```python
# FastAPI with httpx
import httpx

async def call_api():
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

```python
# Flask with requests
import requests

def call_api():
    response = requests.post(url, json=data)
    return response.json()
```

### Database Operations

**async SQLAlchemy → sync SQLAlchemy**

```python
# FastAPI (async)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

async def get_bot(bot_id: int):
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Bot).where(Bot.id == bot_id)
        )
        return result.scalar_one()
```

```python
# Flask (sync)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

def get_bot(bot_id: int):
    with Session(engine) as session:
        return session.query(Bot).filter(Bot.id == bot_id).first()
```

### Error Handling

**FastAPI Exception Handlers → Flask Error Handlers**

```python
# FastAPI
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

# Raise errors
raise HTTPException(status_code=404, detail="Bot not found")
```

```python
# Flask
from flask import jsonify
from werkzeug.exceptions import HTTPException

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Bot not found"}), 404

@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return jsonify({"error": error.description}), error.code
    return jsonify({"error": "Internal server error"}), 500

# Raise errors
from werkzeug.exceptions import NotFound
raise NotFound("Bot not found")
```

### Route Organization

**FastAPI Routers → Flask Blueprints**

```python
# FastAPI
from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.post("/chat")
async def chat():
    pass

app.include_router(router)
```

```python
# Flask
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/chat", methods=["POST"])
def chat():
    pass

app.register_blueprint(api_bp)
```

---

## 💾 Database Changes

### Schema: No Changes! ✅

The database schema remains **100% identical**:
- Same tables (clients, bots, conversations, messages, documents, document_chunks, api_usage)
- Same columns and data types
- Same indexes and constraints
- Same pgvector embeddings
- Same migrations

### Connection: Sync vs Async

**FastAPI (async):**
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/botfarm"
)
```

**Flask (sync):**
```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://user:pass@localhost/botfarm"
)
```

### Query Patterns

**FastAPI:**
```python
async with AsyncSession(engine) as session:
    result = await session.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one()
```

**Flask:**
```python
with Session(engine) as session:
    bot = session.query(Bot).filter(Bot.id == bot_id).first()
```

---

## 🚀 Deployment Changes

### Development Server

**FastAPI:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Flask:**
```bash
# Option 1: Flask built-in
python3 app.py

# Option 2: Flask CLI
flask run --host 0.0.0.0 --port 5001
```

### Production Server

**FastAPI:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

**Flask:**
```bash
gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 120 app:app
```

### Process Management (systemd)

**FastAPI systemd service:**
```ini
[Service]
ExecStart=/opt/bot-farm/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

**Flask systemd service:**
```ini
[Service]
ExecStart=/opt/bot-farm/venv/bin/gunicorn --bind 0.0.0.0:5001 --workers 4 app:app
```

### Configuration

**Similarities:**
- Both use `.env` files
- Both use environment variables
- Both support `config.py` for settings

**Differences:**
- Flask uses `app.config` dictionary
- FastAPI typically uses Pydantic `Settings` models

---

## ⚡ Performance Considerations

### Concurrency Models

**FastAPI (Async):**
- Single process with event loop
- Handles many concurrent requests via async/await
- Excellent for I/O-bound operations
- One request can't block others
- More complex to debug

**Flask + Gunicorn (Multi-process):**
- Multiple worker processes
- Each worker handles one request at a time
- Workers can run on multiple CPU cores
- Simpler mental model
- More memory usage (multiple processes)

### Performance Comparison

| Metric | FastAPI | Flask + Gunicorn |
|--------|---------|------------------|
| **Concurrent Requests** | High (event loop) | Medium (workers × 1) |
| **CPU Usage** | Single core | Multi-core |
| **Memory** | Lower (one process) | Higher (multiple processes) |
| **Latency** | Lower (no context switching) | Slightly higher |
| **Throughput** | High for many small requests | High for mixed workloads |
| **Simplicity** | Lower (async complexity) | Higher (standard Python) |

### For This Use Case

**Bot Army Characteristics:**
- Most time spent waiting for Claude API (1-2 seconds)
- Most time spent waiting for Voyage API (200-400ms)
- Database queries are fast (50-100ms)
- Low to medium request volume
- Not CPU-intensive

**Verdict:**
✅ Flask + Gunicorn is **perfectly suitable** for this workload. The benefits of async are minimal when 95% of time is waiting for external APIs.

---

## ✅ Migration Checklist

### Code Migration

- [x] Replace FastAPI with Flask
- [x] Convert async functions to sync
- [x] Replace httpx with requests
- [x] Replace Pydantic models with dict/JSON
- [x] Update route decorators
- [x] Update error handlers
- [x] Replace async SQLAlchemy with sync
- [x] Update database connection string (asyncpg → psycopg2)

### Testing

- [x] Run all unit tests
- [x] Run integration tests
- [x] Test RAG functionality (51 tests passing)
- [x] Test API endpoints
- [x] Test database operations
- [x] Test error handling

### Documentation

- [x] Update README.md
- [x] Update code examples
- [x] Update deployment instructions
- [x] Create CHANGELOG.md
- [x] Create MIGRATION_NOTES.md

### Deployment

- [x] Update requirements.txt (add gunicorn, document legacy FastAPI deps)
- [x] Document systemd service examples (in README.md)
- [x] Document Gunicorn configuration (in README.md and ARCHITECTURE.md)
- [ ] Update Nginx/reverse proxy config (if applicable)
- [ ] Update monitoring and logging
- [ ] Deploy to staging
- [ ] Deploy to production

---

## 🐛 Troubleshooting

### "async/await not working"

**Problem:** Trying to use `await` in Flask code
```python
@app.route("/api/chat")
def chat():
    result = await some_function()  # ❌ SyntaxError
```

**Solution:** Remove async/await, use synchronous calls
```python
@app.route("/api/chat")
def chat():
    result = some_function()  # ✅ Works
```

### "requests library not installed"

**Problem:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip install requests
```

### "psycopg2 not installed"

**Problem:** `ModuleNotFoundError: No module named 'psycopg2'`

**Solution:**
```bash
pip install psycopg2-binary
```

### "Gunicorn not found"

**Problem:** `command not found: gunicorn`

**Solution:**
```bash
pip install gunicorn
```

### "Database connection error"

**Problem:** FastAPI connection string used with Flask

**Solution:** Update connection string:
```python
# Wrong (FastAPI async)
DATABASE_URL = "postgresql+asyncpg://..."

# Correct (Flask sync)
DATABASE_URL = "postgresql+psycopg2://..."
```

### "Port already in use"

**Problem:** Both FastAPI and Flask trying to use same port

**Solution:** Stop old service or use different port
```bash
sudo systemctl stop keystone-bot-fastapi
# OR
gunicorn --bind 0.0.0.0:5002 app:app  # Different port
```

---

## 📚 Additional Resources

### Flask Documentation
- [Flask Quickstart](https://flask.palletsprojects.com/en/latest/quickstart/)
- [Flask Patterns](https://flask.palletsprojects.com/en/latest/patterns/)
- [Flask API](https://flask.palletsprojects.com/en/latest/api/)

### Gunicorn
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Deployment Options](https://docs.gunicorn.org/en/stable/deploy.html)
- [Configuration](https://docs.gunicorn.org/en/stable/settings.html)

### SQLAlchemy
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)

### Comparison Articles
- [FastAPI vs Flask](https://testdriven.io/blog/fastapi-vs-flask/)
- [Async vs Sync Python](https://realpython.com/async-io-python/)

---

## 🤝 Questions?

If you encounter issues during migration or have questions about the Flask implementation:

1. Check this migration guide first
2. Review the updated [README.md](./README.md)
3. Check [CHANGELOG.md](./CHANGELOG.md) for version-specific changes
4. Open an issue on GitHub with details

---

**Last Updated:** November 25, 2025
**Migration Status:** ✅ Complete
**Flask Version:** 3.x
**Python Version:** 3.11+
