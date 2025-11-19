# My Bot Army

> **🤖 For LLMs/Claude:** Start by reading [LLM-README.md](./LLM-README.md) for complete project context

A scalable multi-tenant platform for deploying AI chatbots powered by Claude, with RAG (Retrieval-Augmented Generation) capabilities for knowledge-base enhanced responses.

**Current Status:** ✅ Production-Ready
**Active System:** Flask-based Keystone Hardscapes Bot with full RAG integration
**Last Updated:** November 19, 2025

---

## 🚀 Quick Start

### For Developers

```bash
# 1. Clone and enter directory
git clone https://github.com/evgeny-vlasov/my-bot-army.git
cd my-bot-army

# 2. Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure .env file
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY and VOYAGE_API_KEY

# 4. Start the Keystone bot
cd bots/keystone-landscaping
python3 app.py

# Bot runs on http://localhost:5001
```

### For LLMs Working on This Project

**📖 Read [LLM-README.md](./LLM-README.md) first!**

That document contains:
- Complete project architecture
- Current system status
- Development workflows
- Common tasks
- Troubleshooting guide
- Everything you need to understand the codebase

---

## 📊 Project Overview

### Two Systems

This repository contains two bot systems:

#### 1. **Active: Flask-Based Bots** (`bots/` directory) ⭐

**Status:** Production, actively used
**Current Bot:** Keystone Hardscapes landscaping assistant
**Framework:** Flask + Claude Sonnet 4.5
**RAG:** Fully integrated with Voyage AI embeddings + pgvector

**Location:** `/opt/bot-farm/bots/keystone-landscaping/`

**Features:**
- ✅ RAG-enhanced responses from knowledge base
- ✅ Real-time chat with Claude Sonnet 4.5
- ✅ Conversation history and logging
- ✅ Embeddable JavaScript widget
- ✅ Usage tracking and cost monitoring
- ✅ Production-ready error handling

#### 2. **Legacy: FastAPI System** (`my_bot_army/` directory)

**Status:** Prototype/reference implementation
**Framework:** FastAPI (async)
**Note:** Not currently deployed, may be used for future scaling

---

## 🏗️ Architecture

### Technology Stack

**Production (Keystone Bot):**
- **Framework:** Flask 3.x
- **LLM:** Claude Sonnet 4.5 (Anthropic API)
- **Embeddings:** Voyage AI voyage-3-lite (512D, $0.06/1M tokens)
- **Database:** PostgreSQL 15+ with pgvector extension
- **Vector Search:** pgvector (cosine similarity)
- **Runtime:** Python 3.11

**Key Components:**
```
┌─────────────────────────────────────────────────┐
│  User → Chat Widget → Flask App                 │
│           ↓                                      │
│      RAG Retriever                               │
│           ↓                                      │
│   Vector Search (pgvector)                      │
│           ↓                                      │
│   Enhanced Prompt → Claude API → Response       │
└─────────────────────────────────────────────────┘
```

### Database Schema

**Core Tables:**
- `clients` - Business clients
- `bots` - Bot configurations and prompts
- `conversations` - Chat sessions
- `messages` - Individual messages
- `documents` - Knowledge base documents
- `document_chunks` - Chunked docs with vector embeddings
- `api_usage` - Usage tracking

**See:** [Database schema documentation](./docs/database_schema.md) (if exists)

---

## 📂 Repository Structure

```
/opt/bot-farm/
├── bots/                              # Flask-based bots ⭐ ACTIVE
│   └── keystone-landscaping/          # Production Keystone bot
│       ├── app.py                     # Main Flask application
│       ├── config.py                  # Configuration
│       ├── prompts.py                 # System prompts
│       ├── rag_config.py              # RAG settings
│       └── knowledge_base/            # KB source files
│
├── shared/                            # Shared modules
│   ├── database.py                    # DB functions
│   ├── claude_client.py               # Claude API wrapper
│   ├── rag_helpers.py                 # RAG helper functions
│   ├── rag/                           # RAG OOP components
│   │   ├── voyage_client.py           # Voyage AI integration
│   │   ├── retriever.py               # Vector search
│   │   ├── chunker.py                 # Text chunking
│   │   └── embedder.py                # Document processing
│   └── widget/                        # JavaScript chat widget
│
├── admin/                             # Admin dashboard (Flask)
├── my_bot_army/                       # FastAPI system (legacy)
├── tests/                             # Test suites
├── migrations/                        # Database migrations
├── knowledge_base/                    # Source KB files
├── scripts/                           # Utility scripts
│
├── LLM-README.md                      # 📖 Context guide for LLMs
├── FLASK_RAG_INTEGRATION.md           # RAG integration docs
├── DEPLOYMENT_VERIFICATION.md         # Deployment report
└── requirements.txt                   # Python dependencies
```

---

## 🎯 Key Features

### RAG (Retrieval-Augmented Generation)

The bot automatically retrieves relevant information from its knowledge base before responding.

