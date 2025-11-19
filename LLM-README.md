# My Bot Army - LLM Context Guide

> **Purpose:** This document helps Claude (or any LLM) quickly understand the My Bot Army project when starting a fresh conversation. Read this first to get complete context.

**Last Updated:** November 19, 2025
**Project Status:** ✅ Production-Ready with RAG Integration
**Primary System:** Flask-based Keystone Hardscapes Bot

---

## Quick Start for LLMs

**What is this?** A multi-tenant AI chatbot platform for deploying custom Claude-powered assistants with knowledge bases.

**Current State:** One production bot (Keystone Hardscapes) fully operational with RAG (Retrieval-Augmented Generation) using Voyage AI embeddings and pgvector.

**Your Role:** You're helping develop, maintain, and extend this platform.

---

## Project Architecture

### Two Systems (Important!)

This repository contains **TWO** bot systems:

#### 1. **ACTIVE: Flask-based Bots** (`bots/` directory) ⭐
- **Status:** Production, actively used
- **Location:** `/opt/bot-farm/bots/keystone-landscaping/`
- **Framework:** Flask + Claude API
- **RAG:** ✅ Fully integrated (Voyage AI + pgvector)
- **Database:** PostgreSQL with pgvector extension
- **Current Bot:** Keystone Hardscapes landscaping assistant

#### 2. **Legacy: FastAPI System** (`my_bot_army/` directory)
- **Status:** Prototype/reference code
- **Location:** `/opt/bot-farm/my_bot_army/`
- **Framework:** FastAPI (async)
- **Note:** Not currently deployed, may be used for future bots

**👉 When working on the chatbot, focus on `bots/keystone-landscaping/`**

---

## System Overview

### Technology Stack

```
Production Stack (Keystone Bot):
├── Flask 3.x                    # Web framework
├── Claude Sonnet 4.5            # LLM (Anthropic API)
├── Voyage AI voyage-3-lite      # Embeddings (512D, $0.06/1M tokens)
├── PostgreSQL 15+               # Database
├── pgvector                     # Vector similarity search
└── Python 3.11                  # Runtime

Development:
├── pytest                       # Testing
├── psycopg2                     # PostgreSQL driver
└── python-dotenv                # Environment management
```

### Database Schema

**Key Tables:**
- `clients` - Business clients who own bots
- `bots` - Bot configurations and prompts
- `conversations` - Chat sessions
- `messages` - Individual messages in conversations
- `documents` - Knowledge base documents (RAG)
- `document_chunks` - Chunked documents with embeddings (RAG)
- `api_usage` - Usage tracking and billing

**Important:** `bot_id` is an integer (PK) in most tables, but also has a string `bot_id` field (like 'keystone-landscaping') for API access.

---

## Directory Structure

```
/opt/bot-farm/
│
├── bots/                              # Flask-based bots (ACTIVE)
│   └── keystone-landscaping/          # Production bot
│       ├── app.py                     # Main Flask application ⭐
│       ├── config.py                  # Bot configuration
│       ├── prompts.py                 # System prompts
│       ├── rag_config.py              # RAG settings ⭐
│       └── knowledge_base/            # KB files (txt)
│
├── shared/                            # Shared modules
│   ├── database.py                    # DB functions + DatabaseConnection ⭐
│   ├── claude_client.py               # Claude API wrapper
│   ├── rag_helpers.py                 # RAG helper functions ⭐
│   ├── rag/                           # RAG OOP components ⭐
│   │   ├── __init__.py
│   │   ├── voyage_client.py           # Voyage AI API wrapper
│   │   ├── retriever.py               # Vector search
│   │   ├── chunker.py                 # Text chunking
│   │   └── embedder.py                # Document processing
│   └── widget/                        # Chat widget (JavaScript)
│       └── bot-widget.js
│
├── admin/                             # Admin dashboard (Flask)
│   ├── app.py                         # Dashboard app
│   └── templates/                     # HTML templates
│
├── my_bot_army/                       # FastAPI system (legacy/reference)
│   └── app/                           # FastAPI application
│
├── tests/                             # Test suites
│   └── test_rag.py                    # RAG system tests (51 tests)
│
├── migrations/                        # Database migrations (SQL)
├── scripts/                           # Utility scripts
├── knowledge_base/                    # Source KB files
│   └── keystone/                      # Keystone-specific files
│
├── docs/                              # Documentation
│   └── sprints/                       # Sprint reports
│
├── .env                               # Environment variables (API keys)
├── requirements.txt                   # Python dependencies
│
└── [Documentation Files]              # See below
```

