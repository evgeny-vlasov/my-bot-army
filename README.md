# My Bot Army 🤖

A scalable multi-bot platform for deploying custom AI assistants powered by Claude. Each bot can be customized with its own personality, knowledge base, and embedded on any website via a simple JavaScript snippet.

## Overview

My Bot Army is designed to host multiple AI chatbot instances, each serving different clients or purposes. The first bot in the army is for **Keystone Hardscapes**, a landscaping contractor in Alberta, Canada.

## Architecture

```
/opt/bot-farm/
├── shared/                      # Shared utilities across all bots
│   ├── claude_client.py        # Reusable Claude API wrapper
│   ├── widget/                 # Embeddable chat widget
│   │   ├── bot-widget.js      # JavaScript widget for client websites
│   │   └── bot-widget.css     # Widget styling
│   └── __init__.py
├── bots/                       # Individual bot instances
│   ├── keystone-landscaping/   # First bot - landscaping assistant
│   │   ├── app.py             # Flask application
│   │   ├── config.py          # Bot-specific configuration
│   │   ├── prompts.py         # System prompts and personality
│   │   └── requirements.txt   # Python dependencies
│   └── [future-bots]/         # Additional bots go here
├── nginx/                      # Reverse proxy configs (optional)
├── .env                        # API keys and secrets (NOT in git)
└── venv/                       # Python virtual environment
```

## Tech Stack

- **Backend**: Python 3.11 + Flask
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **Frontend Widget**: Vanilla JavaScript
- **Server**: Debian 12
- **Process Manager**: systemd (for production)
- **Reverse Proxy**: nginx (optional, for multiple bots)

## Features

### Current (v1.0 - Proof of Concept)
- ✅ Single bot deployment (Keystone Hardscapes)
- ✅ RESTful API endpoint for chat
- ✅ Embeddable JavaScript widget
- ✅ Conversation context management
- ✅ Custom system prompts per bot
- ✅ CORS support for cross-origin requests

### Planned (Future)
- 🔄 Multi-bot routing via nginx
- 🔄 Bot dashboard for management
- 🔄 Usage analytics per bot
- 🔄 Rate limiting per client
- 🔄 Database for conversation history
- 🔄 Webhook support for integrations

## Quick Start

### Prerequisites
- Debian 12 server (or Ubuntu/similar)
- Python 3.11+
- Anthropic API key
- Static IP or domain (for production)

### Installation

See [SETUP.md](./SETUP.md) for detailed server setup instructions.

Quick version:
```bash
# Clone the repo
git clone https://github.com/yourusername/my-bot-army.git /opt/bot-farm
cd /opt/bot-farm

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r bots/keystone-landscaping/requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# Run the bot
cd bots/keystone-landscaping
python app.py
```

Bot will be available at: `http://your-server-ip:5000`

## Embedding the Chat Widget

To add the chatbot to any website, add this snippet before `</body>`:

```html
<!-- Keystone Hardscapes Chat Widget -->
<script src="http://your-server-ip:5000/widget.js"></script>
<script>
  BotWidget.init({
    apiUrl: 'http://your-server-ip:5000',
    botId: 'keystone-landscaping',
    position: 'bottom-right',
    primaryColor: '#2563eb',
    title: 'Chat with Keystone'
  });
</script>
```

## Adding New Bots

1. Create a new directory under `bots/`:
   ```bash
   mkdir bots/new-client-name
   ```

2. Copy the template structure from `keystone-landscaping/`

3. Customize:
   - `prompts.py` - Define the bot's personality and knowledge
   - `config.py` - Set bot-specific settings
   - `app.py` - Adjust endpoints if needed

4. Run on a different port:
   ```python
   app.run(host='0.0.0.0', port=5001)
   ```

## Development

### Project Development with Claude Code

This project is designed to be built with [Claude Code](https://docs.claude.com/en/docs/claude-code). See [CLAUDE_CODE_PROMPT.md](./CLAUDE_CODE_PROMPT.md) for the detailed build instructions.

### Testing Locally

```bash
# Activate venv
source venv/bin/activate

# Run the bot
cd bots/keystone-landscaping
python app.py

# Test the API
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services do you offer?"}'
```

## Production Deployment

### Running as a Service (systemd)

Create `/etc/systemd/system/bot-keystone.service`:

```ini
[Unit]
Description=Keystone Hardscapes Bot
After=network.target

[Service]
Type=simple
User=botfarm
WorkingDirectory=/opt/bot-farm/bots/keystone-landscaping
Environment="PATH=/opt/bot-farm/venv/bin"
ExecStart=/opt/bot-farm/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable bot-keystone
sudo systemctl start bot-keystone
sudo systemctl status bot-keystone
```

### Using nginx (Multiple Bots)

See `nginx/` directory for configuration examples to route multiple bots through port 80/443.

## Security Considerations

- 🔒 Never commit `.env` file to git
- 🔒 Use HTTPS in production (Let's Encrypt)
- 🔒 Implement rate limiting for public endpoints
- 🔒 Run bots as non-privileged `botfarm` user
- 🔒 Keep API keys secure and rotated
- 🔒 Validate and sanitize all user inputs

## Troubleshooting

### Bot won't start
```bash
# Check logs
journalctl -u bot-keystone -f

# Check if port is in use
sudo ss -tlnp | grep :5000

# Verify API key
cd /opt/bot-farm
source venv/bin/activate
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key loaded!' if os.getenv('ANTHROPIC_API_KEY') else 'API Key missing!')"
```

### Widget not loading
- Check CORS settings in `app.py`
- Verify bot URL is accessible from client's website
- Check browser console for errors
- Ensure HTTP/HTTPS match (no mixed content)

## Contributing

This is a personal project, but feel free to fork and adapt for your own use!

## License

MIT License - See [LICENSE](./LICENSE) for details

## Contact

For questions about Keystone Hardscapes bot specifically, visit: https://andrew-two.vercel.app/

---

**Built with Claude Code** 🤖 | **Powered by Anthropic Claude API** ⚡
