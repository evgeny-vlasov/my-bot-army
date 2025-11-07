# Project Structure Reference

Quick reference for the My Bot Army project layout and key information.

## Directory Tree

```
/opt/bot-farm/
│
├── .env                           # API keys (NOT in git)
├── .env.example                   # Example environment file
├── .gitignore                     # Git ignore patterns
├── README.md                      # Project overview
├── SETUP.md                       # Server setup guide
├── CLAUDE_CODE_PROMPT.md          # Build instructions for Claude Code
├── PROJECT_STRUCTURE.md           # This file
│
├── venv/                          # Python virtual environment (NOT in git)
│   └── ...
│
├── shared/                        # Shared utilities for all bots
│   ├── __init__.py               # Python package marker
│   ├── claude_client.py          # Reusable Claude API wrapper
│   │
│   └── widget/                   # Embeddable chat widget
│       ├── bot-widget.js         # Widget JavaScript
│       └── bot-widget.css        # Widget styling (optional)
│
├── bots/                         # Individual bot instances
│   │
│   ├── keystone-landscaping/     # Bot #1: Landscaping contractor
│   │   ├── app.py               # Flask application
│   │   ├── config.py            # Bot configuration
│   │   ├── prompts.py           # System prompt & personality
│   │   └── requirements.txt     # Python dependencies
│   │
│   ├── future-bot-2/            # Bot #2: Future addition
│   │   └── ...
│   │
│   └── future-bot-3/            # Bot #3: Future addition
│       └── ...
│
└── nginx/                        # Reverse proxy configs
    └── bot-farm.conf.example     # Example nginx configuration
```

## File Purposes

### Root Level

| File | Purpose | In Git? |
|------|---------|---------|
| `.env` | API keys and secrets | ❌ No |
| `.env.example` | Template for .env | ✅ Yes |
| `.gitignore` | Files to exclude from git | ✅ Yes |
| `README.md` | Project documentation | ✅ Yes |
| `SETUP.md` | Server setup instructions | ✅ Yes |
| `CLAUDE_CODE_PROMPT.md` | Build instructions | ✅ Yes |
| `PROJECT_STRUCTURE.md` | This reference | ✅ Yes |
| `venv/` | Python virtual environment | ❌ No |

### Shared Components

| File | Purpose | Used By |
|------|---------|---------|
| `shared/__init__.py` | Package marker | Python import system |
| `shared/claude_client.py` | Claude API wrapper | All bots |
| `shared/widget/bot-widget.js` | Embeddable widget | Client websites |
| `shared/widget/bot-widget.css` | Widget styles | Widget JS |

### Bot-Specific Files

| File | Purpose | Customizable? |
|------|---------|---------------|
| `app.py` | Flask web server | Per bot |
| `config.py` | Bot settings | ✅ Yes |
| `prompts.py` | Bot personality | ✅ Yes |
| `requirements.txt` | Dependencies | Usually same |

## Key Commands

### Working with botfarm User

```bash
# Switch to botfarm user
sudo -u botfarm bash

# Check current user
whoami

# Exit botfarm user
exit
```

### Virtual Environment

```bash
# Activate venv
source /opt/bot-farm/venv/bin/activate

# Deactivate venv
deactivate

# Verify activation (should show venv in prompt)
(venv) botfarm@hostname:/opt/bot-farm$
```

### Git Operations

```bash
# Clone repo (first time)
git clone https://github.com/yourusername/my-bot-army.git /opt/bot-farm

# Or initialize in existing directory
cd /opt/bot-farm
git init
git remote add origin https://github.com/yourusername/my-bot-army.git
git pull origin main

# Update from remote
git pull origin main

# Add changes
git add .
git commit -m "Description of changes"
git push origin main

# Check status
git status

# View changes
git diff
```

### Running Bots

```bash
# Run manually (for testing)
cd /opt/bot-farm/bots/keystone-landscaping
source ../../venv/bin/activate
python app.py

# Run as service (production)
sudo systemctl start bot-keystone
sudo systemctl stop bot-keystone
sudo systemctl restart bot-keystone
sudo systemctl status bot-keystone

# View logs
sudo journalctl -u bot-keystone -f
```

### Testing

```bash
# Health check
curl http://localhost:5000/health

# Test chat endpoint
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Check port usage
sudo ss -tlnp | grep :5000

# Test from another computer (replace IP)
curl http://192.168.1.100:5000/health
```

### Maintenance

```bash
# Update Python packages
source venv/bin/activate
pip install --upgrade -r bots/keystone-landscaping/requirements.txt

# Check disk space
df -h

# Check memory usage
free -h

# Monitor bot process
top -u botfarm
```