---

## RAG System (Most Important!)

### Overview

The RAG system retrieves relevant information from the knowledge base before generating responses.

### Flow

```
User Query
    ↓
1. Generate embedding (Voyage AI)
    ↓
2. Vector search (pgvector cosine similarity)
    ↓
3. Retrieve top K chunks
    ↓
4. Inject into system prompt
    ↓
5. Call Claude API
    ↓
Response
```

### Implementation

**Location:** `bots/keystone-landscaping/app.py` lines 416-446

**Key Components:**
- `VoyageClient` - Generates embeddings
- `RAGRetriever` - Performs vector search
- `DatabaseConnection` - Wraps DB access
- Enhanced system prompt - Injects context

**Configuration:** `bots/keystone-landscaping/rag_config.py`
```python
TOP_K_CHUNKS = 5                    # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.7          # Minimum similarity (0-1)
MAX_CONTEXT_TOKENS = 2000           # Max tokens in context
VOYAGE_MODEL = "voyage-3-lite"      # Embedding model (512D)
RAG_ENABLED = True                  # Master switch
```

### Knowledge Base Status

**Current Content:**
- Document ID 8: Keystone Company Information (2,611 chars, 1 chunk)
- Document ID 9: Keystone FAQ (5,088 chars, 2 chunks)
- **Total:** 2 documents, 3 chunks, all with embeddings

**To Add More:**
1. Place .txt files in `/opt/bot-farm/knowledge_base/keystone/`
2. Run: `python3 load_keystone_kb.py`
3. Chunks are automatically created and embedded

---

## Key Files Reference

### Core Application Files

| File | Purpose | Status |
|------|---------|--------|
| `bots/keystone-landscaping/app.py` | Main Flask app with RAG | ✅ Production |
| `bots/keystone-landscaping/config.py` | Bot config (ID, name, port) | ✅ Active |
| `bots/keystone-landscaping/prompts.py` | System prompts | ✅ Active |
| `bots/keystone-landscaping/rag_config.py` | RAG configuration | ✅ Active |
| `shared/database.py` | Database functions | ✅ Active |
| `shared/claude_client.py` | Claude API wrapper | ✅ Active |
| `shared/rag_helpers.py` | RAG helper functions | ✅ Active |

### RAG Module Files

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `shared/rag/voyage_client.py` | Voyage AI API | `VoyageClient` |
| `shared/rag/retriever.py` | Vector search | `RAGRetriever` |
| `shared/rag/chunker.py` | Text chunking | `TextChunker` |
| `shared/rag/embedder.py` | Doc processing | `DocumentEmbedder` |
| `shared/rag_helpers.py` | Simple functions | `process_document()`, `rag_query()` |

### Utility Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `load_keystone_kb.py` | Load knowledge base | `python3 load_keystone_kb.py` |
| `test_keystone_rag.py` | Test RAG queries | `python3 test_keystone_rag.py` |
| `test_keystone_chat_with_rag.py` | Test chat endpoint | `python3 test_keystone_chat_with_rag.py` |

### Documentation Files

| File | Purpose | Read When... |
|------|---------|--------------|
| `LLM-README.md` | This file! Context for LLMs | Starting fresh chat |
| `README.md` | Main project README | Understanding project |
| `FLASK_RAG_INTEGRATION.md` | RAG integration details | Working with RAG |
| `DEPLOYMENT_VERIFICATION.md` | Deployment report | Verifying deployment |
| `PROJECT_STRUCTURE.md` | Detailed structure | Understanding codebase |
| `QUICKSTART.md` | Quick setup guide | Setting up locally |

