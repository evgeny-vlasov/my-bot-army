# My Bot Army

A scalable multi-bot platform for deploying AI assistants powered by Claude. Build, manage, and deploy multiple chatbots with RAG (Retrieval Augmented Generation) capabilities, each with custom knowledge bases and personalities.

## Architecture Overview

This is a modern **FastAPI** application with PostgreSQL + pgvector for semantic search and conversation management.

```
my-bot-army/
├── my_bot_army/                    # Main application package
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── database.py             # SQLAlchemy async setup + pgvector
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic settings
│   │   │   └── exceptions.py       # Error handlers
│   │   ├── models/                 # Pydantic models (request/response)
│   │   │   ├── bot.py
│   │   │   ├── client.py
│   │   │   ├── conversation.py
│   │   │   └── document.py
│   │   ├── schemas/                # SQLAlchemy ORM models (database)
│   │   │   ├── bot.py
│   │   │   ├── client.py
│   │   │   ├── conversation.py
│   │   │   ├── document.py
│   │   │   └── usage.py
│   │   ├── api/v1/                 # API endpoints
│   │   │   ├── clients.py
│   │   │   ├── bots.py
│   │   │   ├── conversations.py    # Main chat endpoint
│   │   │   ├── documents.py        # RAG knowledge base
│   │   │   ├── widget.py           # Embeddable chat UI
│   │   │   └── admin.py
│   │   └── services/               # Business logic
│   │       ├── claude_service.py   # Anthropic API integration
│   │       ├── rag_service.py      # Vector similarity search
│   │       └── embedding_service.py # Text embeddings
│   └── tests/
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── [legacy directories]            # bots/, admin/, shared/ - older code
```

## Tech Stack

- **Framework**: FastAPI 0.104+ (async/await)
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLAlchemy 2.0+ (async)
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **Embeddings**: Claude text embeddings via Anthropic API
- **Vector Search**: pgvector with IVFFlat indexing
- **Validation**: Pydantic 2.5+
- **HTTP Client**: httpx (async)
- **Server**: Uvicorn (ASGI)

## Key Features

### Current Implementation

✅ **Multi-tenant bot platform**
- Clients can have multiple bots
- Each bot has custom system prompt and configuration
- Bot lifecycle management (active/inactive, deployment status)

✅ **Conversation management**
- Full conversation history with messages
- Session tracking with user identifiers
- Token usage and cost tracking

✅ **RAG (Retrieval Augmented Generation)**
- Document ingestion with vector embeddings
- Semantic similarity search using pgvector
- Context injection into Claude prompts
- Configurable similarity thresholds

✅ **RESTful API (v1)**
- Client management
- Bot CRUD operations
- Chat endpoint with streaming support potential
- Document upload and management
- Usage analytics

✅ **Embeddable Widget**
- Simple HTML/JS chat interface
- Served at `/api/v1/widget/chat-widget/{bot_id}`

✅ **Production-ready**
- Async database operations
- Connection pooling
- Health check endpoint
- CORS middleware
- Exception handling
- Background task processing (usage logging)

## Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Anthropic API key

### 1. Install PostgreSQL + pgvector

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE EXTENSION vector;"

# macOS (Homebrew)
brew install postgresql pgvector
```

### 2. Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE my_bot_army;
CREATE USER botfarm WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE my_bot_army TO botfarm;
\c my_bot_army
CREATE EXTENSION vector;
\q
```

### 3. Install Python Dependencies

```bash
# Clone repository
git clone https://github.com/yourusername/my-bot-army.git
cd my-bot-army

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env
```

Set these required variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://botfarm:your_secure_password@localhost/my_bot_army

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Security
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32

# Application
APP_NAME="My Bot Army"
APP_VERSION="1.0.0"
DEBUG=False
LOG_LEVEL=INFO

# Database Pool
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### 5. Run the Application

```bash
# Development mode (auto-reload)
uvicorn my_bot_army.app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn my_bot_army.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Application will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs` (Swagger UI)
- Health: `http://localhost:8000/health`

## API Usage Guide

### Authentication

Currently, the API is open. Add authentication middleware for production.

### Core Endpoints

#### 1. Create a Client

```bash
POST /api/v1/clients/
{
  "name": "Acme Corp",
  "contact_email": "contact@acme.com",
  "subscription_plan": "pro",
  "is_active": true
}
```