**How it works:**
1. User asks: "How much does a patio cost?"
2. System generates query embedding (Voyage AI)
3. Vector search finds relevant chunks (pgvector)
4. Context injected into system prompt
5. Claude generates response with KB context

**Configuration:** `bots/keystone-landscaping/rag_config.py`
```python
TOP_K_CHUNKS = 5                    # Retrieve top 5 chunks
SIMILARITY_THRESHOLD = 0.7          # Minimum relevance (0-1)
MAX_CONTEXT_TOKENS = 2000           # Max tokens in context
VOYAGE_MODEL = "voyage-3-lite"      # 512D embeddings
```

**Current Knowledge Base:**
- 2 documents (company info, FAQ)
- 3 chunks with embeddings
- Covers: services, pricing, warranties, timing

**Cost:** ~$0.000006-0.000012 per query (extremely affordable)

### Embeddable Chat Widget

Simple JavaScript widget for any website:

```html
<!-- Add to your website -->
<script src="http://localhost:5001/widget.js"></script>
<script>
  BotWidget.init({
    apiUrl: 'http://localhost:5001',
    botId: 'keystone-landscaping',
    position: 'bottom-right',
    primaryColor: '#2563eb',
    title: 'Chat with Keystone'
  });
</script>
```

### Conversation Management

- Full conversation history
- Session tracking
- Message persistence
- Usage tracking and billing

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Anthropic API key (Claude)
- Voyage AI API key (embeddings)

### 1. Install PostgreSQL + pgvector

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE EXTENSION vector;"

# macOS
brew install postgresql pgvector
```

### 2. Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE botfarm;
CREATE USER botfarm WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE botfarm TO botfarm;
\c botfarm
CREATE EXTENSION vector;
\q
```

### 3. Run Database Migrations

```bash
cd /opt/bot-farm
psql -U botfarm -d botfarm -f migrations/001_initial_schema.sql
# Run other migrations as needed
```

### 4. Install Python Dependencies

```bash
cd /opt/bot-farm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Configure Environment

Create `.env` file:

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
VOYAGE_API_KEY=pa-...

# Database
DB_PASSWORD=your_secure_password

# Bot Configuration
BOT_ID=keystone-landscaping
BOT_NAME=Keystone Hardscapes Assistant
PORT=5001
HOST=0.0.0.0
DEBUG=False
```

### 6. Load Knowledge Base

```bash
cd /opt/bot-farm
python3 load_keystone_kb.py
```

Expected output:
```
Bot: Keystone Hardscapes Assistant (keystone-landscaping)
[1/2] Processing: keystone_company.txt
      ✓ Created 1 chunks
[2/2] Processing: keystone_faq.txt
      ✓ Created 2 chunks
✓ Knowledge base loaded successfully!
```

### 7. Start the Bot

```bash
cd /opt/bot-farm/bots/keystone-landscaping
python3 app.py
```

You should see:
```
✓ Claude client initialized successfully
✓ RAG system initialized (model: voyage-3-lite)
✓ Bot 'Keystone Hardscapes Assistant' connected to database
 * Running on http://0.0.0.0:5001
```

### 8. Test It

```bash
# In another terminal
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services do you offer?", "session_id": "test123"}'
```

Or visit: `http://localhost:5001/test` for the test page with widget

---

## 🧪 Testing

### Run Test Suite

```bash
# RAG system tests (51 tests)
pytest tests/test_rag.py -v

# RAG query tests
python3 test_keystone_rag.py

# Chat endpoint tests
python3 test_keystone_chat_with_rag.py
```

### Manual Testing

```bash
# Start bot
cd bots/keystone-landscaping && python3 app.py &

# Test chat
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How much does interlock cost?",
    "session_id": "test"
  }' | python3 -m json.tool

# Check logs for: "RAG: Found X relevant chunks"
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [LLM-README.md](./LLM-README.md) | **START HERE** - Complete context for LLMs |
| [FLASK_RAG_INTEGRATION.md](./FLASK_RAG_INTEGRATION.md) | RAG implementation details |
| [DEPLOYMENT_VERIFICATION.md](./DEPLOYMENT_VERIFICATION.md) | Deployment report and verification |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Detailed codebase structure |
| [QUICKSTART.md](./QUICKSTART.md) | Quick setup guide |

---

## 🔧 Common Tasks

### Add Documents to Knowledge Base

```bash
# 1. Add .txt files to knowledge_base/keystone/
echo "New content here..." > knowledge_base/keystone/new_doc.txt

# 2. Update loader to include new file
nano load_keystone_kb.py

# 3. Run loader
python3 load_keystone_kb.py

# No bot restart needed - data is in database
```

### Adjust RAG Settings

```bash
# Edit configuration
nano bots/keystone-landscaping/rag_config.py

# Example: Lower similarity threshold for more results
SIMILARITY_THRESHOLD = 0.6  # Was 0.7