---

## Environment Setup

### Required Environment Variables

Located in `/opt/bot-farm/.env`:

```bash
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-...

# Voyage AI Embeddings
VOYAGE_API_KEY=pa-...

# Database
DB_PASSWORD=your_db_password

# Bot Configuration
BOT_ID=keystone-landscaping
BOT_NAME=Keystone Hardscapes Assistant
PORT=5001
```

### Database Connection

**Config:**
- Host: localhost
- Database: botfarm
- User: botfarm
- Password: from `DB_PASSWORD` env var
- Port: 5432 (default)

**Connection String:** Configured in `.pgpass` file for user `chip`

---

## Common Tasks

### Starting the Keystone Bot

```bash
cd /opt/bot-farm/bots/keystone-landscaping
python3 app.py

# Should see:
# ✓ Claude client initialized successfully
# ✓ RAG system initialized (model: voyage-3-lite)
# ✓ Bot 'Keystone Hardscapes Assistant' connected to database
# Running on http://localhost:5001
```

### Testing the Chat Endpoint

```bash
# Start bot first
cd /opt/bot-farm/bots/keystone-landscaping
python3 app.py &

# Send test message
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services do you offer?", "session_id": "test123"}'

# Check logs for: "RAG: Found X relevant chunks"
```

### Loading Knowledge Base

```bash
cd /opt/bot-farm
python3 load_keystone_kb.py

# Expected output:
# Bot: Keystone Hardscapes Assistant (keystone-landscaping)
# [1/2] Processing: keystone_company.txt
#       ✓ Created 1 chunks
# [2/2] Processing: keystone_faq.txt
#       ✓ Created 2 chunks
# ✓ Knowledge base loaded successfully!
```

### Running Tests

```bash
# RAG system tests (51 tests)
pytest tests/test_rag.py -v

# RAG query tests
python3 test_keystone_rag.py

# Chat endpoint tests
python3 test_keystone_chat_with_rag.py
```

### Database Queries

```python
# Check knowledge base
from shared.database import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents WHERE bot_id = 1")
        docs = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) FROM document_chunks WHERE bot_id = 1")
        chunks = cur.fetchone()['count']

        print(f"Documents: {docs}, Chunks: {chunks}")
```

---

## Recent Changes (November 2025)

### Completed Work

1. **RAG System Deployment** (Commit: ac5c55e)
   - Implemented Voyage AI embeddings (512D)
   - Created chunking and retrieval system
   - Added vector search with pgvector

2. **Schema Alignment** (Commit: 26aee64)
   - Fixed column names (`chunk_text` vs `content`)
   - Updated embedding dimensions (1024→512)
   - Added bot_id to document_chunks
   - Fixed RealDictCursor access patterns

3. **Integration Verification** (Commit: 3c6b61d)
   - Added `DatabaseConnection` wrapper class
   - Created comprehensive test suite
   - Documented RAG integration
   - Verified end-to-end functionality

### Current Status

✅ **All Systems Operational**
- Knowledge base: 2 documents, 3 chunks loaded
- RAG: Fully integrated, tested, working
- Chat endpoint: Responding with context-aware answers
- Database: Schema aligned, connections stable
- Tests: 51 RAG tests passing

---

## Important Notes

### Bot ID Confusion

**Be careful!** There are TWO bot ID concepts:

1. **Integer ID** (database PK): `id = 1`
   - Used in: `documents.bot_id`, `document_chunks.bot_id`
   - Type: INTEGER

2. **String ID** (API identifier): `bot_id = 'keystone-landscaping'`
   - Used in: `bots.bot_id`, API routes
   - Type: VARCHAR

