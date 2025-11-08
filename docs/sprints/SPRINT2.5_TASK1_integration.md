# Sprint 2.5 - Task 1: Database Integration Module

**Claude Code Prompt**: Create a reusable database module for the Bot Army platform

---

## Context

The Bot Army platform now has a PostgreSQL database set up with 8 tables (clients, bots, subscriptions, conversations, messages, api_usage, invoices, payments). We need a Python module that provides clean, reusable functions for interacting with this database.

---

## Prerequisites

- PostgreSQL 15 database running
- Database `botfarm` exists with schema loaded
- Environment variable `DB_PASSWORD` in `/opt/bot-farm/.env`
- `psycopg2-binary` installed in venv

---

## Task: Create `shared/database.py`

Create a comprehensive database module at `/opt/bot-farm/shared/database.py` with the following requirements:

### 1. Database Connection Management

**Requirements:**
- Use `psycopg2` with `RealDictCursor` (returns dictionaries, not tuples)
- Load credentials from environment variables
- Use context manager pattern for safe connections
- Handle connection errors gracefully
- Support connection pooling for performance

**Configuration:**
```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'botfarm',
    'user': 'botfarm',
    'password': os.getenv('DB_PASSWORD')
}
```

### 2. Core Helper Functions

Create these utility functions:

#### Connection Helpers
```python
@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically commits on success, rolls back on error.
    """
    pass

def execute_query(query, params=None):
    """Execute SELECT query, return all results as list of dicts"""
    pass

def execute_update(query, params=None):
    """Execute INSERT/UPDATE/DELETE, return number of rows affected"""
    pass

def execute_one(query, params=None):
    """Execute SELECT query, return single result or None"""
    pass
```

### 3. Client Functions

```python
def get_client(client_id):
    """Get client by ID"""
    pass

def get_client_by_email(email):
    """Get client by email address"""
    pass

def create_client(name, email, company_name=None, phone=None):
    """Create a new client, return client_id"""
    pass

def update_client_status(client_id, status):
    """Update client status (active, suspended, cancelled)"""
    pass

def get_all_clients():
    """Get all clients with their subscription status"""
    pass
```

### 4. Bot Functions

```python
def get_bot_by_id(bot_id):
    """Get bot information by bot_id (e.g., 'keystone-landscaping')"""
    pass

def get_bots_by_client(client_id):
    """Get all bots for a specific client"""
    pass

def create_bot(client_id, bot_id, bot_name, port, config=None):
    """Create a new bot, return bot database id"""
    pass

def update_bot_status(bot_id, status):
    """Update bot status (active, inactive, suspended)"""
    pass

def update_bot_config(bot_id, config):
    """Update bot configuration JSON"""
    pass

def get_all_bots():
    """Get all bots with client information"""
    pass
```

### 5. Conversation & Message Functions

```python
def create_conversation(bot_id, session_id, user_ip=None):
    """Create a new conversation, return conversation_id"""
    pass

def save_message(conversation_id, role, content, tokens_used=0):
    """
    Save a message to database.
    Also increments conversation message_count and updates ended_at.
    """
    pass

def get_conversation_history(conversation_id, limit=50):
    """Get messages for a conversation"""
    pass

def end_conversation(conversation_id):
    """Mark conversation as ended"""
    pass
```

### 6. API Usage Tracking Functions

```python
def log_api_usage(bot_id, input_tokens, output_tokens, cost):
    """
    Log API usage for billing.
    Uses UPSERT (INSERT ... ON CONFLICT) to aggregate daily usage.
    If entry for bot_id + today exists, increment values.
    Otherwise, create new entry.
    """
    pass

def get_usage_by_bot(bot_id, start_date=None, end_date=None):
    """Get API usage for a bot within date range"""
    pass

def get_usage_by_client(client_id, start_date=None, end_date=None):
    """Get API usage for all of a client's bots"""
    pass

def get_daily_usage(date=None):
    """Get total usage for a specific date (default: today)"""
    pass

def calculate_cost(input_tokens, output_tokens):
    """
    Calculate cost based on current pricing.
    Claude Sonnet 4.5 pricing (as of 2025):
    - Input: $3 per million tokens
    - Output: $15 per million tokens
    """
    pass
```

