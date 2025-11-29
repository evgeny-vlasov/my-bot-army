# My Bot Army - Technical Architecture

**Version:** 2.0.0 (Flask)
**Last Updated:** November 29, 2025
**Status:** Production Ready
**Active Bots:** Keystone Hardscapes (port 5001), Psyling Therapist (port 5002)

This document provides detailed technical information about the My Bot Army Flask-based architecture.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Flask Application Architecture](#flask-application-architecture)
5. [Database Architecture](#database-architecture)
6. [RAG System Architecture](#rag-system-architecture)
7. [API Endpoints](#api-endpoints)
8. [Integration Points](#integration-points)
9. [Deployment Architecture](#deployment-architecture)
10. [Performance & Scalability](#performance--scalability)

---

## Architecture Overview

### System Design Principles

**Simplicity First:**
- Synchronous Python (no async/await complexity)
- Standard Flask patterns and conventions
- Clear separation of concerns
- Easy to understand and maintain

**Multi-Tenant by Design:**
- One database, multiple bots
- Per-bot configuration and prompts
- Isolated knowledge bases
- Shared infrastructure

**Production Ready:**
- Error handling and graceful degradation
- Usage tracking and cost monitoring
- Structured logging
- Health checks

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Clients                         │
│              (Web Browsers, Mobile Apps)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Reverse Proxy (Nginx)                      │
│               SSL Termination, Load Balancing               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Gunicorn WSGI Server                        │
│              (Multi-worker Process Model)                   │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker 4 │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application                         │
│                 (bots/keystone-landscaping/app.py)          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Request Processing                      │  │
│  │  1. Parse & validate request                        │  │
│  │  2. RAG context retrieval (if needed)               │  │
│  │  3. Call Claude API                                 │  │
│  │  4. Log conversation & usage                        │  │
│  │  5. Return response                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routes     │  │  Services    │  │   Config     │     │
│  │ /api/chat    │  │ RAG Service  │  │  Prompts     │     │
│  │ /health      │  │ Claude API   │  │  Settings    │     │
│  │ /widget.js   │  │ Database     │  └──────────────┘     │
│  └──────────────┘  └──────────────┘                        │
└────────┬──────────────────┬──────────────────┬─────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL     │  │ Anthropic    │  │  Voyage AI   │
│  + pgvector     │  │  Claude API  │  │  Embeddings  │
│                 │  │              │  │              │
│ • Conversations │  │ Sonnet 4.5   │  │ voyage-3-lite│
│ • Messages      │  │              │  │              │
│ • Documents     │  │ $3/1M in     │  │ $0.06/1M tok │
│ • Embeddings    │  │ $15/1M out   │  │              │
│ • Usage tracking│  │              │  │              │
└─────────────────┘  └──────────────┘  └──────────────┘
```

---

## Technology Stack

### Production Stack (Current)

#### Web Framework
- **Flask 3.0.0** - Synchronous web framework
  - Route handlers: `@app.route()` decorators
  - Request handling: `request.get_json()`
  - Response: `jsonify()` helper
  - Error handling: `@app.errorhandler()` decorators
  - CORS: `flask-cors` extension

#### Server
- **Development:** Flask built-in server (`app.run()`)
- **Production:** Gunicorn 21.2.0 (WSGI server)
  - Multi-worker process model
  - Worker count: typically 2 × CPU cores
  - Timeout: 120s (for long Claude API calls)

#### Database
- **PostgreSQL 15+** - Primary database
  - Extension: **pgvector** - Vector similarity search
  - Driver: **psycopg2-binary** - Synchronous Python adapter
  - Connection: Direct psycopg2.connect() (no ORM for simple queries)
  - Cursor: RealDictCursor (returns dict, not tuple)

#### AI Services
- **Claude (Anthropic):**
  - Model: claude-sonnet-4-20250514
  - Library: `anthropic` official Python SDK
  - API: Synchronous (blocking HTTP requests)

- **Voyage AI:**
  - Model: voyage-3-lite (512 dimensions)
  - Library: Custom wrapper (`shared/rag/voyage_client.py`)
  - API: RESTful, synchronous requests

#### HTTP Client
- **requests 2.31.0** - Synchronous HTTP library
  - Used for Voyage AI API calls
  - Simple, battle-tested, widely known

#### Runtime
- **Python 3.11+** - Latest stable Python
- **Virtual Environment** - Isolated dependencies
- **Environment Variables** - `.env` file with `python-dotenv`

### Legacy Stack (Reference Only)

Located in `my_bot_army/app/` directory, **not used in production**:

- **FastAPI 0.104.1** - Modern async web framework
- **Uvicorn** - ASGI server for FastAPI
- **AsyncPG** - Async PostgreSQL driver
- **httpx** - Async HTTP client
- **Pydantic** - Data validation models

**Note:** These dependencies remain in `requirements.txt` for reference but are not used by the production Flask system.

---

## Project Structure

### Directory Layout

```
my-bot-army/
│
├── bots/                                # Flask bot instances (PRODUCTION)
│   ├── keystone-landscaping/            # Keystone bot (port 5001, bot_id=1)
│   │   ├── app.py                       # Main Flask app ⭐
│   │   ├── config.py                    # Bot configuration
│   │   ├── prompts.py                   # System prompts
│   │   ├── rag_config.py                # RAG settings (threshold: 0.7)
│   │   └── knowledge_base/              # Source documents
│   └── therapist/                       # Therapist bot (port 5002, bot_id=2)
│       ├── app.py                       # Main Flask app ⭐
│       ├── config.py                    # Bot configuration
│       ├── prompts.py                   # System prompts
│       ├── rag_config.py                # RAG settings (threshold: 0.3)
│       └── knowledge_base/              # Source documents
│
├── shared/                              # Shared modules
│   ├── __init__.py
│   ├── claude_client.py                 # Claude API wrapper ⭐
│   ├── database.py                      # Database functions ⭐
│   ├── rag.py                          # RAG OOP implementation
│   ├── rag_helpers.py                   # RAG helper functions
│   ├── rag/                             # RAG components
│   │   ├── __init__.py
│   │   ├── voyage_client.py             # Voyage AI API
│   │   ├── retriever.py                 # Vector search
│   │   ├── chunker.py                   # Text chunking
│   │   └── embedder.py                  # Document processing
│   └── widget/
│       └── bot-widget.js                # Chat widget (JavaScript)
│
├── my_bot_army/                         # FastAPI system (LEGACY)
│   └── app/
│       ├── main.py                      # FastAPI app (not used)
│       ├── core/
│       ├── services/
│       └── schemas/
│
├── migrations/                          # SQL migrations
│   ├── 001_initial_schema.sql
│   ├── 002_add_rag_tables.sql
│   └── ...
│
├── scripts/                             # Utility scripts
│   ├── add_document.py
│   ├── reindex_bot.py
│   └── test_rag.py
│
├── tests/                               # Test suites
│   └── test_rag.py                      # RAG tests (51 tests)
│
├── knowledge_base/                      # Source KB files
│   └── keystone/
│       ├── keystone_company.txt
│       └── keystone_faq.txt
│
├── docs/                                # Documentation
│   └── sprints/                         # Sprint reports
│
├── .env                                 # Environment variables (gitignored)
├── .env.example                         # Template for .env
├── requirements.txt                     # Python dependencies ⭐
│
├── README.md                            # Main documentation
├── LLM-README.md                        # Context for LLMs
├── ARCHITECTURE.md                      # This file ⭐
├── MIGRATION_NOTES.md                   # FastAPI → Flask guide
├── FLASK_NOTES.md                       # Flask implementation notes
└── ...
```

### File Responsibilities

| File | Responsibility | Used By |
|------|---------------|---------|
| `bots/keystone-landscaping/app.py` | Flask routes, request handling, RAG integration | Production ✅ |
| `bots/keystone-landscaping/config.py` | Bot ID, name, port, CORS origins | Flask app |
| `bots/keystone-landscaping/prompts.py` | System prompts for Claude | Flask app |
| `bots/keystone-landscaping/rag_config.py` | RAG parameters (top_k, threshold, etc.) | Flask app |
| `shared/claude_client.py` | Claude API calls, usage tracking | All bots |
| `shared/database.py` | Database connections, queries, helpers | All bots |
| `shared/rag/voyage_client.py` | Voyage AI embedding generation | RAG system |
| `shared/rag/retriever.py` | Vector similarity search | RAG system |
| `shared/rag/chunker.py` | Text chunking logic | Document processing |
| `shared/rag/embedder.py` | End-to-end document processing | Knowledge base loading |

---

## Flask Application Architecture

### Application Structure (app.py)

The main Flask application follows this structure:

```python
# 1. Imports
from flask import Flask, request, jsonify
from flask_cors import CORS
from shared.claude_client import ClaudeClient
from shared.rag import VoyageClient, RAGRetriever
from shared.database import DatabaseConnection, get_bot_by_id
from config import Config
from prompts import SYSTEM_PROMPT
import rag_config

# 2. Initialize Flask app
app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

# 3. Initialize services
claude_client = ClaudeClient(bot_id=Config.BOT_ID)
voyage_client = VoyageClient(model=rag_config.VOYAGE_MODEL)
db_connection = DatabaseConnection()
rag_retriever = RAGRetriever(voyage_client, db_connection)

# 4. Define routes
@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Bot is running'})

@app.route('/api/chat', methods=['POST'])
def chat():
    # Main chat endpoint with RAG integration
    pass

@app.route('/widget.js', methods=['GET'])
def serve_widget():
    # Serve JavaScript chat widget
    pass

# 5. Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

# 6. Run application
if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
```

### Request Flow (Chat Endpoint)

When a user sends a message to `/api/chat`:

```
1. Request Reception
   ├─ Parse JSON body
   ├─ Validate required fields (message)
   └─ Extract optional fields (conversation_history, session_id)

2. Conversation Management
   ├─ Get or create conversation (if session_id provided)
   ├─ Save user message to database
   └─ Retrieve conversation history

3. RAG Context Retrieval (if enabled)
   ├─ Generate embedding for user query (Voyage AI)
   ├─ Search document_chunks table (pgvector)
   ├─ Retrieve top K most similar chunks
   └─ Format context for system prompt

4. Claude API Call
   ├─ Build enhanced system prompt (original + RAG context)
   ├─ Prepare messages array (history + current message)
   ├─ Call Claude API (Anthropic SDK)
   └─ Receive response

5. Response Handling
   ├─ Save assistant message to database
   ├─ Log API usage (tokens, cost)
   └─ Return JSON response to client

6. Error Handling (if any step fails)
   ├─ Log error details
   ├─ Graceful degradation (e.g., continue without RAG)
   └─ Return appropriate error response
```

### Configuration Management

#### config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Identity
    BOT_ID = os.getenv('BOT_ID', 'keystone-landscaping')
    BOT_NAME = os.getenv('BOT_NAME', 'Keystone Hardscapes Assistant')

    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # CORS
    CORS_ORIGINS = ['*']  # Configure for production

    # Limits
    MAX_MESSAGE_LENGTH = 5000
    MAX_CONVERSATION_HISTORY = 20
```

#### rag_config.py
```python
import os

# RAG Master Switch
RAG_ENABLED = os.getenv('RAG_ENABLED', 'true').lower() == 'true'

# Voyage AI Settings
VOYAGE_MODEL = "voyage-3-lite"  # 512D embeddings (both bots)
VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')

# Retrieval Parameters
TOP_K_CHUNKS = int(os.getenv('RAG_TOP_K', 5))
# Note: Keystone uses 0.7, Therapist uses 0.3 for broader retrieval
SIMILARITY_THRESHOLD = float(os.getenv('RAG_SIMILARITY_THRESHOLD', 0.7))
MAX_CONTEXT_TOKENS = 2000

# System Instruction
RAG_SYSTEM_INSTRUCTION = """
Use the following information from our knowledge base to help answer the user's question.
If the information doesn't relate to the question, you can ignore it.
"""

# Logging
LOG_CONTEXT_CHUNKS = True  # Log which chunks were used

def get_rag_enabled():
    return RAG_ENABLED and VOYAGE_API_KEY is not None
```

---

## Database Architecture

### Schema Overview

The database uses PostgreSQL 15+ with the `pgvector` extension for vector similarity search.

#### Core Tables

**clients** - Business clients who own bots
```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**bots** - Bot configurations
```sql
CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    bot_id VARCHAR(255) UNIQUE NOT NULL,  -- e.g. 'keystone-landscaping'
    bot_name VARCHAR(255) NOT NULL,
    system_prompt TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**conversations** - Chat sessions
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES bots(id),
    session_id VARCHAR(255),
    user_ip VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**messages** - Individual messages
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    tokens INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### RAG Tables

**documents** - Knowledge base documents
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES bots(id),
    title VARCHAR(500) NOT NULL,
    source VARCHAR(500),  -- File path or URL
    content TEXT NOT NULL,
    content_hash VARCHAR(64),  -- SHA256 for deduplication
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**document_chunks** - Chunked documents with embeddings
```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    bot_id INTEGER REFERENCES bots(id),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(512),  -- Voyage-3-lite: 512 dimensions
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for performance
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX idx_chunks_bot_id ON document_chunks(bot_id);
```

**api_usage** - API usage tracking
```sql
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES bots(id),
    date DATE NOT NULL,
    requests INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0,

    UNIQUE(bot_id, date)
);
```

### Database Access Patterns

#### Connection Management

```python
# shared/database.py

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DB_CONFIG = {
    'host': 'localhost',
    'database': 'botfarm',
    'user': 'botfarm',
    'password': os.getenv('DB_PASSWORD')
}

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
```

#### Common Queries

**Get bot by string ID:**
```python
def get_bot_by_id(bot_id_str: str) -> dict:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, bot_id, bot_name, system_prompt, status
                FROM bots
                WHERE bot_id = %s
            """, (bot_id_str,))
            return cur.fetchone()
```

**Save message:**
```python
def save_message(conversation_id: int, role: str, content: str) -> int:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO messages (conversation_id, role, content)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (conversation_id, role, content))
            return cur.fetchone()['id']
```

**Vector similarity search:**
```python
def search_similar_chunks(bot_id: int, query_embedding: list, top_k: int = 5):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # IMPORTANT: Filter on dc.bot_id, not d.bot_id
            # Filtering on d.bot_id causes PostgreSQL query planner issues
            # See bugfix documentation for details
            cur.execute("""
                SELECT
                    dc.id as chunk_id,
                    dc.chunk_text,
                    dc.document_id,
                    d.title as document_title,
                    1 - (dc.embedding <=> %s::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.bot_id = %s
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, bot_id, query_embedding, top_k))
            return cur.fetchall()
```

---

## RAG System Architecture

### Overview

The Retrieval-Augmented Generation (RAG) system enhances Claude's responses with relevant information from the bot's knowledge base.

### Components

#### 1. VoyageClient (`shared/rag/voyage_client.py`)

Handles communication with Voyage AI's embedding API.

```python
class VoyageClient:
    def __init__(self, model: str = "voyage-3-lite"):
        self.model = model
        self.api_key = os.getenv('VOYAGE_API_KEY')
        self.url = "https://api.voyageai.com/v1/embeddings"

    def get_embedding(self, text: str) -> list:
        """Generate embedding for text."""
        response = requests.post(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"input": text, "model": self.model}
        )
        return response.json()['data'][0]['embedding']

    def get_embeddings_batch(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        # Batch API call for efficiency
        pass
```

#### 2. TextChunker (`shared/rag/chunker.py`)

Splits documents into smaller, semantically meaningful chunks.

```python
class TextChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> list:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += (self.chunk_size - self.overlap)
        return chunks
```

#### 3. RAGRetriever (`shared/rag/retriever.py`)

Performs vector similarity search to find relevant chunks.

```python
class RAGRetriever:
    def __init__(self, voyage_client: VoyageClient, db_connection: DatabaseConnection):
        self.voyage_client = voyage_client
        self.db = db_connection

    def get_context_for_query(
        self,
        bot_id: int,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        max_tokens: int = 2000
    ) -> tuple:
        """
        Retrieve relevant context for a query.

        Returns:
            (context_str, chunks_list) - Formatted context and chunk details
        """
        # 1. Generate query embedding
        query_embedding = self.voyage_client.get_embedding(query)

        # 2. Search database
        chunks = self.db.search_similar_chunks(bot_id, query_embedding, top_k)

        # 3. Filter by similarity threshold
        relevant_chunks = [c for c in chunks if c['similarity'] >= similarity_threshold]

        # 4. Format context
        if not relevant_chunks:
            return None, []

        context = self._format_context(relevant_chunks, max_tokens)
        return context, relevant_chunks
```

#### 4. DocumentEmbedder (`shared/rag/embedder.py`)

End-to-end document processing: chunk → embed → store.

```python
class DocumentEmbedder:
    def __init__(self, voyage_client, db_connection, chunker):
        self.voyage = voyage_client
        self.db = db_connection
        self.chunker = chunker

    def process_document(self, bot_id: int, title: str, content: str, source: str):
        """Process a document: chunk, embed, and store."""
        # 1. Create document record
        doc_id = self.db.create_document(bot_id, title, content, source)

        # 2. Chunk the text
        chunks = self.chunker.chunk_text(content)

        # 3. Generate embeddings (batch for efficiency)
        embeddings = self.voyage.get_embeddings_batch(chunks)

        # 4. Store chunks with embeddings
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            self.db.create_chunk(doc_id, bot_id, idx, chunk, embedding)

        return doc_id, len(chunks)
```

### RAG Integration in Flask App

```python
# In app.py

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data['message']

    # RAG: Retrieve context
    context_chunks = []
    enhanced_system_prompt = SYSTEM_PROMPT

    if rag_retriever:
        try:
            context, chunks = rag_retriever.get_context_for_query(
                bot_id=Config.BOT_ID,
                query=message,
                top_k=rag_config.TOP_K_CHUNKS,
                similarity_threshold=rag_config.SIMILARITY_THRESHOLD,
                max_tokens=rag_config.MAX_CONTEXT_TOKENS
            )

            if context and chunks:
                enhanced_system_prompt = (
                    f"{SYSTEM_PROMPT}\n\n"
                    f"{rag_config.RAG_SYSTEM_INSTRUCTION}\n\n"
                    f"{context}"
                )
                context_chunks = chunks
                print(f"RAG: Found {len(chunks)} relevant chunks")
        except Exception as e:
            print(f"Warning: RAG search failed: {e}")
            # Continue without RAG if it fails

    # Call Claude with enhanced prompt
    response = claude_client.chat(
        message=message,
        system_prompt=enhanced_system_prompt,
        conversation_history=data.get('conversation_history', [])
    )

    return jsonify({'response': response, 'status': 'success'})
```

### RAG Performance

**Latency Breakdown:**
- Query embedding: 200-400ms (Voyage API network call)
- Vector search: 50-100ms (PostgreSQL with pgvector)
- Total RAG overhead: 250-500ms

**Cost (per query):**
- Voyage AI voyage-3-lite: ~$0.000006-0.000012
- Claude API: ~$0.01-0.05 (varies by conversation length)
- Total: Dominated by Claude costs

**Accuracy:**
- Similarity threshold 0.7 provides good precision
- Top-5 chunks typically cover the topic comprehensively
- False negatives rare with well-chunked documents

---

## API Endpoints

### Public Endpoints

#### GET `/`
**Welcome / Status Check**

Response:
```json
{
  "message": "Keystone Hardscapes Bot API",
  "status": "running",
  "bot_id": "keystone-landscaping",
  "bot_name": "Keystone Hardscapes Assistant"
}
```

#### GET `/health`
**Health Check**

Response:
```json
{
  "status": "healthy",
  "bot": "keystone-landscaping"
}
```

#### POST `/api/chat`
**Main Chat Endpoint**

Request:
```json
{
  "message": "What services do you offer?",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ],
  "session_id": "abc123"
}
```

Response (Success):
```json
{
  "response": "We offer hardscaping services including...",
  "status": "success"
}
```

Response (Error):
```json
{
  "error": "Message field is required",
  "status": "error"
}
```

**Validation Rules:**
- `message` (required): string, max 5000 chars
- `conversation_history` (optional): array of message objects
- `session_id` (optional): string for conversation tracking

#### GET `/widget.js`
**Serve Chat Widget**

Returns JavaScript file for embeddable chat widget.

Headers:
```
Content-Type: application/javascript
Cache-Control: no-cache, no-store, must-revalidate
```

#### GET `/test`
**Widget Test Page**

Returns HTML page for testing the chat widget.

### Admin Endpoints

#### GET `/admin/stats`
**Bot Statistics**

Response:
```json
{
  "bot_id": "keystone-landscaping",
  "today_usage": {
    "requests": 42,
    "input_tokens": 15000,
    "output_tokens": 8000,
    "cost": 0.165
  },
  "total_conversations": 120,
  "total_messages": 480,
  "status": "success"
}
```

**Note:** Should be protected with authentication in production.

---

## Integration Points

### WebGarden Integration

My Bot Army is designed to integrate with the WebGarden Flask infrastructure.

**Shared Patterns:**
- Flask framework
- Synchronous SQLAlchemy
- PostgreSQL database
- Gunicorn deployment
- Environment variable configuration

**Integration Options:**

1. **Standalone Service** (Current)
   - Bot runs on separate port (5001)
   - WebGarden can embed chat widget
   - Independent deployment and scaling

2. **Embedded Blueprint** (Future)
   - Bot registered as Flask blueprint in WebGarden
   - Shared database connection pool
   - Unified authentication and session management

3. **Reverse Proxy** (Production)
   - Nginx routes `/bot/*` to bot service
   - SSL termination at proxy level
   - Load balancing across bot workers

### External API Integration

**Anthropic Claude:**
- Library: Official `anthropic` Python SDK
- Authentication: API key in environment variable
- Rate limits: Handle 429 errors gracefully
- Timeout: 30 seconds default

**Voyage AI:**
- Custom HTTP client (requests library)
- Authentication: Bearer token
- Rate limits: Graceful degradation (continue without RAG)
- Batch operations: Multiple embeddings per request

### Database Integration

**Connection Pattern:**
```python
# Each worker has its own connection pool
# Connections opened/closed per request (context manager)
# No persistent connections (simple, reliable)

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ...")
        results = cur.fetchall()
# Connection automatically committed and closed
```

**Migration Strategy:**
- SQL migrations in `migrations/` directory
- Manual execution: `psql -U botfarm -d botfarm -f migration.sql`
- No ORM auto-migration (explicit control)

---

## Deployment Architecture

### Development Deployment

```bash
# Single-worker Flask development server
cd /opt/bot-farm/bots/keystone-landscaping
python3 app.py

# Runs on http://localhost:5001
# Auto-reload on code changes (if DEBUG=True)
# Single-threaded, not for production
```

### Production Deployment

```bash
# Multi-worker Gunicorn WSGI server
cd /opt/bot-farm/bots/keystone-landscaping
gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 120 app:app

# Workers: 2-4 per CPU core
# Timeout: 120s (Claude can be slow)
# Graceful worker restarts
# Process supervision via systemd
```

### systemd Service

```ini
[Unit]
Description=Keystone Hardscapes Bot (Flask + Gunicorn)
After=network.target postgresql.service

[Service]
Type=notify
User=chip
Group=www-data
WorkingDirectory=/opt/bot-farm/bots/keystone-landscaping
Environment="PATH=/opt/bot-farm/venv/bin"
ExecStart=/opt/bot-farm/venv/bin/gunicorn \
    --bind 0.0.0.0:5001 \
    --workers 4 \
    --timeout 120 \
    --access-logfile /var/log/keystone-bot/access.log \
    --error-logfile /var/log/keystone-bot/error.log \
    app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name bot.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bot.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/bot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.example.com/privkey.pem;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts (Claude can be slow)
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Widget with caching
    location /widget.js {
        proxy_pass http://127.0.0.1:5001;
        # Cache for 1 hour
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Performance & Scalability

### Performance Characteristics

**Request Latency:**
- RAG embedding: 200-400ms (Voyage API)
- Vector search: 50-100ms (PostgreSQL)
- Claude API: 1000-2000ms (largest component)
- Database ops: 10-50ms
- **Total: 1.5-2.5 seconds average**

**Throughput:**
- 4 Gunicorn workers = 4 concurrent requests
- Each request blocks for ~2 seconds
- Theoretical max: ~120 requests/minute
- Practical sustained: ~60-80 requests/minute

### Scalability Strategies

**Vertical Scaling:**
- Add more Gunicorn workers
- 2× CPU cores is typical
- Diminishing returns beyond 8-12 workers
- Limited by database connection pool

**Horizontal Scaling:**
- Run multiple bot instances
- Load balance with Nginx
- Shared PostgreSQL database
- No session affinity required

**Database Optimization:**
- Connection pooling (pgbouncer)
- Read replicas for analytics
- Partition large tables (messages, api_usage)
- Index optimization for common queries

**Caching:**
- Cache embeddings for common queries
- Redis for session data
- CDN for widget.js
- Database query result caching

### Bottlenecks & Mitigation

**Claude API Latency:**
- Bottleneck: 1-2 second response time
- Mitigation: Streaming responses (future), asynchronous processing

**Voyage AI Rate Limits:**
- Bottleneck: 429 errors under heavy load
- Mitigation: Request queuing, embedding cache, graceful degradation

**Database Connections:**
- Bottleneck: Connection pool exhaustion
- Mitigation: Connection pooler (pgbouncer), optimize query efficiency

**Memory Usage:**
- Bottleneck: Multiple Gunicorn workers
- Mitigation: Tune worker count, use worker_class=gthread for I/O-bound loads

### Monitoring & Observability

**Key Metrics:**
- Request rate (requests/minute)
- Response latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Claude API usage (tokens, cost)
- RAG hit rate (queries with context vs without)
- Database query time
- Worker CPU and memory usage

**Logging:**
- Application logs: stdout/stderr
- Access logs: Gunicorn or Nginx
- Error logs: Application + Gunicorn
- Structured logging: JSON format recommended

**Alerting:**
- High error rate (>5%)
- High latency (>5 seconds p95)
- Service down
- Database connection failures
- API rate limit errors

---

## Security Considerations

**API Keys:**
- Store in environment variables, never commit
- Use separate keys for dev/staging/production
- Rotate keys periodically

**Database:**
- Dedicated user with limited privileges
- No direct internet access
- Regular backups
- Encrypted connections (SSL)

**CORS:**
- Configure allowed origins in production
- Don't use `*` for production

**Input Validation:**
- Sanitize user input
- Limit message length
- Validate JSON structure
- Rate limiting (future)

**Authentication:**
- Admin endpoints should require auth
- API key or JWT for widget initialization
- IP whitelisting for admin access

---

## Future Enhancements

**Short Term:**
- Admin dashboard integration
- Usage analytics and reporting
- Conversation export functionality
- Multi-bot deployment automation

**Medium Term:**
- Async Flask migration (if needed for scale)
- Caching layer (Redis)
- Streaming responses
- Advanced RAG (re-ranking, hybrid search)

**Long Term:**
- Multi-model support (Claude, GPT, etc.)
- Fine-tuning integration
- A/B testing framework
- White-label deployments

---

**Document Version:** 1.0
**Created:** November 25, 2025
**Status:** ✅ Current and Accurate
