# 🚀 Getting Started - Visual Guide

Welcome to **My Bot Army**! This visual guide will get you from zero to deployed in the fastest way possible.

## 🎯 What You're Building

```
┌─────────────────────────────────────────────────┐
│  Client Websites (Any Website)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Website1 │  │ Website2 │  │ Website3 │      │
│  │   💬     │  │   💬     │  │   💬     │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┘
        │             │             │
        │  Widget JS  │             │
        └─────────────┼─────────────┘
                      ▼
        ┌─────────────────────────────┐
        │  Your Debian Server         │
        │  /opt/bot-farm/             │
        │                             │
        │  ┌─────────────────────┐   │
        │  │ Bot 1: Keystone     │◄──┼── Port 5000
        │  │ (Landscaping)       │   │
        │  └─────────────────────┘   │
        │                             │
        │  ┌─────────────────────┐   │
        │  │ Bot 2: Client X     │◄──┼── Port 5001
        │  └─────────────────────┘   │
        │                             │
        │  ┌─────────────────────┐   │
        │  │ Bot 3: Client Y     │◄──┼── Port 5002
        │  └─────────────────────┘   │
        └──────────────┬──────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Anthropic Claude API        │
        │  (claude-sonnet-4.5)         │
        └──────────────────────────────┘
```

## 📋 Prerequisites Checklist

Before you start, make sure you have:

```
Hardware:
□ Debian 12 server (or Ubuntu 22.04+)
□ At least 1GB RAM (2GB recommended)
□ Static IP (LAN is fine for now)

Access:
□ SSH access to server
□ Sudo privileges on server

Accounts:
□ GitHub account
□ Anthropic account with API key

Software on Server:
□ Python 3.11+
□ git
□ pip
```

## 🗺️ The Journey (Choose Your Path)

### Path A: Speed Run (10 minutes) 🏃‍♂️
```
1. Read QUICKSTART.md
2. Follow commands
3. Done!
```
**Best for:** Experienced developers who want results fast

---

### Path B: Proper Setup (2-4 hours) 👨‍💻
```
1. Read README.md          (10 min)
2. Setup server (SETUP.md) (30 min)
3. Build with Claude Code  (1 hour)
4. Deploy (DEPLOYMENT.md)  (1 hour)
5. Test & polish           (30 min)
```
**Best for:** First-time deployment, learning the system

---

### Path C: Just the Essentials (1 hour) ⚡
```
1. Skim README.md
2. Jump to QUICKSTART.md
3. Use Claude Code
4. Deploy
```
**Best for:** Balance of speed and understanding

## 🎬 Step-by-Step Quickstart

### Stage 1: Setup (15 min)

```bash
# 1. SSH into your Debian server
ssh youruser@192.168.x.x

# 2. Become root or use sudo
sudo -i

# 3. Run the setup script
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git

# 4. Create the bot user
useradd -r -m -s /bin/bash botfarm
mkdir -p /opt/bot-farm
chown -R botfarm:botfarm /opt/bot-farm

# Done with Stage 1! ✅
```

---

### Stage 2: GitHub Setup (10 min)

```bash
# On your main computer:

# 1. Create repo on GitHub.com
#    Name: my-bot-army
#    Private: Yes

# 2. Download the documentation files from Claude
#    (You already have them!)

# 3. Upload to GitHub
cd ~/my-bot-army
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/my-bot-army.git
git push -u origin main

# Done with Stage 2! ✅
```

---

### Stage 3: Build with Claude Code (30 min)

```
# In Claude Code:

You: "Read CLAUDE_CODE_PROMPT.md and build all the files 
     exactly as specified. Create the shared components 
     and the Keystone Landscaping bot."

Claude Code: [Builds all the Python, JavaScript, and config files]

You: [Review the code]

You: "Looks good, commit it"

Claude Code: [Commits to GitHub]

# Done with Stage 3! ✅
```

---

### Stage 4: Deploy (20 min)

```bash
# Back on your Debian server

# 1. Switch to botfarm user
sudo -u botfarm bash

# 2. Clone the repo
cd /opt/bot-farm
git clone https://github.com/yourusername/my-bot-army.git .

# 3. Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r bots/keystone-landscaping/requirements.txt

# 4. Add your API key
nano .env
# Add: ANTHROPIC_API_KEY=sk-ant-your-key-here
# Save: Ctrl+X, Y, Enter
chmod 600 .env

# 5. Test it
cd bots/keystone-landscaping
python app.py

# You should see: * Running on http://0.0.0.0:5000

# Done with Stage 4! ✅
```

