# Sprint 2.5: Database Setup & Integration

**Goal**: Add PostgreSQL database for storing clients, bots, conversations, and usage data.

**Status**: ✅ Infrastructure Complete | ⏳ Code Integration Pending  
**Time to Complete**: ~2 hours (1 hour infrastructure, 1 hour integration)  
**Prerequisites**: Debian 12 server with sudo access

---

## Overview

This sprint adds a robust PostgreSQL database to the Bot Army platform, enabling:
- ✅ Client and subscription management
- ✅ Bot tracking and configuration
- ✅ Conversation history storage
- ✅ API usage tracking for billing
- ✅ Wave invoice integration
- ✅ Analytics and reporting

---

## Table of Contents

1. [Infrastructure Setup](#infrastructure-setup) (Manual - Done)
2. [Database Schema](#database-schema)
3. [Python Integration](#python-integration) (Claude Code)
4. [Bot Integration](#bot-integration) (Claude Code)
5. [Admin Dashboard](#admin-dashboard) (Claude Code)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Infrastructure Setup

### 1. Install PostgreSQL

```bash
# Update system
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Verify installation
psql --version
# Should show: psql (PostgreSQL) 15.x
```

### 2. Create Database and User

```bash
# Switch to postgres user
sudo -i -u postgres

# Open PostgreSQL prompt
psql
```

Run these SQL commands:

```sql
-- Create database
CREATE DATABASE botfarm;

-- Create user with password
CREATE USER botfarm WITH PASSWORD 'your-secure-password-here';

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE botfarm TO botfarm;

-- Make botfarm owner of database (important for PostgreSQL 15+)
ALTER DATABASE botfarm OWNER TO botfarm;

-- Exit
\q
```

Exit postgres user:
```bash
exit
```

### 3. Configure Authentication

Edit PostgreSQL authentication config:

```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Add this line **before** the existing `local all all peer` line:

```
local   botfarm         botfarm                                 md5
```

This allows the `botfarm` user to connect with a password.

**What this means:**
- `local` = Unix socket connection (local machine only)
- `botfarm` (first) = database name
- `botfarm` (second) = username
- `md5` = password authentication required

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
sudo systemctl status postgresql
```

### 4. Test Connection

```bash
# Test connecting as botfarm user
psql -U botfarm -d botfarm -h localhost

# Enter password when prompted
# You should see: botfarm=>

# Test it works
\dt

# Should say "Did not find any relations" (empty database)

# Exit
\q
```

---

## Database Schema

### Schema Overview

The database consists of 8 core tables:

```
clients          # Customer information
  ├── bots              # Bot instances
  ├── subscriptions     # Billing & plans
  ├── invoices          # Invoice tracking
  └── payments          # Payment history

bots
  ├── conversations     # Chat sessions
  │     └── messages    # Individual messages
  └── api_usage         # Daily usage stats
```

### Create Schema

Create the schema file:

```bash
cd /opt/bot-farm
nano schema.sql
```

Paste this complete schema:

```sql
-- Clients/Customers
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'  -- active, suspended, cancelled
);

-- Bots
CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    bot_id VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'keystone-landscaping'
    bot_name VARCHAR(255) NOT NULL,       -- e.g., 'Keystone Hardscapes Assistant'
    port INTEGER UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, suspended
    config JSONB,                         -- Bot configuration as JSON
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    plan_name VARCHAR(100) NOT NULL,      -- 'basic', 'pro', 'enterprise'
    price DECIMAL(10,2) NOT NULL,
    billing_cycle VARCHAR(50) NOT NULL,   -- 'monthly', 'annual'
    status VARCHAR(50) DEFAULT 'active',  -- active, past_due, cancelled
    current_period_start DATE NOT NULL,
    current_period_end DATE NOT NULL,
    wave_invoice_id VARCHAR(255),         -- Wave integration
    last_paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(100) REFERENCES bots(bot_id),
    session_id VARCHAR(255) NOT NULL,
    user_ip VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0
);

-- Messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL,            -- 'user', 'assistant'
    content TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API Usage (for billing and monitoring)
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(100) REFERENCES bots(bot_id),
    date DATE NOT NULL,
    requests INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0,
    UNIQUE(bot_id, date)
);

-- Invoices
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, paid, overdue, cancelled
    due_date DATE NOT NULL,
    paid_at TIMESTAMP,
    wave_invoice_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payments
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    invoice_id INTEGER REFERENCES invoices(id),
    wave_payment_id VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),           -- 'credit_card', 'bank_transfer'
    paid_at TIMESTAMP DEFAULT NOW(),
    wave_fee DECIMAL(10,2)
);

-- Performance Indexes
CREATE INDEX idx_bots_client_id ON bots(client_id);
CREATE INDEX idx_conversations_bot_id ON conversations(bot_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_api_usage_bot_date ON api_usage(bot_id, date);
CREATE INDEX idx_subscriptions_client_id ON subscriptions(client_id);
```

Load the schema:

```bash
psql -U botfarm -d botfarm -h localhost -f schema.sql
```

Verify tables were created:

```bash
psql -U botfarm -d botfarm -h localhost -c "\dt"
```

Should show all 8 tables!

### Add Initial Data

Create initial data file:

```bash
nano initial_data.sql
```

```sql
-- Example: Add first client (Keystone Hardscapes)
INSERT INTO clients (name, email, company_name, phone, status)
VALUES ('Andrew', 'andrew@keystonehardscapes.com', 'Keystone Hardscapes', NULL, 'active');

-- Add Keystone bot
INSERT INTO bots (client_id, bot_id, bot_name, port, status, config)
VALUES (
    1,
    'keystone-landscaping',
    'Keystone Hardscapes Assistant',
    5000,
    'active',
    '{"primary_color": "#2563eb", "position": "bottom-right"}'::jsonb
);

-- Add subscription (testing, free)
INSERT INTO subscriptions (
    client_id,
    plan_name,
    price,
    billing_cycle,
    status,
    current_period_start,
    current_period_end
)
VALUES (
    1,
    'testing',
    0.00,
    'monthly',
    'active',
    CURRENT_DATE,
    CURRENT_DATE + INTERVAL '1 month'
);
```

Load initial data:

```bash
psql -U botfarm -d botfarm -h localhost -f initial_data.sql
```

Verify:

```bash
psql -U botfarm -d botfarm -h localhost -c "SELECT * FROM clients;"
psql -U botfarm -d botfarm -h localhost -c "SELECT * FROM bots;"
```

---

## Python Integration

### Install Dependencies

```bash
# As botfarm user with venv activated
sudo -u botfarm bash
cd /opt/bot-farm
source venv/bin/activate

# Install PostgreSQL library
pip install psycopg2-binary

# Update requirements.txt
echo "psycopg2-binary==2.9.9" >> bots/keystone-landscaping/requirements.txt
```

### Configure Environment

Add database password to `.env`:

```bash
nano /opt/bot-farm/.env
```

Add:
```
DB_PASSWORD=your-postgres-password-here
```

### Database Module

**See**: `SPRINT2.5_TASK1_integration.md` for Claude Code prompt to create:
- `shared/database.py` - Database connection and helper functions
- Integration with existing bots
- Usage tracking

---

## Bot Integration

**See**: `SPRINT2.5_TASK2_bot_integration.md` for Claude Code prompt to:
- Integrate database logging into bots
- Store conversations and messages
- Track API usage for billing
- Add session management

---

## Admin Dashboard

**See**: `SPRINT2.5_TASK3_admin_dashboard.md` for Claude Code prompt to:
- Build Flask admin interface
- View clients and bots
- Monitor usage and costs
- Control bot status (start/stop)
- Generate reports

---

## Testing

### Manual Database Tests

```bash
# Connect to database
psql -U botfarm -d botfarm -h localhost

# View all clients
SELECT * FROM clients;

# View all bots with client info
SELECT 
    c.name as client_name,
    b.bot_name,
    b.port,
    b.status,
    s.plan_name,
    s.price
FROM bots b
JOIN clients c ON b.client_id = c.id
JOIN subscriptions s ON s.client_id = c.id;

# View API usage summary
SELECT 
    bot_id,
    SUM(requests) as total_requests,
    SUM(cost) as total_cost
FROM api_usage
GROUP BY bot_id;

# Exit
\q
```

### Python Connection Test

Create a test script:

```bash
nano test_db.py
```

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Test connection
try:
    conn = psycopg2.connect(
        host='localhost',
        database='botfarm',
        user='botfarm',
        password=os.getenv('DB_PASSWORD'),
        cursor_factory=RealDictCursor
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients;")
    clients = cursor.fetchall()
    
    print("✓ Database connection successful!")
    print(f"✓ Found {len(clients)} client(s)")
    for client in clients:
        print(f"  - {client['name']} ({client['email']})")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Database connection failed: {e}")
```

Run test:

```bash
python test_db.py
```

---

## Troubleshooting

### "peer authentication failed"

**Problem**: Can't connect with password

**Solution**: Check `pg_hba.conf` has `md5` authentication:
```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Make sure this line exists:
```
local   botfarm         botfarm                                 md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

### "permission denied for schema public"

**Problem**: User can't create tables

**Solution**: Make botfarm owner of database:
```bash
sudo -u postgres psql
```

```sql
ALTER DATABASE botfarm OWNER TO botfarm;
\q
```

---

### "relation already exists"

**Problem**: Trying to create tables that already exist

**Solution**: This is normal if you run schema.sql twice. Either:

**Option A**: Drop and recreate (loses data):
```sql
DROP TABLE IF EXISTS payments, invoices, api_usage, messages, 
                     conversations, subscriptions, bots, clients CASCADE;
```

**Option B**: Just continue - tables already exist

---

### "psycopg2 not found"

**Problem**: Python can't find PostgreSQL library

**Solution**: Make sure venv is activated and library is installed:
```bash
source venv/bin/activate
pip install psycopg2-binary
```

---

### Can't connect to PostgreSQL

**Problem**: PostgreSQL not running

**Solution**: Check status and start if needed:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Start on boot
```

---

## Database Maintenance

### Backup Database

```bash
# Backup to file
pg_dump -U botfarm -h localhost botfarm > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U botfarm -h localhost botfarm < backup_20250107.sql
```

### View Database Size

```bash
psql -U botfarm -d botfarm -h localhost -c "
SELECT 
    pg_size_pretty(pg_database_size('botfarm')) as database_size;
"
```

### Clean Old Data

```sql
-- Delete messages older than 90 days
DELETE FROM messages 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete old conversations
DELETE FROM conversations 
WHERE ended_at < NOW() - INTERVAL '90 days';
```

---

## Next Steps

After database infrastructure is set up:

1. **Task 1**: Create `shared/database.py` module (Claude Code)
2. **Task 2**: Integrate database with bots (Claude Code)
3. **Task 3**: Build admin dashboard (Claude Code)
4. **Task 4**: Add usage tracking and reporting (Claude Code)

See the individual task prompts for Claude Code implementation.

---

## Summary

**What We Built:**
- ✅ PostgreSQL 15 database server
- ✅ `botfarm` database with 8 tables
- ✅ Proper authentication and permissions
- ✅ Initial data (first client & bot)
- ✅ Python libraries installed

**What's Next:**
- ⏳ Python database module
- ⏳ Bot integration
- ⏳ Admin dashboard
- ⏳ Usage tracking & billing

**Time Investment:**
- Infrastructure: ~1 hour (done)
- Code integration: ~2-3 hours (via Claude Code)

**Result:**
A professional, scalable database foundation for the Bot Army platform that enables client management, billing, analytics, and growth to 100+ bots.

---

**Sprint 2.5 Complete!** 🎉

Database infrastructure is ready. Proceed to Task 1 for Claude Code integration.
