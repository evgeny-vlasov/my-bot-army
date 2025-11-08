# Sprint 2.5 - Task 2: Bot Database Integration

**Claude Code Prompt**: Integrate database logging into existing bots

---

## Context

We now have:
- ✅ PostgreSQL database with schema
- ✅ `shared/database.py` module with helper functions

Now we need to integrate database logging into the bot applications so they:
- Store conversations and messages
- Track API usage for billing
- Log errors and events

---

## Prerequisites

- Sprint 2.5 Task 1 completed (`shared/database.py` exists)
- Bots are running (e.g., `bots/keystone-landscaping/app.py`)
- Database is accessible and has initial data

---

## Task: Update Bot Applications

### Files to Modify

1. `bots/keystone-landscaping/app.py` - Add database logging
2. `shared/claude_client.py` - Track API usage automatically
3. Test and verify logging works

---

## Part 1: Update `shared/claude_client.py`

### Current Structure

The Claude client currently just calls the API and returns responses.

### Required Changes

Add automatic API usage tracking:

```python
"""
Claude API client with automatic usage tracking
"""
import anthropic
import os
from dotenv import load_dotenv

# Import database functions
import sys
sys.path.insert(0, '/opt/bot-farm')
from shared.database import log_api_usage, calculate_cost

load_dotenv('/opt/bot-farm/.env')

class ClaudeClient:
    def __init__(self, bot_id=None):
        """
        Initialize Claude client
        
        Args:
            bot_id: Optional bot identifier for usage tracking
        """
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 1024
        self.bot_id = bot_id  # NEW: Store bot_id for tracking
    
    def chat(self, message, system_prompt, conversation_history=None):
        """
        Send message to Claude and track usage
        
        Args:
            message: User message
            system_prompt: System prompt for bot personality
            conversation_history: Optional list of previous messages
            
        Returns:
            str: Claude's response
        """
        messages = conversation_history or []
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=messages
        )
        
        # NEW: Track API usage in database
        if self.bot_id:
            try:
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = calculate_cost(input_tokens, output_tokens)
                
                log_api_usage(self.bot_id, input_tokens, output_tokens, cost)
            except Exception as e:
                print(f"Warning: Failed to log API usage: {e}")
        
        return response.content[0].text
```