# Restart bot to apply
cd bots/keystone-landscaping && python3 app.py
```

### Check Knowledge Base Status

```python
from shared.database import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents WHERE bot_id = 1")
        docs = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) FROM document_chunks WHERE bot_id = 1")
        chunks = cur.fetchone()['count']

        print(f"Documents: {docs}, Chunks: {chunks}")
```

### View Bot Logs

```bash
# Bot prints to stdout
cd bots/keystone-landscaping
python3 app.py

# Look for:
# "RAG: Found X relevant chunks" - RAG is working
# "RAG: No relevant chunks found" - No matches (adjust threshold)
# "Warning: RAG search failed" - API or DB issue
```

---

## 📈 Performance & Costs

### Response Times

- **Total:** 1.5-2.5 seconds average
- RAG overhead: ~250-500ms
  - Query embedding: 200-400ms (Voyage API)
  - Vector search: 50-100ms (PostgreSQL)
- Claude API: 1-2 seconds (main latency)

### API Costs

**Voyage AI (voyage-3-lite):**
- $0.06 per 1M tokens
- ~100-200 tokens per query
- **Cost: $0.000006-0.000012 per query**

**Claude Sonnet 4.5:**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens
- Varies by conversation length

**Total cost per query:** ~$0.01-0.05 (mostly Claude)

---

## 🐛 Troubleshooting

### Bot Won't Start

**Check:**
1. Virtual environment activated?
2. Dependencies installed? `pip install -r requirements.txt`
3. `.env` file with API keys?
4. PostgreSQL running? `sudo systemctl status postgresql`
5. Database exists? `psql -U botfarm -d botfarm -c "\l"`

### RAG Not Finding Context

**Issue:** "No relevant chunks found" in logs

**Fix:**
```bash
# 1. Verify KB loaded
python3 -c "
from shared.database import get_db_connection
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM document_chunks WHERE bot_id = 1')
        print(f\"Chunks: {cur.fetchone()['count']}\")
"

# 2. If 0 chunks, load KB
python3 load_keystone_kb.py

# 3. Lower similarity threshold
nano bots/keystone-landscaping/rag_config.py
# Set SIMILARITY_THRESHOLD = 0.6
```

### API Rate Limits (429 Errors)

**Behavior:** Bot continues without RAG (graceful)

**Fix:** Wait a few minutes or implement caching

### Database Connection Errors

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U botfarm -d botfarm

# Check .env has DB_PASSWORD
cat .env | grep DB_PASSWORD
```

**See [LLM-README.md](./LLM-README.md) for complete troubleshooting guide**

---

## 🚀 Deployment

### Production Checklist

- [ ] PostgreSQL with pgvector installed
- [ ] Database migrations run
- [ ] `.env` configured with production values
- [ ] Knowledge base loaded
- [ ] Tests passing
- [ ] Bot starts without errors
- [ ] RAG retrieving context correctly
- [ ] Process manager (systemd/supervisor) configured
- [ ] Nginx reverse proxy (optional but recommended)
- [ ] SSL certificate (Let's Encrypt)
- [ ] Monitoring and logging
- [ ] Backup strategy

### Process Manager (systemd example)

```ini
# /etc/systemd/system/keystone-bot.service
[Unit]
Description=Keystone Hardscapes Bot
After=network.target postgresql.service

[Service]
Type=simple
User=chip
WorkingDirectory=/opt/bot-farm/bots/keystone-landscaping
Environment="PATH=/opt/bot-farm/venv/bin"
ExecStart=/opt/bot-farm/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable keystone-bot
sudo systemctl start keystone-bot
sudo systemctl status keystone-bot
```

---

## 🤝 Contributing

### Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes and test**
   ```bash
   pytest tests/test_rag.py -v
   python3 test_keystone_chat_with_rag.py
   ```

3. **Commit with descriptive message**
   ```bash
   git commit -m "Add feature: description

   - Detail 1
   - Detail 2

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   ```

### Code Style

- Follow PEP 8 for Python
- Use type hints where appropriate
- Write docstrings for functions
- Add tests for new features
- Update documentation

---

## 📝 License

[Add your license here]

---

## 🙋 Support

- **Issues:** [GitHub Issues](https://github.com/evgeny-vlasov/my-bot-army/issues)
- **Documentation:** See files in `/docs` and root documentation files
- **LLM Context:** [LLM-README.md](./LLM-README.md) for complete project understanding

---

## 📊 Project Status

**Current Version:** 1.0 (Production)
**Last Updated:** November 19, 2025
**Active Bots:** 1 (Keystone Hardscapes)
**RAG Status:** ✅ Fully integrated and operational
**Test Coverage:** 51 RAG tests passing
**Knowledge Base:** 2 documents, 3 chunks loaded

**Recent Milestones:**
- ✅ RAG system deployed (Nov 18, 2025)
- ✅ Schema alignment completed (Nov 19, 2025)
- ✅ Integration verified (Nov 19, 2025)
- ✅ Documentation complete (Nov 19, 2025)

---

**🤖 For LLMs:** Remember to read [LLM-README.md](./LLM-README.md) for complete context!
