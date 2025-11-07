# Deployment Workflow

Complete workflow from documentation to production deployment.

## Overview

This document outlines the complete workflow for deploying the My Bot Army platform, from creating the GitHub repository to running in production.

## Phase 1: Repository Setup

### Step 1: Create GitHub Repository

1. Go to GitHub.com
2. Click "New repository"
3. Repository name: `my-bot-army`
4. Description: "Scalable multi-bot AI assistant platform powered by Claude"
5. Make it **Private** (contains API configuration)
6. **Do NOT** initialize with README (we already have one)
7. Click "Create repository"

### Step 2: Upload Initial Documentation

You have these documentation files ready:
- `README.md` - Project overview
- `SETUP.md` - Server setup guide
- `CLAUDE_CODE_PROMPT.md` - Build instructions
- `PROJECT_STRUCTURE.md` - Structure reference
- `QUICKSTART.md` - Quick start guide
- `.env.example` - Environment template
- `.gitignore` - Git ignore rules
- `LICENSE` - MIT license

**From your Windows/Ubuntu machine:**

```bash
# Create a local directory
mkdir ~/my-bot-army
cd ~/my-bot-army

# Copy all the documentation files into this directory
# (Download from Claude's outputs directory)

# Initialize git
git init
git add .
git commit -m "Initial documentation"

# Connect to GitHub (replace with your URL)
git remote add origin https://github.com/yourusername/my-bot-army.git
git branch -M main
git push -u origin main
```

## Phase 2: Code Generation with Claude Code

### Step 1: Give Claude Code the Build Prompt

In Claude Code, share the repository and say:

```
I need you to build the My Bot Army platform. Please read CLAUDE_CODE_PROMPT.md 
in this repository and build all the code files exactly as specified.

The project structure should match what's documented in PROJECT_STRUCTURE.md.

Start by creating the shared components, then build the Keystone Landscaping bot.
```

### Step 2: Review Generated Code

Claude Code will create:
- `shared/__init__.py`
- `shared/claude_client.py`
- `shared/widget/bot-widget.js`
- `shared/widget/bot-widget.css` (if applicable)
- `bots/keystone-landscaping/app.py`
- `bots/keystone-landscaping/config.py`
- `bots/keystone-landscaping/prompts.py`
- `bots/keystone-landscaping/requirements.txt`
- `nginx/bot-farm.conf.example`

### Step 3: Test Locally (Optional)

If you have Python on your main machine:

```bash
cd ~/my-bot-army
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r bots/keystone-landscaping/requirements.txt

# Create .env
cp .env.example .env
# Edit .env and add your API key

# Run
cd bots/keystone-landscaping
python app.py
```

Test at http://localhost:5000

### Step 4: Commit to GitHub

```bash
git add .
git commit -m "Add bot implementation"
git push origin main
```

## Phase 3: Server Deployment

### Step 1: SSH into Server

```bash
ssh your-ssh-user@your-server-ip
```

### Step 2: Prepare Server (if not done)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install packages
sudo apt install -y python3 python3-pip python3-venv git

# Create botfarm user
sudo useradd -r -m -s /bin/bash botfarm

# Create directory
sudo mkdir -p /opt/bot-farm
sudo chown -R botfarm:botfarm /opt/bot-farm
```

### Step 3: Deploy Code

```bash
# Switch to botfarm
sudo -u botfarm bash

# Clone repository
cd /opt/bot-farm
git clone https://github.com/yourusername/my-bot-army.git .

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r bots/keystone-landscaping/requirements.txt
```

### Step 4: Configure Environment

```bash
# Create .env
nano .env
```

Add:
```
ANTHROPIC_API_KEY=your-actual-api-key-here
```

Save: `Ctrl+X`, `Y`, `Enter`

```bash
chmod 600 .env
```

### Step 5: Test Manually

```bash
cd /opt/bot-farm/bots/keystone-landscaping
source ../../venv/bin/activate
python app.py
```

From another terminal:
```bash
curl http://localhost:5000/health
```

Should return: `{"status":"healthy","bot":"keystone-landscaping"}`

Stop with `Ctrl+C`

## Phase 4: Production Setup

### Step 1: Create systemd Service

Exit botfarm user first:
```bash
exit
```

Create service file:
```bash
sudo nano /etc/systemd/system/bot-keystone.service
```

Paste:
```ini
[Unit]
Description=Keystone Hardscapes AI Assistant
After=network.target