## Port Assignments

| Bot | Port | Service Name |
|-----|------|--------------|
| Keystone Landscaping | 5000 | bot-keystone |
| Future Bot 2 | 5001 | bot-future-2 |
| Future Bot 3 | 5002 | bot-future-3 |
| ... | ... | ... |

## API Endpoints

### For Each Bot

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Welcome message |
| `/health` | GET | Health check |
| `/widget.js` | GET | Serve widget JavaScript |
| `/api/chat` | POST | Send message to bot |

### Chat API Request Format

```json
POST /api/chat
Content-Type: application/json

{
  "message": "User message here",
  "conversation_history": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

### Chat API Response Format

```json
{
  "response": "Bot response here",
  "status": "success"
}
```

## Widget Embedding

### Basic Embed

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

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiUrl` | string | required | Bot API endpoint |
| `botId` | string | required | Bot identifier |
| `position` | string | `'bottom-right'` | Widget position |
| `primaryColor` | string | `'#2563eb'` | Theme color |
| `title` | string | `'Chat with us'` | Chat window title |

## Environment Variables

### Required

```bash
ANTHROPIC_API_KEY=sk-ant-...    # Your Anthropic API key
```

### Optional

```bash
DEBUG=False                      # Enable Flask debug mode
```

## Security Notes

### Files to NEVER Commit

- `.env` - Contains API keys
- `venv/` - Virtual environment (large, machine-specific)
- `__pycache__/` - Python cache files
- `*.log` - Log files
- Any file with secrets or credentials

### Permissions

```bash
# .env should be readable only by botfarm
chmod 600 /opt/bot-farm/.env

# Project directory owned by botfarm
chown -R botfarm:botfarm /opt/bot-farm
```

## Adding a New Bot

### Steps

1. **Create bot directory:**
   ```bash
   mkdir -p /opt/bot-farm/bots/new-bot-name
   ```

2. **Copy template files from keystone-landscaping:**
   ```bash
   cp bots/keystone-landscaping/*.py bots/new-bot-name/
   cp bots/keystone-landscaping/requirements.txt bots/new-bot-name/
   ```

3. **Customize files:**
   - `config.py` - Change PORT and BOT_ID
   - `prompts.py` - Write new system prompt
   - `app.py` - Update if needed

4. **Install dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r bots/new-bot-name/requirements.txt
   ```

5. **Create systemd service:**
   ```bash
   sudo nano /etc/systemd/system/bot-new-name.service
   # Modify from bot-keystone.service template
   ```

6. **Enable and start:**
   ```bash
   sudo systemctl enable bot-new-name
   sudo systemctl start bot-new-name
   ```

## Troubleshooting Quick Reference

| Problem | Command to Check | Likely Fix |
|---------|------------------|------------|
| Bot won't start | `sudo systemctl status bot-keystone` | Check logs with journalctl |
| Port in use | `sudo ss -tlnp \| grep :5000` | Kill process or change port |
| API key not working | `cat /opt/bot-farm/.env` | Verify key is correct |
| Permission denied | `ls -la /opt/bot-farm/` | Fix ownership with chown |
| Widget not loading | Browser console | Check CORS settings |
| Import errors | `source venv/bin/activate` | Reinstall requirements.txt |

## Useful File Locations

| What | Location |
|------|----------|
| Bot logs | `sudo journalctl -u bot-keystone` |
| nginx config | `/etc/nginx/sites-available/bot-farm` |
| systemd service | `/etc/systemd/system/bot-keystone.service` |
| SSH config | `/etc/ssh/sshd_config` |
| Firewall rules | `sudo ufw status` |

## Resources

- **Flask**: https://flask.palletsprojects.com/
- **Anthropic API**: https://docs.anthropic.com/
- **Claude Code**: https://docs.claude.com/en/docs/claude-code
- **Python venv**: https://docs.python.org/3/library/venv.html
- **systemd**: https://www.freedesktop.org/software/systemd/man/
- **nginx**: https://nginx.org/en/docs/

---

**Quick Start Reminder:**

```bash
# 1. SSH into server
ssh your-user@server-ip

# 2. Switch to botfarm
sudo -u botfarm bash

# 3. Navigate to project
cd /opt/bot-farm

# 4. Activate venv
source venv/bin/activate

# 5. Work on your bots!
```

---

**Next Steps:** See [CLAUDE_CODE_PROMPT.md](./CLAUDE_CODE_PROMPT.md) to build the project with Claude Code.