#### 2. Create a Bot

```bash
POST /api/v1/bots/
{
  "client_id": 1,
  "name": "Support Bot",
  "description": "Customer support assistant",
  "system_prompt": "You are a helpful customer support agent for Acme Corp...",
  "config": {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1000,
    "temperature": 0.7
  }
}
```

#### 3. Upload Documents (RAG Knowledge Base)

```bash
POST /api/v1/documents/
{
  "bot_id": 1,
  "title": "Product Documentation",
  "content": "Our product features include...",
  "source": "docs.acme.com/products"
}
```

Documents are automatically embedded and indexed for semantic search.

#### 4. Start a Conversation

```bash
POST /api/v1/conversations/
{
  "bot_id": 1,
  "user_identifier": "user_12345",
  "source": "web_widget",
  "metadata": {"ip": "192.168.1.1"}
}

# Response:
{
  "id": 42,
  "bot_id": 1,
  "is_active": true,
  "created_at": "2025-11-09T10:00:00Z"
}
```

#### 5. Chat with Bot

```bash
POST /api/v1/conversations/chat
{
  "conversation_id": 42,
  "message": "What are your product features?"
}

# Response:
{
  "conversation_id": 42,
  "user_message": {
    "id": 101,
    "role": "user",
    "content": "What are your product features?",
    "created_at": "2025-11-09T10:01:00Z"
  },
  "bot_message": {
    "id": 102,
    "role": "assistant",
    "content": "Based on our documentation, our product features include...",
    "tokens_used": 245,
    "created_at": "2025-11-09T10:01:02Z"
  }
}
```

The RAG service automatically:
1. Generates embedding for user message
2. Searches for similar documents using pgvector
3. Injects relevant context into Claude's system prompt
4. Returns response with conversation history

#### 6. Get Conversation History

```bash
GET /api/v1/conversations/42/messages
```

### Widget Endpoint

```bash
GET /api/v1/widget/chat-widget/1
```

Returns a simple HTML chat interface for testing bots.

## Database Schema

### Key Tables

**clients**
- `id`, `name`, `contact_email`, `subscription_plan`, `monthly_budget`, `is_active`

**bots**
- `id`, `client_id`, `name`, `description`, `system_prompt`, `config` (JSONB)
- `is_active`, `deployment_status`, `created_at`, `updated_at`, `deployed_at`

**conversations**
- `id`, `bot_id`, `user_identifier`, `source`, `metadata` (JSONB)
- `is_active`, `started_at`, `ended_at`, `updated_at`

**messages**
- `id`, `conversation_id`, `role` (user/assistant/system)
- `content`, `tokens_used`, `created_at`

**documents** (RAG)
- `id`, `bot_id`, `title`, `content`, `source`
- `embedding` (vector(1024)) - pgvector column
- `created_at`, `updated_at`

**usage**
- `id`, `client_id`, `bot_id`, `conversation_id`
- `event_type`, `tokens_used`, `cost`, `timestamp`

### Vector Search

Documents use pgvector with IVFFlat indexing for fast similarity search:

```sql
CREATE INDEX documents_embedding_idx
ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## How RAG Works

1. **Document Ingestion** (`/api/v1/documents/`)
   - Upload text documents for a bot
   - System generates embeddings via Anthropic API
   - Stored in PostgreSQL with vector column

2. **Query Processing** (automatic in `/conversations/chat`)
   - User sends message
   - System generates query embedding
   - pgvector performs cosine similarity search
   - Retrieves top 3 most relevant documents

3. **Context Injection**
   - Relevant documents appended to system prompt
   - Sent to Claude API with conversation history
   - Claude responds with context-aware answer

4. **Response**
   - Bot response saved to database
   - Usage metrics logged for billing

## Development Guide for AI Assistants

### Code Navigation

**Entry Point**: `my_bot_army/app/main.py:27-31`
- FastAPI app initialization
- CORS middleware
- API router registration at `/api/v1`

**Database Setup**: `my_bot_army/app/database.py:7-13,52-63`
- Async SQLAlchemy engine
- Connection pooling
- Auto-creates tables on startup
- Enables pgvector extension

**Chat Logic**: `my_bot_army/app/api/v1/conversations.py:166-253`
- Main `/conversations/chat` endpoint
- Handles conversation state
- Calls RAG service
- Logs usage in background

**RAG Implementation**: `my_bot_army/app/services/rag_service.py:11-102`
- `search_similar_documents()` - vector similarity search
- `get_context_for_query()` - retrieves and formats context

**Claude Integration**: `my_bot_army/app/services/claude_service.py:14-84`
- API wrapper for Anthropic Claude
- Handles conversation history
- Injects RAG context into system prompt

### Common Tasks

**Add new API endpoint**:
1. Create route in `my_bot_army/app/api/v1/{module}.py`
2. Register router in `my_bot_army/app/api/__init__.py`

**Add new database model**:
1. Create SQLAlchemy model in `my_bot_army/app/schemas/{name}.py`
2. Create Pydantic model in `my_bot_army/app/models/{name}.py`
3. Import in `my_bot_army/app/database.py:54` for auto-creation

**Modify RAG behavior**:
- Similarity threshold: `my_bot_army/app/services/rag_service.py:88`
- Number of results: `my_bot_army/app/services/rag_service.py:91`
- Context formatting: `my_bot_army/app/services/rag_service.py:98-102`

**Change Claude model**:
- Default model: `my_bot_army/app/services/claude_service.py:54`
- Per-bot config: Set in bot's `config` JSONB field

### Testing

```bash
# Run tests (when available)
pytest

# Test API with curl
curl http://localhost:8000/health

# Interactive API docs
open http://localhost:8000/docs
```

## Production Deployment

### Using systemd

Create `/etc/systemd/system/my-bot-army.service`:

```ini
[Unit]
Description=My Bot Army API
After=network.target postgresql.service

[Service]
Type=notify
User=botfarm
WorkingDirectory=/opt/my-bot-army
Environment="PATH=/opt/my-bot-army/venv/bin"
ExecStart=/opt/my-bot-army/venv/bin/uvicorn my_bot_army.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable my-bot-army
sudo systemctl start my-bot-army
sudo systemctl status my-bot-army

# View logs
sudo journalctl -u my-bot-army -f
```

### Using Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY my_bot_army/ my_bot_army/
COPY .env .env

CMD ["uvicorn", "my_bot_army.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name api.mybotarmy.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Considerations

⚠️ **Before Production**:

1. **Add authentication**
   - Implement JWT or API key middleware
   - See FastAPI security docs

2. **Rate limiting**
   - Use slowapi or similar
   - Prevent abuse

3. **CORS configuration**
   - Update `allow_origins` in `main.py:34-36`
   - Don't use `["*"]` in production

4. **Environment variables**
   - Never commit `.env`
   - Use secrets manager in production

5. **Database security**
   - Strong password
   - Firewall rules
   - SSL connections

6. **Input validation**
   - Already using Pydantic
   - Add custom validators for content

## Monitoring & Analytics

### Built-in Metrics

- **Usage tracking**: All API calls logged to `usage` table
- **Token consumption**: Tracked per message
- **Cost estimation**: Calculated in `conversations.py:301-303`
- **Conversation analytics**: Duration, message count, user patterns

### Health Endpoint

```bash
GET /health

{
  "status": "healthy",
  "database": "connected",
  "pgvector": "0.5.0"
}
```

## Legacy Code

The `bots/`, `admin/`, and `shared/` directories contain older Flask-based implementations. The current production system uses the FastAPI application in `my_bot_army/`. The legacy code may be useful for reference but is not actively maintained.

## Troubleshooting

**Database connection errors**:
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check connection string in `.env`
- Ensure pgvector extension is installed

**Import errors**:
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

**API errors**:
- Check logs: `journalctl -u my-bot-army -f`
- Verify API key is set
- Test health endpoint first

**Vector search not working**:
- Ensure pgvector extension is enabled
- Check documents have embeddings
- Verify index exists

## Contributing

This is a personal project, but suggestions and feedback are welcome via issues.

## License

MIT License - See LICENSE file for details.

## Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **pgvector**: https://github.com/pgvector/pgvector
- **Anthropic API**: https://docs.anthropic.com/
- **Claude Code**: https://docs.claude.com/en/docs/claude-code

---

**Built with Claude Code** | **Powered by Claude Sonnet 4.5**