**Conversion:**
```python
# Get integer ID from string ID
cur.execute("SELECT id FROM bots WHERE bot_id = %s", ('keystone-landscaping',))
bot_id_int = cur.fetchone()['id']  # Returns 1
```

### Database Cursors

**Important:** We use `RealDictCursor`, so `fetchone()` returns a dict, not a tuple:

```python
# ✅ Correct
row = cur.fetchone()
value = row['column_name']

# ❌ Wrong
row = cur.fetchone()
value = row[0]  # KeyError!
```

### RAG Integration Pattern

RAG is integrated at the **application level**, not database level:

1. User query arrives at Flask endpoint
2. App calls `rag_retriever.get_context_for_query()`
3. Context is injected into system prompt
4. Enhanced prompt sent to Claude
5. Response returned to user

**Not** using database triggers or stored procedures.

### Common Issues

**"No relevant chunks found"**
- Check: `SELECT COUNT(*) FROM document_chunks WHERE bot_id = 1`
- Fix: Load KB with `python3 load_keystone_kb.py`
- Or: Lower `SIMILARITY_THRESHOLD` in rag_config.py

**"429 Too Many Requests" (Voyage AI)**
- Cause: API rate limit hit
- Impact: Bot continues without RAG (graceful)
- Fix: Wait a few minutes, implement caching

**"RAG modules not available"**
- Check: `from shared.rag import VoyageClient, RAGRetriever`
- Fix: Verify imports work, check for circular dependencies

---

## Development Workflow

### Making Changes to RAG

1. **Configuration Changes:**
   - Edit: `bots/keystone-landscaping/rag_config.py`
   - Restart bot to apply

2. **Code Changes:**
   - Edit relevant files in `shared/rag/`
   - Test with: `pytest tests/test_rag.py`
   - Restart bot

3. **Knowledge Base Updates:**
   - Add/edit files in `knowledge_base/keystone/`
   - Run: `python3 load_keystone_kb.py`
   - No bot restart needed (data in DB)

### Git Workflow

```bash
# Check status
git status

# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "Description

- Detail 1
- Detail 2

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

### Testing Workflow

```bash
# 1. Unit tests (fast)
pytest tests/test_rag.py -v

# 2. Integration tests (requires bot running)
python3 test_keystone_chat_with_rag.py

# 3. Manual testing
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test query", "session_id": "test"}'
```

---

## Performance Metrics

### RAG Query Performance

- **Query embedding:** 200-400ms (Voyage API call)
- **Vector search:** 50-100ms (PostgreSQL)
- **Total RAG overhead:** 250-500ms
- **Claude API call:** 1-2 seconds (main latency)
- **Total response time:** 1.5-2.5 seconds average

### Costs

**Voyage AI (voyage-3-lite):**
- Pricing: $0.06 per 1M tokens
- Per query: ~100-200 tokens
- **Cost per query:** $0.000006-0.000012
- **Cost per 1000 queries:** ~$0.006-0.012

**Extremely cost-effective!**

---

## Troubleshooting Guide

### Bot Won't Start

**Symptoms:** Import errors, initialization failures

**Check:**
1. Virtual environment activated?
2. Dependencies installed? `pip install -r requirements.txt`
3. `.env` file exists with API keys?
4. Database connection working?

**Fix:**
```bash
# Activate venv
source /opt/bot-farm/venv/bin/activate

# Install deps
pip install -r requirements.txt

# Test imports
python3 -c "from shared.rag import VoyageClient; print('OK')"

# Test database
python3 -c "from shared.database import get_db_connection; \
  with get_db_connection() as conn: print('DB OK')"
```

### RAG Not Retrieving Context

**Symptoms:** "No relevant chunks found" in logs

**Check:**
```python
from shared.database import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Check documents
        cur.execute("SELECT COUNT(*) FROM documents WHERE bot_id = 1")
        print(f"Documents: {cur.fetchone()['count']}")

        # Check chunks
        cur.execute("SELECT COUNT(*) FROM document_chunks WHERE bot_id = 1")
        print(f"Chunks: {cur.fetchone()['count']}")

        # Check embeddings
        cur.execute("""
            SELECT COUNT(*) FROM document_chunks
            WHERE bot_id = 1 AND embedding IS NOT NULL
        """)
        print(f"With embeddings: {cur.fetchone()['count']}")
