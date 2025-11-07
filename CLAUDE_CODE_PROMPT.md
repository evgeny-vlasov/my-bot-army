# Claude Code Build Instructions

**Project**: My Bot Army - Multi-Bot AI Assistant Platform  
**First Bot**: Keystone Hardscapes Landscaping Assistant  
**Build Tool**: Claude Code  

## Project Overview

Build a scalable platform for hosting multiple AI chatbot instances. Each bot serves a different client/purpose and can be embedded on any website via a JavaScript snippet. The first bot is for Keystone Hardscapes, a landscaping contractor in Alberta, Canada.

## Technical Requirements

### Backend
- **Framework**: Flask (Python 3.11+)
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)
- **Key Features**:
  - RESTful API endpoints
  - CORS support for cross-origin requests
  - Conversation context management
  - Health check endpoint
  - Environment-based configuration

### Frontend Widget
- **Technology**: Vanilla JavaScript (no frameworks)
- **Features**:
  - Embeddable via `<script>` tag
  - Floating chat bubble (customizable position)
  - Minimizable chat window
  - Conversation history in session
  - Responsive design (mobile-friendly)
  - Customizable colors and branding

### Deployment
- **Server**: Debian 12 Linux
- **Process**: systemd service
- **User**: botfarm (non-privileged)
- **Location**: /opt/bot-farm/

## File Structure to Create

```
/opt/bot-farm/
├── .env.example                    # Example environment variables
├── .gitignore                      # Git ignore file
├── README.md                       # Already created
├── SETUP.md                        # Already created
├── shared/
│   ├── __init__.py                # Make it a package
│   ├── claude_client.py           # Reusable Claude API client
│   └── widget/
│       ├── bot-widget.js          # Embeddable JavaScript widget
│       └── bot-widget.css         # Widget styling
├── bots/
│   └── keystone-landscaping/
│       ├── app.py                 # Flask application
│       ├── config.py              # Configuration
│       ├── prompts.py             # System prompt
│       └── requirements.txt       # Python dependencies
└── nginx/
    └── bot-farm.conf.example      # Example nginx config
```

## Build Instructions

### 1. Shared Components

#### File: `shared/__init__.py`
- Empty file to make shared/ a Python package

#### File: `shared/claude_client.py`

**Purpose**: Reusable wrapper for Anthropic Claude API

**Requirements**:
- Import anthropic SDK and os, dotenv
- Load .env from /opt/bot-farm/.env
- Class: `ClaudeClient`
  - Initialize with Anthropic API key from environment
  - Method: `chat(message, system_prompt, conversation_history=None)`
    - Takes user message, system prompt, and optional conversation history
    - Returns Claude's text response
    - Uses model: claude-sonnet-4-20250514
    - Max tokens: 1024
    - Appends user message to history
    - Returns response.content[0].text

**Example usage**:
```python
client = ClaudeClient()
response = client.chat(
    message="Hello!",
    system_prompt="You are a helpful assistant.",
    conversation_history=[{"role": "user", "content": "Hi"}]
)
```

---

#### File: `shared/widget/bot-widget.js`

**Purpose**: Embeddable chat widget for client websites

**Requirements**:

**Structure**:
- IIFE pattern to avoid global namespace pollution
- Create `window.BotWidget` object with `init()` method

