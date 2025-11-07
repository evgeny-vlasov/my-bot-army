# Server Setup Guide

Complete guide for setting up the My Bot Army platform on a Debian 12 server.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Initial Server Setup](#initial-server-setup)
3. [User Configuration](#user-configuration)
4. [Python Environment](#python-environment)
5. [Project Deployment](#project-deployment)
6. [Network Configuration](#network-configuration)
7. [Production Setup](#production-setup)

## System Requirements

### Minimum Specs
- **OS**: Debian 12 (or Ubuntu 22.04+)
- **RAM**: 1GB minimum, 2GB recommended
- **Disk**: 10GB available space
- **Network**: Static IP (LAN or public)
- **Python**: 3.11 or higher

### Required Software
- Python 3.11+
- pip
- venv
- git
- systemd (included in Debian 12)
- nginx (optional, for reverse proxy)

## Initial Server Setup

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Required Packages

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    nginx \
    ufw
```

### 3. Verify Python Version

```bash
python3 --version
# Should show Python 3.11.x or higher
```

## User Configuration

### 1. Create Service User

Create a dedicated user for running the bot services:

```bash
sudo useradd -r -m -s /bin/bash botfarm
```

**Flags explained:**
- `-r`: System account (no password login by default)
- `-m`: Create home directory
- `-s /bin/bash`: Set bash as shell

### 2. Create Project Directory

```bash
sudo mkdir -p /opt/bot-farm
sudo chown -R botfarm:botfarm /opt/bot-farm
```

### 3. Grant Your User Access

Add your SSH user to botfarm group (optional):

```bash
sudo usermod -aG botfarm your-ssh-username
```

Or work as botfarm user when needed:

```bash
sudo -u botfarm bash
```

## Python Environment

### 1. Switch to botfarm User

```bash
sudo -u botfarm bash
cd /opt/bot-farm
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

If you get an error about `ensurepip`, install venv:

```bash
exit  # Exit botfarm user first
sudo apt install python3.11-venv
sudo -u botfarm bash
cd /opt/bot-farm
python3 -m venv venv
```

### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt:
```
(venv) botfarm@hostname:/opt/bot-farm$
```

### 4. Upgrade pip

```bash
pip install --upgrade pip
```

## Project Deployment

### 1. Clone Repository

```bash
# As botfarm user
cd /opt/bot-farm
git clone https://github.com/yourusername/my-bot-army.git .
```

**Or** if directory already exists:

```bash
# As botfarm user
cd /opt/bot-farm
git init
git remote add origin https://github.com/yourusername/my-bot-army.git
git pull origin main
```

### 2. Install Dependencies

```bash
# Make sure venv is activated
source venv/bin/activate

# Install for first bot
pip install -r bots/keystone-landscaping/requirements.txt
```

### 3. Configure Environment Variables

```bash
# Create .env file
nano /opt/bot-farm/.env
```

Add your configuration:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

Save and exit: `Ctrl+X`, `Y`, `Enter`

**Secure the file:**
```bash
chmod 600 /opt/bot-farm/.env
```

### 4. Test the Bot

```bash
cd /opt/bot-farm/bots/keystone-landscaping
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

**Test from another terminal:**
```bash
curl http://localhost:5000/health
```

Stop the test server: `Ctrl+C`

## Network Configuration

### 1. Find Your Server IP

```bash
hostname -I
# Or
ip addr show
```

Look for your LAN IP (e.g., `192.168.1.100`)

### 2. Configure Firewall (UFW)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow bot port
sudo ufw allow 5000/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 3. Test from Another Computer

From your Windows/Ubuntu machine:

```bash
curl http://192.168.1.100:5000/health
```

Or open in browser:
```
http://192.168.1.100:5000/
```

## Production Setup

### 1. Create systemd Service

Create service file:

```bash
sudo nano /etc/systemd/system/bot-keystone.service
```

Paste this configuration:

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

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bot-keystone

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable bot-keystone

# Start service
sudo systemctl start bot-keystone

# Check status
sudo systemctl status bot-keystone
```

### 3. View Logs

```bash
# Follow logs in real-time
sudo journalctl -u bot-keystone -f

# View last 100 lines
sudo journalctl -u bot-keystone -n 100

# View logs from today
sudo journalctl -u bot-keystone --since today
```

### 4. Manage Service

```bash
# Stop service
sudo systemctl stop bot-keystone

# Restart service
sudo systemctl restart bot-keystone

# Disable service (won't start on boot)
sudo systemctl disable bot-keystone
```

## nginx Reverse Proxy (Optional)

If you want to run multiple bots or use port 80/443:

### 1. Install nginx

```bash
sudo apt install nginx
```

### 2. Create Configuration

```bash
sudo nano /etc/nginx/sites-available/bot-farm
```

Paste:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or your IP

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

    # Add more bots here as /bot-name/
}
```

### 3. Enable Configuration

```bash
sudo ln -s /etc/nginx/sites-available/bot-farm /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### 4. Update Firewall

```bash
sudo ufw allow 'Nginx Full'
```

## SSH Configuration (Security)

### 1. Create SSH-only User

If you want a separate SSH user:

```bash
sudo useradd -m -s /bin/bash sshuser
sudo passwd sshuser
sudo usermod -aG sudo sshuser
```

### 2. Secure SSH

Edit SSH config:

```bash
sudo nano /etc/ssh/sshd_config
```

Recommended settings:
```
Port 22  # Or change to custom port
PermitRootLogin no
PasswordAuthentication yes  # Or use keys only
PubkeyAuthentication yes
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

## Maintenance

### Update Bot Code

```bash
sudo -u botfarm bash
cd /opt/bot-farm
source venv/bin/activate
git pull origin main
sudo systemctl restart bot-keystone
```

### Update Dependencies

```bash
sudo -u botfarm bash
cd /opt/bot-farm
source venv/bin/activate
pip install --upgrade -r bots/keystone-landscaping/requirements.txt
sudo systemctl restart bot-keystone
```

### Backup

```bash
# Backup project (excluding venv)
sudo tar -czf /backup/bot-farm-$(date +%Y%m%d).tar.gz \
    --exclude='/opt/bot-farm/venv' \
    /opt/bot-farm

# Backup .env separately (secure location)
sudo cp /opt/bot-farm/.env /backup/.env-$(date +%Y%m%d)
```

## Troubleshooting

### Bot Won't Start

```bash
# Check service status
sudo systemctl status bot-keystone

# Check logs
sudo journalctl -u bot-keystone -n 50

# Test manually
sudo -u botfarm bash
cd /opt/bot-farm/bots/keystone-landscaping
source /opt/bot-farm/venv/bin/activate
python app.py
```

### Permission Denied

```bash
# Fix ownership
sudo chown -R botfarm:botfarm /opt/bot-farm

# Fix .env permissions
sudo chmod 600 /opt/bot-farm/.env
```

### Port Already in Use

```bash
# Find what's using port 5000
sudo ss -tlnp | grep :5000

# Kill the process (if safe)
sudo kill -9 <PID>
```

### API Key Not Working

```bash
# Verify .env file exists
cat /opt/bot-farm/.env

# Test API key loading
sudo -u botfarm bash
cd /opt/bot-farm
source venv/bin/activate
python3 << EOF
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key loaded: {key[:10]}..." if key else "API Key NOT loaded!")
EOF
```

## Next Steps

- [ ] Deploy first bot (Keystone)
- [ ] Test chat widget on local website
- [ ] Set up HTTPS with Let's Encrypt
- [ ] Configure domain name
- [ ] Add monitoring (optional)
- [ ] Deploy additional bots

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [systemd Documentation](https://www.freedesktop.org/software/systemd/man/)
- [nginx Documentation](https://nginx.org/en/docs/)

---

**Setup complete!** 🎉 Your bot army is ready to deploy.