**Key Changes:**
1. Accept `bot_id` in constructor
2. Import database functions
3. After API call, log usage to database
4. Handle logging errors gracefully (don't break bot if DB fails)

---

## Part 2: Update `bots/keystone-landscaping/app.py`

### Current Structure

The bot currently:
- Receives messages via `/api/chat` endpoint
- Calls Claude API
- Returns response

### Required Changes

Add conversation and message logging:

#### 1. Import Database Functions

```python
# Add to imports at top of file
import sys
sys.path.insert(0, '/opt/bot-farm')
from shared.database import (
    get_bot_by_id,
    create_conversation,
    save_message,
    get_conversation_history
)
from shared.claude_client import ClaudeClient
from config import Config
from prompts import SYSTEM_PROMPT
```

#### 2. Initialize Claude Client with bot_id

```python
# Update initialization
bot_id = Config.BOT_ID
claude_client = ClaudeClient(bot_id=bot_id)  # Pass bot_id for tracking

# Verify bot exists in database on startup
try:
    bot_info = get_bot_by_id(bot_id)
    if bot_info:
        print(f"✓ Bot '{bot_info['bot_name']}' connected to database")
    else:
        print(f"⚠ Warning: Bot '{bot_id}' not found in database")
except Exception as e:
    print(f"⚠ Warning: Could not verify bot in database: {e}")
```

#### 3. Update `/api/chat` Endpoint

Add conversation and message logging:

```python
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint with database logging
    """
    try:
        # Get request data
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        session_id = data.get('session_id')  # NEW: Get session ID from client
        
        # Validate input
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        if len(user_message) > Config.MAX_MESSAGE_LENGTH:
            return jsonify({'error': 'Message too long'}), 400
        
        # Get or create conversation
        conversation_id = None
        if session_id:
            try:
                # Try to find existing conversation
                # If new session, create conversation in database
                user_ip = request.remote_addr
                conversation_id = create_conversation(Config.BOT_ID, session_id, user_ip)
            except Exception as e:
                print(f"Warning: Could not create conversation: {e}")
        
        # Trim conversation history
        if len(conversation_history) > Config.MAX_CONVERSATION_HISTORY:
            conversation_history = conversation_history[-Config.MAX_CONVERSATION_HISTORY:]
        
        # Save user message to database
        if conversation_id:
            try:
                save_message(conversation_id, 'user', user_message)
            except Exception as e:
                print(f"Warning: Could not save user message: {e}")
        
        # Get response from Claude
        response_text = claude_client.chat(
            message=user_message,
            system_prompt=SYSTEM_PROMPT,
            conversation_history=conversation_history
        )
        
        # Save assistant response to database
        if conversation_id:
            try:
                save_message(conversation_id, 'assistant', response_text)
            except Exception as e:
                print(f"Warning: Could not save assistant message: {e}")
        
        # Return response
        return jsonify({
            'response': response_text,
            'status': 'success'
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            'error': 'An error occurred processing your message',
            'status': 'error'
        }), 500
```

**Key Changes:**
1. Accept `session_id` from client (widget needs to send this)
2. Create conversation record in database
3. Save user message before calling Claude
4. Save assistant response after getting it
5. Handle all database errors gracefully (don't break chat if DB fails)

---

## Part 3: Update Widget to Send session_id

### Modify `shared/widget/bot-widget.js`

The widget needs to generate and maintain a session ID:

```javascript
// Near the top of the init() function, add:
const sessionId = sessionStorage.getItem('bot_session_id') || 
                  'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
sessionStorage.setItem('bot_session_id', sessionId);

// In sendMessage() function, update the API call:
fetch(`${config.apiUrl}/api/chat`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: userMessage,
        conversation_history: conversationHistory,
        session_id: sessionId  // NEW: Send session ID
    })
})
```

**What this does:**
- Generates unique session ID on first visit
- Stores in sessionStorage (persists across page refreshes)
- Sends with every message so server can track conversations

---

## Part 4: Add Admin Endpoint

Add a simple endpoint to view bot statistics:

```python
@app.route('/admin/stats', methods=['GET'])
def stats():
    """
    Get bot statistics (for admin dashboard)
    Authentication should be added in production!
    """
    try:
        from shared.database import execute_query
        
        # Get today's usage
        today_usage = execute_query("""
            SELECT 
                requests,
                input_tokens,
                output_tokens,
                cost
            FROM api_usage
            WHERE bot_id = %s AND date = CURRENT_DATE
        """, (Config.BOT_ID,))
        
        # Get total conversations
        total_conversations = execute_query("""
            SELECT COUNT(*) as count
            FROM conversations
            WHERE bot_id = %s
        """, (Config.BOT_ID,))
        
        # Get total messages
        total_messages = execute_query("""
            SELECT COUNT(*) as count
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.bot_id = %s
        """, (Config.BOT_ID,))
        
        return jsonify({
            'bot_id': Config.BOT_ID,
            'today_usage': today_usage[0] if today_usage else None,
            'total_conversations': total_conversations[0]['count'] if total_conversations else 0,
            'total_messages': total_messages[0]['count'] if total_messages else 0,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500
```

---

## Testing

### Test 1: Verify Database Logging

```bash
# Start the bot
cd /opt/bot-farm/bots/keystone-landscaping
source ../../venv/bin/activate
python app.py
```

In another terminal:

```bash
# Send a test message
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What services do you offer?",
    "session_id": "test_session_123"
  }'

# Check database
psql -U botfarm -d botfarm -h localhost

# View conversations
SELECT * FROM conversations;

# View messages
SELECT * FROM messages;

# View API usage
SELECT * FROM api_usage WHERE date = CURRENT_DATE;
```

### Test 2: Check Stats Endpoint

```bash
curl http://localhost:5000/admin/stats
```

Should return JSON with usage statistics.

### Test 3: Widget Test

Open test HTML page and chat. Then check database:

```sql
SELECT 
    c.session_id,
    c.message_count,
    c.started_at
FROM conversations c
WHERE c.bot_id = 'keystone-landscaping'
ORDER BY c.started_at DESC
LIMIT 5;
```

---

## Error Handling Requirements

**CRITICAL**: Database logging should NEVER break the bot!

1. ✅ Wrap all database calls in try/except
2. ✅ Log errors but continue execution
3. ✅ If database is down, bot should still work (just no logging)
4. ✅ Return helpful responses even if logging fails

**Example Pattern:**
```python
try:
    save_message(conversation_id, 'user', user_message)
except Exception as e:
    print(f"Warning: Could not save message: {e}")
    # Continue anyway - don't crash!
```

---

## Success Criteria

✅ Claude client tracks API usage automatically  
✅ Bot logs conversations and messages  
✅ Widget sends session_id with requests  
✅ Stats endpoint returns usage data  
✅ Bot continues working even if database fails  
✅ Test messages appear in database  
✅ API usage is tracked daily  
✅ No errors in bot logs  

---

## Performance Considerations

1. **Don't block responses**: Database writes should be fast
2. **Index usage**: We have indexes on frequently queried columns
3. **Connection pooling**: Context managers handle this
4. **Async option**: For high traffic, consider async database writes

---

## Security Notes

1. **Don't log sensitive data**: Be careful about user input
2. **Sanitize before storage**: No SQL injection via stored messages
3. **Admin endpoint**: Add authentication in production!
4. **Rate limiting**: Consider adding to prevent abuse

---

## Next Steps

After integration is complete:
- Task 3: Build admin dashboard to view this data
- Task 4: Add usage reports and billing integration

---

**Build it with Claude Code!** 🚀

Update the existing bot files to add comprehensive database logging while maintaining reliability and performance.