**Features to implement**:
1. **Configuration** (via `init()` method):
   - `apiUrl`: Bot API endpoint (required)
   - `botId`: Bot identifier (required)
   - `position`: 'bottom-right' | 'bottom-left' (default: bottom-right)
   - `primaryColor`: Hex color (default: #2563eb)
   - `title`: Chat window title (default: "Chat with us")

2. **UI Components**:
   - Chat bubble button (floating, fixed position)
   - Chat window (popup/modal style)
   - Message list (scrollable)
   - Input field + send button
   - Minimize/close buttons
   - Loading indicator

3. **Functionality**:
   - Toggle chat window on bubble click
   - Send messages to API endpoint: `POST /api/chat`
   - Display user messages immediately
   - Show typing indicator while waiting for response
   - Display bot responses
   - Maintain conversation history in sessionStorage
   - Auto-scroll to latest message
   - Handle API errors gracefully
   - Mobile responsive

4. **Styling**:
   - Use inline styles or inject CSS
   - Smooth animations (fade in/out, slide up)
   - Professional, modern design
   - Z-index high enough to appear over most content
   - Box shadow for depth

**API Request Format**:
```javascript
POST /api/chat
Content-Type: application/json

{
  "message": "user message here",
  "conversation_history": [
    {"role": "user", "content": "previous message"},
    {"role": "assistant", "content": "previous response"}
  ]
}
```

**API Response Format**:
```javascript
{
  "response": "bot response here",
  "status": "success"
}
```

**Example HTML embed**:
```html
<script src="http://your-server:5000/widget.js"></script>
<script>
  BotWidget.init({
    apiUrl: 'http://your-server:5000',
    botId: 'keystone-landscaping',
    position: 'bottom-right',
    primaryColor: '#2563eb',
    title: 'Chat with Keystone'
  });
</script>
```

---

#### File: `shared/widget/bot-widget.css`

**Purpose**: Styling for the chat widget (if not using inline styles)

**Requirements**:
- Style for chat bubble button
- Style for chat window
- Style for messages (user vs bot)
- Style for input field
- Responsive design
- Smooth transitions
- Professional appearance

Alternatively, this can be embedded in the JS file as inline styles.

---

### 2. Keystone Landscaping Bot

#### File: `bots/keystone-landscaping/requirements.txt`

```
flask==3.0.0
anthropic==0.39.0
python-dotenv==1.0.0
flask-cors==4.0.0
```

---

#### File: `bots/keystone-landscaping/config.py`

**Purpose**: Configuration settings for the bot

**Requirements**:
```python
import os

class Config:
    # Server settings
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False
    
    # Bot settings
    BOT_ID = 'keystone-landscaping'
    BOT_NAME = 'Keystone Hardscapes Assistant'
    
    # API settings
    MAX_CONVERSATION_HISTORY = 10  # Keep last 10 messages
    MAX_MESSAGE_LENGTH = 1000      # Max chars per message
    
    # CORS settings
    CORS_ORIGINS = ['*']  # In production, specify actual domains
```

---

#### File: `bots/keystone-landscaping/prompts.py`

**Purpose**: System prompt defining the bot's personality and knowledge

**Requirements**:

Create a comprehensive system prompt that includes:

**About Keystone Hardscapes**:
- Owner: Andrew (owner and lead craftsman)
- Location: Alberta, Canada
- Service areas: Calgary, Airdrie, Cochrane, Okotoks, Chestermere, and nearby areas

**Services**:
1. **Landscaping & Hardscape**:
   - Patios and retaining walls
   - Complete backyard transformations
   - Owner-led quality control
   - 5-year workmanship warranty
   - Built for Alberta climate (proper base prep, geotextiles, drainage)

2. **Snow Removal**:
   - Residential and commercial properties
   - Timely clearing for winter safety
   - Trigger options available

3. **Concrete Restoration**:
   - Epoxy and overlay applications
   - Restore instead of replace
   - High-quality materials

**Key Features**:
- Transparent, itemized quotes (no hidden fees)
- Owner personally oversees every project
- 5-year warranty on hardscape work
- Built to withstand Alberta winters

**Scheduling**:
- Hardscape season: Spring-Fall (weather-dependent, book early for prime dates)
- Snow services: Residential & commercial routes with trigger options

**Bot Personality**:
- Friendly and professional
- Knowledgeable about landscaping and Alberta climate
- Helpful without being pushy
- Encourages users to request a quote for specific pricing
- Can provide general pricing ranges but always suggests a detailed quote
- Can answer questions about services, materials, process, timeline

**Bot Guidelines**:
- Answer questions about services, scheduling, and general landscaping advice
- Guide customers toward the contact form for detailed quotes
- Be honest if you don't know something
- Keep responses concise but informative
- Use Canadian English spelling

**Example interactions to handle**:
- "What services do you offer?"
- "How much does a patio cost?"
- "Do you service Airdrie?"
- "What's your warranty?"
- "Can you help with my sloped backyard?"
- "Do you do snow removal?"

Store the prompt in a variable: `SYSTEM_PROMPT = """..."""`

---

#### File: `bots/keystone-landscaping/app.py`

**Purpose**: Main Flask application for the Keystone bot

**Requirements**:

**Imports**:
- Flask, request, jsonify
- flask_cors (CORS)
- sys.path manipulation to import from shared/
- ClaudeClient from shared.claude_client
- Config from config
- SYSTEM_PROMPT from prompts

**Flask App Setup**:
- Initialize Flask app
- Enable CORS with config origins
- Initialize ClaudeClient

**Endpoints**:

1. **GET /**
   - Simple welcome message
   - Returns JSON: `{"message": "Keystone Hardscapes Bot API", "status": "running"}`

2. **GET /health**
   - Health check endpoint
   - Returns JSON: `{"status": "healthy", "bot": "keystone-landscaping"}`

3. **GET /widget.js**
   - Serve the JavaScript widget
   - Set Content-Type: application/javascript
   - Read and return shared/widget/bot-widget.js

4. **POST /api/chat**
   - Main chat endpoint
   - Accept JSON: `{"message": str, "conversation_history": list (optional)}`
   - Validate input:
     - Check message exists and is string
     - Check message length (use Config.MAX_MESSAGE_LENGTH)
     - Validate conversation_history format if provided
   - Trim conversation history (use Config.MAX_CONVERSATION_HISTORY)
   - Call claude_client.chat() with message, SYSTEM_PROMPT, and history
   - Return JSON: `{"response": str, "status": "success"}`
   - Handle errors gracefully:
     - Invalid input: 400 error
     - API errors: 500 error with safe error message
     - Catch all exceptions

**Error Handling**:
- Use try/except blocks
- Return appropriate HTTP status codes
- Log errors (print to console)
- Never expose API keys or sensitive details in errors

**Main Block**:
```python
if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
```

**Code Quality**:
- Clean, readable code
- Proper error handling
- Input validation
- Comments for clarity
- Follow PEP 8 style guide

---

### 3. Configuration Files

#### File: `.env.example`

```
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Bot Configuration (Optional)
DEBUG=False
```

---

#### File: `.gitignore`

```
# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
```

---

### 4. nginx Configuration

#### File: `nginx/bot-farm.conf.example`

**Purpose**: Example nginx reverse proxy configuration

**Requirements**:
- Server block listening on port 80
- Proxy pass to localhost:5000 (Keystone bot)
- Include for /keystone/ location
- Headers for proxying (X-Real-IP, X-Forwarded-For, etc.)
- WebSocket support headers
- Comment showing how to add more bots

**Example**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Keystone Landscaping Bot
    location /keystone/ {
        proxy_pass http://localhost:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Add more bots here:
    # location /another-bot/ {
    #     proxy_pass http://localhost:5001/;
    #     ...
    # }
}
```

---

## Testing Instructions

### 1. Manual Testing

After building, test with these steps:

**Start the bot**:
```bash
cd /opt/bot-farm/bots/keystone-landscaping
source ../../venv/bin/activate
python app.py
```

**Test health endpoint**:
```bash
curl http://localhost:5000/health
```

**Test chat endpoint**:
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What services do you offer?"
  }'
```

**Test widget**:
Create a simple HTML file:
```html
<!DOCTYPE html>
<html>
<head><title>Widget Test</title></head>
<body>
  <h1>Test Page</h1>
  <script src="http://localhost:5000/widget.js"></script>
  <script>
    BotWidget.init({
      apiUrl: 'http://localhost:5000',
      botId: 'keystone-landscaping',
      position: 'bottom-right',
      primaryColor: '#2563eb',
      title: 'Chat with Keystone'
    });
  </script>
</body>
</html>
```

Open in browser and test the chat functionality.

---

## Code Quality Guidelines

1. **Python**:
   - Follow PEP 8 style guide
   - Use type hints where appropriate
   - Include docstrings for functions
   - Handle errors gracefully
   - Validate all inputs

2. **JavaScript**:
   - Use modern ES6+ syntax
   - Avoid global namespace pollution
   - Use descriptive variable names
   - Add comments for complex logic
   - Handle edge cases

3. **Security**:
   - Never expose API keys
   - Validate and sanitize user input
   - Use HTTPS in production
   - Implement rate limiting (future)
   - Follow OWASP best practices

4. **Performance**:
   - Minimize API calls
   - Efficient conversation history management
   - Lazy load widget resources
   - Optimize CSS/JS delivery

---

## Future Enhancements (Not in v1.0)

These are ideas for future development but NOT required now:

- Database for conversation persistence
- User authentication
- Analytics dashboard
- Rate limiting per IP/client
- Multi-language support
- Voice input/output
- File upload support
- Integration with calendars/CRM
- A/B testing framework

---

## Success Criteria

The build is successful when:

✅ All files are created with correct structure  
✅ Flask app starts without errors  
✅ Health endpoint returns 200 OK  
✅ Chat endpoint accepts messages and returns Claude responses  
✅ Widget loads and displays on test page  
✅ Widget can send messages and display responses  
✅ Conversation history is maintained in session  
✅ Code is clean, commented, and follows best practices  
✅ No API keys or secrets are hardcoded  

---

## Notes for Claude Code

- Use the project structure exactly as specified
- Prioritize code quality and error handling
- Add helpful comments in the code
- Make the widget user-friendly and professional
- Ensure all paths are correct for /opt/bot-farm/ deployment
- Test API integration thoroughly
- Keep the design simple but effective

---

**Ready to build!** Use this prompt to create the complete My Bot Army platform with Claude Code. 🚀