```

**Fix:**
- If 0 documents: Run `python3 load_keystone_kb.py`
- If documents but no embeddings: Re-run loader
- If all present but no matches: Lower `SIMILARITY_THRESHOLD` to 0.6

### Database Connection Issues

**Symptoms:** Connection errors, authentication failures

**Check:**
1. PostgreSQL running? `sudo systemctl status postgresql`
2. Database exists? `psql -U botfarm -d botfarm -c "\l"`
3. `.pgpass` configured? `cat ~/.pgpass | grep botfarm`
4. Credentials in `.env`?

### API Rate Limits

**Symptoms:** 429 errors from Voyage AI

**Behavior:** Bot continues working without RAG (graceful)

**Fix:**
- Wait a few minutes for rate limit reset
- Implement request caching (future enhancement)
- Monitor usage patterns

---

## Next Steps / Future Work

### Immediate Priorities

1. **Monitor Production Usage**
   - Track RAG hit rates
   - Measure response times
   - Monitor API costs

2. **Expand Knowledge Base**
   - Add technical specifications
   - Include project portfolio
   - Document seasonal services

3. **Optimize Performance**
   - Implement query embedding cache
   - Add connection pooling improvements
   - Consider async RAG calls

### Medium-term Enhancements

1. **Admin Dashboard Integration**
   - RAG statistics display
   - Document upload interface
   - Usage analytics

2. **Smart RAG Triggering**
   - Query classification
   - Only use RAG for relevant queries
   - Skip for greetings/chitchat

3. **Multi-bot Support**
   - Deploy additional bots
   - Shared RAG infrastructure
   - Per-bot knowledge bases

### Long-term Vision

1. **Advanced RAG**
   - Re-ranking with cross-encoder
   - Hybrid search (keyword + vector)
   - Query expansion

2. **FastAPI Migration**
   - Move to async architecture
   - Utilize `my_bot_army/` codebase
   - Improve scalability

3. **Platform Features**
   - Bot marketplace
   - Self-service bot creation
   - White-label deployments

---

## Quick Reference Commands

```bash
# Start Keystone bot
cd /opt/bot-farm/bots/keystone-landscaping && python3 app.py

# Load knowledge base
python3 /opt/bot-farm/load_keystone_kb.py

# Run RAG tests
pytest /opt/bot-farm/tests/test_rag.py -v

# Test chat endpoint
python3 /opt/bot-farm/test_keystone_chat_with_rag.py

# Check DB
psql -U botfarm -d botfarm

# View logs
tail -f /opt/bot-farm/bots/keystone-landscaping/logs/*.log  # if logging configured

# Git status
cd /opt/bot-farm && git status

# Python console (with imports)
cd /opt/bot-farm && python3
>>> from shared.database import get_db_connection
>>> from shared.rag_helpers import rag_query
```

---

## Contact & Resources

- **Repository:** github.com/evgeny-vlasov/my-bot-army
- **Working Directory:** `/opt/bot-farm`
- **Database:** `botfarm` on localhost
- **User:** `chip`

---

## Final Notes for Claude

**When you start a new conversation:**

1. **Read this file first** to get complete context
2. **Check git status** to see what's changed since this was written
3. **Ask the user** what they want to work on
4. **Reference specific files** by path when discussing code
5. **Test changes** before committing
6. **Update documentation** if you make significant changes
7. **Be explicit** about bot ID types (integer vs string)
8. **Remember** RAG is already integrated - don't re-implement it!

**Key principle:** The system works. Understand it before changing it.

---

**Document Version:** 1.0
**Created:** November 19, 2025
**Last Verified:** November 19, 2025
**Status:** ✅ Current and accurate