---

### Stage 5: Production (15 min)

```bash
# Exit the test (Ctrl+C)
# Exit botfarm user
exit

# Create the service
sudo nano /etc/systemd/system/bot-keystone.service

# Paste this:
```

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

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable bot-keystone
sudo systemctl start bot-keystone
sudo systemctl status bot-keystone

# Open firewall
sudo ufw allow 5000/tcp
sudo ufw enable

# Done with Stage 5! ✅
```

---

### Stage 6: Test (10 min)

```bash
# Get your server IP
hostname -I
# Note the IP (e.g., 192.168.1.100)

# From another computer:
curl http://192.168.1.100:5000/health

# Should return:
# {"status":"healthy","bot":"keystone-landscaping"}

# Create test.html on your main computer:
```

```html
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Bot Test</h1>
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

```
Open in browser → Click chat bubble → Chat!

# Done with Stage 6! ✅
```

---

## 🎊 You're Live!

Your bot army is now operational! Here's what you have:

✅ **Scalable platform** - Add unlimited bots  
✅ **Production-ready** - Runs as a service  
✅ **Easy to embed** - Simple JavaScript snippet  
✅ **Claude-powered** - Latest AI technology  
✅ **Self-hosted** - You control everything  

## 📊 Project Status Dashboard

After deployment, check your status:

```bash
# Service status
sudo systemctl status bot-keystone
# Should show: ● bot-keystone.service - Keystone Hardscapes Bot
#              Active: active (running)

# Port check
sudo ss -tlnp | grep :5000
# Should show: LISTEN  0  128  0.0.0.0:5000

# Logs
sudo journalctl -u bot-keystone -n 20
# Should show: No errors, successful starts

# Resource usage
htop -u botfarm
# Should show: Minimal CPU/RAM usage
```

## 🔄 Daily Operations

### Start of Day
```bash
# Check bot is running
sudo systemctl status bot-keystone

# Check logs for errors
sudo journalctl -u bot-keystone --since "1 hour ago"
```

### Deploy Update
```bash
# 1. Push code to GitHub (from main computer)
git push origin main

# 2. Pull on server
sudo -u botfarm bash
cd /opt/bot-farm
git pull origin main
exit

# 3. Restart service
sudo systemctl restart bot-keystone
```

### Add New Client Bot
```bash
# See PROJECT_STRUCTURE.md → "Adding a New Bot"
# Copy keystone bot → Customize → Deploy on port 5001
```

## 🆘 Emergency Troubleshooting

```bash
# Bot won't start?
sudo journalctl -u bot-keystone -n 50

# Port conflict?
sudo ss -tlnp | grep :5000
sudo kill -9 [PID]

# Permission error?
sudo chown -R botfarm:botfarm /opt/bot-farm

# API key issue?
sudo -u botfarm cat /opt/bot-farm/.env

# Complete restart?
sudo systemctl restart bot-keystone
```

## 📚 Documentation Map

```
START HERE → INDEX.md
              │
              ├─ Quick? → QUICKSTART.md
              │
              ├─ Detailed? → README.md → SETUP.md → DEPLOYMENT.md
              │
              ├─ Building code? → CLAUDE_CODE_PROMPT.md
              │
              └─ Reference? → PROJECT_STRUCTURE.md
```

## 🎯 Success Metrics

You've succeeded when:

1. ✅ `systemctl status bot-keystone` shows "active"
2. ✅ Can chat with bot on test page
3. ✅ Widget works on client website
4. ✅ Bot gives helpful responses
5. ✅ Service restarts after reboot
6. ✅ Can add second bot easily
7. ✅ Your buddy is impressed! 🎉

## 🚀 Next Level

Once you're comfortable:

- **Add HTTPS** with Let's Encrypt
- **Get a domain** and point it to your server
- **Use nginx** for cleaner URLs
- **Add monitoring** with uptime checks
- **Scale up** - Deploy more bots!
- **Go public** - Offer bot-as-a-service

## 💪 You've Got This!

Remember:
- 📖 All docs are here when you need them
- 🤖 Claude Code builds the code for you
- 🏃‍♂️ QUICKSTART.md if you're in a hurry
- 📘 DEPLOYMENT.md for step-by-step
- 🆘 Troubleshooting in every doc

**Ready to start? Pick your path above and go! 🚀**

---

Questions? Check:
1. INDEX.md (navigation)
2. README.md (overview)
3. PROJECT_STRUCTURE.md (reference)
4. Specific guide for your task

**Good luck building your bot army!** 🤖⚔️🤖
