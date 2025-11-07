# Quick Start Guide 🚀

Get your bot army up and running in under 10 minutes!

## Prerequisites Checklist

- [ ] Debian 12 server (or Ubuntu 22.04+)
- [ ] SSH access to server
- [ ] Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))
- [ ] Git installed on server

## Step 1: Initial Server Setup (5 minutes)

SSH into your server and run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git

# Create botfarm user
sudo useradd -r -m -s /bin/bash botfarm

# Create project directory
sudo mkdir -p /opt/bot-farm
sudo chown -R botfarm:botfarm /opt/bot-farm
```

## Step 2: Clone and Setup Project (2 minutes)

```bash
# Switch to botfarm user
sudo -u botfarm bash

# Navigate to project directory
cd /opt/bot-farm

# Clone repository (replace with your GitHub URL)
git clone https://github.com/yourusername/my-bot-army.git .

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (will be created by Claude Code)
pip install -r bots/keystone-landscaping/requirements.txt
```

## Step 3: Configure Environment (1 minute)

```bash
# Create .env file
cp .env.example .env
nano .env
```

Add your API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

Save and exit: `Ctrl+X`, `Y`, `Enter`

Secure it:
```bash
chmod 600 .env
```

## Step 4: Test the Bot (1 minute)

```bash
# Make sure you're in the right directory and venv is activated
cd /opt/bot-farm/bots/keystone-landscaping
source ../../venv/bin/activate

# Run the bot
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

## Step 5: Test from Another Computer (1 minute)

Open another terminal on your main computer:

```bash
# Replace 192.168.1.100 with your server's IP
curl http://192.168.1.100:5000/health
```

You should get:
```json
{"status":"healthy","bot":"keystone-landscaping"}
```

**Test the chat:**
```bash
curl -X POST http://192.168.1.100:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services do you offer?"}'
```

## Step 6: Test the Widget

Create a test HTML file on your main computer:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Bot Test</title>
</head>
<body>
    <h1>Test Page for My Bot Army</h1>
    
    <script src="http://192.168.1.100:5000/widget.js"></script>
    <script>
        BotWidget.init({
            apiUrl: 'http://192.168.1.100:5000',
            botId: 'keystone-landscaping',
            position: 'bottom-right',
            primaryColor: '#2563eb',
            title: 'Chat with Keystone'
        });
    </script>
</body>
</html>
```

Open in your browser and click the chat bubble!

## Production Deployment (Optional)

### Set up as a systemd service:

```bash
# Exit botfarm user first
exit

# Create service file
sudo nano /etc/systemd/system/bot-keystone.service
```

Paste this:
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
sudo systemctl daemon-reload
sudo systemctl enable bot-keystone
sudo systemctl start bot-keystone
sudo systemctl status bot-keystone
```

## Firewall Setup

```bash
# Allow SSH (if not already)
sudo ufw allow 22/tcp

# Allow bot port
sudo ufw allow 5000/tcp

# Enable firewall
sudo ufw enable
```

## Common Issues

### "ensurepip not available"
```bash
exit  # Exit botfarm
sudo apt install python3-venv
sudo -u botfarm bash
cd /opt/bot-farm
python3 -m venv venv
```

### "Permission denied"
```bash
sudo chown -R botfarm:botfarm /opt/bot-farm
```

### "Port already in use"
```bash
sudo ss -tlnp | grep :5000
# Kill the process or change the port in config.py
```

### Widget not loading
- Check browser console for errors
- Verify CORS is enabled in app.py
- Make sure the bot is running

## Next Steps

1. ✅ **Bot is running** - Check!
2. 📝 **Customize** - Edit `prompts.py` to customize bot personality
3. 🎨 **Style widget** - Modify colors and position
4. 🔒 **Secure** - Set up HTTPS with Let's Encrypt
5. 🌐 **Domain** - Point a domain to your server
6. 🤖 **Add more bots** - Scale your army!

## Useful Commands

```bash
# View logs
sudo journalctl -u bot-keystone -f

# Restart bot
sudo systemctl restart bot-keystone

# Stop bot
sudo systemctl stop bot-keystone

# Update code
sudo -u botfarm bash
cd /opt/bot-farm
git pull origin main
exit
sudo systemctl restart bot-keystone
```

## Getting Help

- **Full documentation**: See [README.md](./README.md)
- **Detailed setup**: See [SETUP.md](./SETUP.md)
- **Project structure**: See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
- **Build with Claude Code**: See [CLAUDE_CODE_PROMPT.md](./CLAUDE_CODE_PROMPT.md)

---

**That's it!** 🎉 Your bot army is ready to serve.

**Time to deploy:** ~10 minutes  
**Coffee breaks:** 0 (it's that fast!)
