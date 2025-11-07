# 📚 My Bot Army - Documentation Index

Welcome to your bot army! This guide will help you navigate all the documentation.

## 🎯 Start Here

**New to the project?**
1. Read [README.md](./README.md) for the big picture
2. Follow [QUICKSTART.md](./QUICKSTART.md) to get running in 10 minutes
3. Use [CLAUDE_CODE_PROMPT.md](./CLAUDE_CODE_PROMPT.md) to build the code

**Setting up your server?**
→ See [SETUP.md](./SETUP.md) for detailed server configuration

**Ready to deploy?**
→ Follow [DEPLOYMENT.md](./DEPLOYMENT.md) for the complete workflow

**Need quick reference?**
→ Check [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for commands and structure

## 📖 Documentation Files

| File | Purpose | When to Use |
|------|---------|-------------|
| **README.md** | Project overview and features | First read, reference |
| **QUICKSTART.md** | Get up and running fast | When you want to skip details |
| **SETUP.md** | Detailed server setup | Setting up Debian server |
| **DEPLOYMENT.md** | Complete deployment workflow | Step-by-step production deploy |
| **CLAUDE_CODE_PROMPT.md** | Instructions for Claude Code | Building the actual code |
| **PROJECT_STRUCTURE.md** | File structure and commands | Reference while working |
| **LICENSE** | MIT license terms | Legal reference |

## 🗂️ Configuration Files

| File | Purpose | Notes |
|------|---------|-------|
| **.env.example** | Environment template | Copy to .env and add API key |
| **.gitignore** | Git exclusions | Protects secrets from git |

## 🚀 Workflow Overview

```
1. Read Documentation
   ↓
2. Create GitHub Repo
   ↓
3. Upload Documentation Files
   ↓
4. Use Claude Code to Build
   (Follow CLAUDE_CODE_PROMPT.md)
   ↓
5. Push Code to GitHub
   ↓
6. Setup Debian Server
   (Follow SETUP.md)
   ↓
7. Deploy to Server
   (Follow DEPLOYMENT.md)
   ↓
8. Test & Launch
   ↓
9. Embed Widget on Websites
   ↓
10. Add More Bots!
```

## 🎓 Learning Path

### Phase 1: Understanding (30 minutes)
- [ ] Read README.md
- [ ] Skim PROJECT_STRUCTURE.md
- [ ] Review architecture diagram in README

### Phase 2: Server Prep (30 minutes)
- [ ] Follow SETUP.md
- [ ] Create botfarm user
- [ ] Install Python and dependencies
- [ ] Get Anthropic API key

### Phase 3: Build (1-2 hours)
- [ ] Create GitHub repository
- [ ] Upload documentation
- [ ] Use Claude Code with CLAUDE_CODE_PROMPT.md
- [ ] Review generated code
- [ ] Test locally (optional)
- [ ] Commit to GitHub

### Phase 4: Deploy (1 hour)
- [ ] Follow DEPLOYMENT.md
- [ ] Clone to server
- [ ] Configure .env
- [ ] Setup systemd service
- [ ] Test on LAN

### Phase 5: Widget Integration (30 minutes)
- [ ] Create test HTML page
- [ ] Test widget functionality
- [ ] Embed on client website
- [ ] Verify on production

**Total time: ~4 hours from zero to production**

## 🔧 Common Tasks

### Starting Fresh
1. SETUP.md → Server configuration
2. CLAUDE_CODE_PROMPT.md → Build code
3. DEPLOYMENT.md → Deploy to server

### Quick Deploy (server ready)
1. QUICKSTART.md → Fast deployment
2. Skip to testing section

### Adding New Bot
1. PROJECT_STRUCTURE.md → "Adding a New Bot" section
2. Copy keystone-landscaping bot
3. Customize prompts.py
4. Create new systemd service

### Troubleshooting
1. PROJECT_STRUCTURE.md → "Troubleshooting" section
2. DEPLOYMENT.md → "Troubleshooting Checklist"
3. Check logs with journalctl

### Updating Code
1. Push changes to GitHub
2. SSH to server
3. `git pull origin main`
4. `systemctl restart bot-keystone`

## 💡 Quick Tips

**For the impatient:**
→ Go straight to QUICKSTART.md

**For the thorough:**
→ Read README.md, then SETUP.md, then DEPLOYMENT.md

**For developers:**
→ CLAUDE_CODE_PROMPT.md has all technical specs

**For reference:**
→ PROJECT_STRUCTURE.md has commands and file locations

**For troubleshooting:**
→ Check "Troubleshooting" sections in any doc

## 🎯 Goal Checklist

- [ ] Server is configured (SETUP.md complete)
- [ ] Code is built (CLAUDE_CODE_PROMPT.md used)
- [ ] Bot runs locally for testing
- [ ] Code is on GitHub
- [ ] Bot deployed to server (DEPLOYMENT.md complete)
- [ ] systemd service is running
- [ ] Bot accessible on LAN
- [ ] Widget tested on test page
- [ ] Widget embedded on client site
- [ ] Client is happy! 🎉

## 📞 Project Structure Quick Ref

```
/opt/bot-farm/
├── README.md              ← Overview
├── SETUP.md               ← Server setup
├── DEPLOYMENT.md          ← Deploy workflow
├── QUICKSTART.md          ← Fast start
├── CLAUDE_CODE_PROMPT.md  ← Build instructions
├── PROJECT_STRUCTURE.md   ← Reference
├── .env                   ← Your API key
├── shared/                ← Shared code
├── bots/                  ← Your bots
└── nginx/                 ← Reverse proxy
```

## 🤖 Bot Checklist

For each new bot client:

1. **Create bot directory**
   - [ ] `mkdir bots/client-name`
   - [ ] Copy template files

2. **Customize bot**
   - [ ] Edit prompts.py (personality & knowledge)
   - [ ] Edit config.py (port, name, etc.)
   - [ ] Test locally

3. **Deploy bot**
   - [ ] Create systemd service
   - [ ] Enable and start service
   - [ ] Open firewall port

4. **Integrate widget**
   - [ ] Create test page
   - [ ] Test functionality
   - [ ] Embed on client site

5. **Monitor**
   - [ ] Check logs regularly
   - [ ] Monitor API usage
   - [ ] Gather feedback

## 📚 External Resources

- **Anthropic API Docs**: https://docs.anthropic.com/
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **Flask Docs**: https://flask.palletsprojects.com/
- **Python venv**: https://docs.python.org/3/library/venv.html
- **systemd**: https://www.freedesktop.org/software/systemd/man/
- **nginx**: https://nginx.org/en/docs/

## 🚨 Important Notes

⚠️ **Never commit .env to git** - Contains API keys  
⚠️ **Use HTTPS in production** - HTTP is for testing only  
⚠️ **Backup your .env file** - You can't recover API keys  
⚠️ **Monitor API usage** - Watch your Anthropic console  
⚠️ **Test before deploying** - Always test changes locally first  

## 🎉 Success Indicators

You'll know you're successful when:

✅ `systemctl status bot-keystone` shows "active (running)"  
✅ `curl http://localhost:5000/health` returns JSON  
✅ Widget loads and chats on test page  
✅ Client website has working chat widget  
✅ Bot gives helpful, accurate responses  
✅ You can add new bots easily  
✅ Your buddy loves his new website assistant!  

---

## Next Steps

**Right now:**
1. [Create your GitHub repository](https://github.com/new)
2. Upload these documentation files
3. Start with [QUICKSTART.md](./QUICKSTART.md) if you want speed
4. Or follow [DEPLOYMENT.md](./DEPLOYMENT.md) for the full workflow

**After first bot is live:**
1. Monitor and improve prompts
2. Gather user feedback
3. Plan next bot deployment
4. Consider HTTPS and domain setup

---

**Ready to build your bot army?** Start with the file that matches your style:
- **Fast learner**: QUICKSTART.md
- **Detail-oriented**: DEPLOYMENT.md → SETUP.md
- **Developer**: CLAUDE_CODE_PROMPT.md
- **Just browsing**: README.md

**Good luck, and may your bots be ever helpful!** 🤖⚔️