### 7. Subscription Functions

```python
def get_subscription(client_id):
    """Get active subscription for client"""
    pass

def create_subscription(client_id, plan_name, price, billing_cycle):
    """Create a new subscription"""
    pass

def update_subscription_status(subscription_id, status):
    """Update subscription status"""
    pass

def mark_subscription_paid(subscription_id):
    """
    Mark subscription as paid.
    Updates last_paid_at and extends current_period_end.
    """
    pass

def get_overdue_subscriptions():
    """Get subscriptions past their end date that haven't been paid"""
    pass
```

### 8. Error Handling

**Requirements:**
- Catch and log all database errors
- Return meaningful error messages
- Never expose database internals to users
- Use try/except blocks appropriately

**Example pattern:**
```python
def get_client(client_id):
    try:
        query = "SELECT * FROM clients WHERE id = %s"
        return execute_one(query, (client_id,))
    except Exception as e:
        print(f"Error fetching client {client_id}: {e}")
        return None
```

### 9. Testing Function

Include a test function at the bottom:

```python
if __name__ == '__main__':
    """Test database connection and basic functions"""
    print("Testing database connection...")
    
    # Test connection
    try:
        bot = get_bot_by_id('keystone-landscaping')
        if bot:
            print(f"✓ Connected! Found bot: {bot['bot_name']}")
        else:
            print("✗ Bot not found")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
    
    # Test client query
    clients = get_all_clients()
    print(f"✓ Found {len(clients)} client(s)")
    
    # Test usage calculation
    cost = calculate_cost(1000, 500)
    print(f"✓ Cost calculation works: ${cost:.4f}")
```

---

## Code Quality Requirements

1. **Documentation:**
   - Docstring for every function
   - Explain parameters and return values
   - Include usage examples in docstrings

2. **Type Hints:**
   - Use type hints where appropriate
   - Example: `def get_client(client_id: int) -> dict | None:`

3. **SQL Security:**
   - ALWAYS use parameterized queries (never string interpolation)
   - Example: `cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))`
   - NEVER: `cursor.execute(f"SELECT * FROM clients WHERE id = {client_id}")`

4. **Error Handling:**
   - Catch specific exceptions
   - Log errors for debugging
   - Return None or empty list on errors (don't crash)

5. **Performance:**
   - Use indexes (already created in schema)
   - Limit result sets when appropriate
   - Close connections properly (use context managers)

6. **Naming Conventions:**
   - snake_case for functions and variables
   - Clear, descriptive names
   - Follow PEP 8 style guide

---

## File Structure

```python
"""
Database connection and helper functions for Bot Army platform.

This module provides a clean interface for interacting with the PostgreSQL
database, including functions for managing clients, bots, conversations,
and API usage tracking.

Usage:
    from shared.database import get_bot_by_id, log_api_usage
    
    bot = get_bot_by_id('keystone-landscaping')
    log_api_usage('keystone-landscaping', 1000, 500, 0.015)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv('/opt/bot-farm/.env')

# [Your code here]
```

---

## Testing After Creation

After creating the file, test it:

```bash
cd /opt/bot-farm
source venv/bin/activate
python shared/database.py
```

Should output:
```
Testing database connection...
✓ Connected! Found bot: Keystone Hardscapes Assistant
✓ Found 1 client(s)
✓ Cost calculation works: $0.0105
```

---

## Success Criteria

✅ File created at `/opt/bot-farm/shared/database.py`  
✅ All functions implemented with proper error handling  
✅ Docstrings for all functions  
✅ Parameterized queries (no SQL injection risk)  
✅ Test function runs successfully  
✅ No hardcoded credentials  
✅ Clean, readable code following PEP 8  

---

## Next Steps

After this task is complete:
1. Integrate database logging into bots (Task 2)
2. Build admin dashboard (Task 3)
3. Add usage tracking and reporting (Task 4)

---

## Notes

- The database module is shared across ALL bots
- Keep it simple and focused on database operations
- Business logic belongs in bot apps, not in database module
- This is a foundational piece - make it robust!

---

**Build it with Claude Code!** 🚀

Read this prompt and create the complete `shared/database.py` module following all requirements and best practices.