[Service]
Type=simple
User=botfarm
Group=botfarm
WorkingDirectory=/opt/bot-farm/bots/keystone-landscaping
Environment="PATH=/opt/bot-farm/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/bot-farm/venv/bin/python app.py
Restart=always
RestartSec=3

NoNewPrivileges=true
PrivateTmp=true

StandardOutput=journal
StandardError=journal
SyslogIdentifier=bot-keystone

[Install]
WantedBy=multi-user.target
```

### Step 2: Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable bot-keystone
sudo systemctl start bot-keystone
sudo systemctl status bot-keystone
```

Should show "active (running)"

### Step 3: Configure Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 5000/tcp
sudo ufw enable
```

### Step 4: Get Server IP

```bash
hostname -I
```

Note your IP address (e.g., 192.168.1.100)

## Phase 5: Widget Testing

### On Your Main Computer

Create `test.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Army Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        h1 { color: #2563eb; }
        .info {
            background: #f0f9ff;
            border: 1px solid #2563eb;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>🤖 My Bot Army - Test Page</h1>
    
    <div class="info">
        <h2>Keystone Hardscapes Assistant</h2>
        <p>Click the blue chat bubble in the bottom-right corner to start chatting!</p>
        <p><strong>Try asking:</strong></p>
        <ul>
            <li>"What services do you offer?"</li>
            <li>"Do you service Calgary?"</li>
            <li>"How much does a patio cost?"</li>
            <li>"Tell me about your warranty"</li>
        </ul>
    </div>
    
    <!-- Replace 192.168.1.100 with your server's IP -->
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

Open in your browser and test the chat!

## Phase 6: Embed on Client Website

### For Keystone Hardscapes Site

Add before `</body>` tag:

```html
<!-- Keystone Hardscapes Chat Assistant -->
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

### For Other Client Sites

Same approach, just paste the snippet!

## Monitoring & Maintenance

### View Logs

```bash
# Real-time logs
sudo journalctl -u bot-keystone -f

# Last 100 lines
sudo journalctl -u bot-keystone -n 100

# Errors only
sudo journalctl -u bot-keystone -p err
```

### Restart Bot

```bash
sudo systemctl restart bot-keystone
```

### Update Code

```bash
sudo -u botfarm bash
cd /opt/bot-farm
git pull origin main
exit
sudo systemctl restart bot-keystone
```

### Check Status

```bash
# Service status
sudo systemctl status bot-keystone

# Port status
sudo ss -tlnp | grep :5000

# Resource usage
top -u botfarm
```

## Scaling: Adding More Bots

### Step 1: Create New Bot Directory

```bash
sudo -u botfarm bash
cd /opt/bot-farm/bots
mkdir new-client-bot
```

### Step 2: Copy Template

```bash
cp -r keystone-landscaping/* new-client-bot/
```

### Step 3: Customize

Edit these files in `new-client-bot/`:
- `config.py` - Change `PORT = 5001` and `BOT_ID`
- `prompts.py` - New system prompt for client
- `app.py` - Update if needed

### Step 4: Create New Service

```bash
exit  # Exit botfarm
sudo cp /etc/systemd/system/bot-keystone.service \
       /etc/systemd/system/bot-newclient.service
       
sudo nano /etc/systemd/system/bot-newclient.service
# Update Description and WorkingDirectory
```

### Step 5: Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable bot-newclient
sudo systemctl start bot-newclient
sudo ufw allow 5001/tcp
```

## Troubleshooting Checklist

- [ ] Server can reach Anthropic API
- [ ] API key is correct in .env
- [ ] Port 5000 is open in firewall
- [ ] Service is running: `systemctl status bot-keystone`
- [ ] No errors in logs: `journalctl -u bot-keystone`
- [ ] Can curl health endpoint from server
- [ ] Can curl from another computer
- [ ] Widget loads in browser (check console)
- [ ] CORS is configured correctly

## Success Criteria

✅ Bot service starts without errors  
✅ Health endpoint returns 200 OK  
✅ Chat endpoint responds with Claude messages  
✅ Widget loads on test page  
✅ Can send and receive messages  
✅ Service restarts automatically if it crashes  
✅ Service starts on boot  

## Next Steps

1. **Domain Setup** - Point a domain to your server
2. **HTTPS** - Set up Let's Encrypt SSL certificate
3. **nginx** - Use reverse proxy for cleaner URLs
4. **Monitoring** - Set up uptime monitoring
5. **Backups** - Automate backups of configuration
6. **Analytics** - Track usage and conversations
7. **Scale** - Add more bots for other clients!

---

**Deployment complete!** 🚀 Your bot army is live and ready to chat.
