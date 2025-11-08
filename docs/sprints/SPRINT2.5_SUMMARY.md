# Sprint 2.5: Database Setup - Complete Documentation

**Status**: ✅ Infrastructure Complete | 📝 Documentation Ready | ⏳ Code Integration Pending

---

## 📚 Documentation Package Contents

This package contains everything needed to complete Sprint 2.5 (Database Setup & Integration):

### 1. **SPRINT2.5_DATABASE_SETUP.md** (Main Guide)
Complete walkthrough of:
- PostgreSQL installation on Debian 12
- Database and user creation
- Schema setup (8 tables)
- Initial data loading
- Python library installation
- Testing and troubleshooting

**Status**: ✅ Completed on server  
**Time**: ~1 hour (done!)

---

### 2. **SPRINT2.5_TASK1_integration.md** (Claude Code Prompt)
**Purpose**: Create `shared/database.py` module

**What it builds**:
- Database connection management
- Helper functions for all tables
- Client, bot, conversation CRUD operations
- API usage tracking functions
- Subscription management
- Error handling and logging

**Time Estimate**: 30-45 minutes (Claude Code)  
**Complexity**: Medium

---

### 3. **SPRINT2.5_TASK2_bot_integration.md** (Claude Code Prompt)
**Purpose**: Integrate database logging into bots

**What it updates**:
- `shared/claude_client.py` - Automatic usage tracking
- `bots/keystone-landscaping/app.py` - Conversation logging
- `shared/widget/bot-widget.js` - Session ID tracking
- Add admin stats endpoint

**Time Estimate**: 45-60 minutes (Claude Code)  
**Complexity**: Medium-High

---

### 4. **SPRINT2.5_TASK3_admin_dashboard.md** (Claude Code Prompt)
**Purpose**: Build web admin interface

**What it creates**:
- `admin/app.py` - Flask admin application
- HTML templates (dashboard, clients, bots, usage, conversations)
- CSS styling
- JavaScript interactions
- Bot control (start/stop)
- Usage reports and analytics

**Time Estimate**: 2-3 hours (Claude Code)  
**Complexity**: High

---

## 🎯 Sprint 2.5 Goals

### Primary Objectives
1. ✅ **Database Infrastructure** - PostgreSQL setup and schema
2. ⏳ **Data Persistence** - Store all conversations and messages
3. ⏳ **Usage Tracking** - Track API calls for billing
4. ⏳ **Client Management** - Manage clients and subscriptions
5. ⏳ **Admin Interface** - View and control everything

### Why This Matters
- **Billing**: Track usage to bill clients accurately
- **Analytics**: Understand bot performance and usage patterns
- **Management**: Control multiple bots from one place
- **Scaling**: Foundation for managing 100+ bots
- **Reliability**: Data persistence and audit trails

---

## 📊 Database Schema Overview

### Tables Created

```
clients (8 columns)
  ├── id, name, email, company_name, phone
  ├── created_at, status
  └── Stores customer information

bots (9 columns)
  ├── id, client_id, bot_id, bot_name, port
  ├── status, config (JSON), created_at, updated_at
  └── Each bot instance

subscriptions (11 columns)
  ├── id, client_id, plan_name, price
  ├── billing_cycle, status, dates
  ├── wave_invoice_id, last_paid_at
  └── Billing and plans

conversations (7 columns)
  ├── id, bot_id, session_id
  ├── user_ip, timestamps, message_count
  └── Chat sessions

messages (5 columns)
  ├── id, conversation_id, role
  ├── content, tokens_used, created_at
  └── Individual messages

api_usage (7 columns)
  ├── id, bot_id, date
  ├── requests, input_tokens, output_tokens, cost
  └── Daily usage for billing

invoices (8 columns)
  ├── id, client_id, invoice_number
  ├── amount, status, dates, wave_invoice_id
  └── Invoice tracking

payments (7 columns)
  ├── id, client_id, invoice_id
  ├── wave_payment_id, amount, method, wave_fee
  └── Payment history
```

**Total**: 8 tables, ~60 columns, 5 indexes

---

## 🚀 Implementation Workflow

### What's Done (Infrastructure)
✅ PostgreSQL installed and running  
✅ Database `botfarm` created  
✅ User `botfarm` with proper permissions  
✅ Complete schema loaded (8 tables)  
✅ Initial data (Andrew/Keystone bot)  
✅ Python libraries installed (`psycopg2-binary`)  
✅ Environment configured (`.env` with DB_PASSWORD)  
✅ Tested and verified working  

### What's Next (Code Integration)

**Phase 1: Task 1 - Database Module** (Use Claude Code)
```bash
cd /path/to/my-bot-army
# Give Claude Code the SPRINT2.5_TASK1_integration.md prompt
# It will create shared/database.py
```

**Phase 2: Task 2 - Bot Integration** (Use Claude Code)
```bash
# Give Claude Code the SPRINT2.5_TASK2_bot_integration.md prompt
# It will update existing bot files to log to database
```

**Phase 3: Task 3 - Admin Dashboard** (Use Claude Code)
```bash
# Give Claude Code the SPRINT2.5_TASK3_admin_dashboard.md prompt
# It will create complete admin interface
```

**Phase 4: Deploy to Server**
```bash
# On Debian server
cd /opt/bot-farm
git pull origin main
sudo systemctl restart bot-keystone
python admin/app.py  # Start admin dashboard
```

---

## ⏱️ Time Estimates

| Task | Method | Time | Status |
|------|--------|------|--------|
| **Infrastructure** | Manual | 1 hour | ✅ Done |
| **Task 1: Database Module** | Claude Code | 30-45 min | ⏳ Pending |
| **Task 2: Bot Integration** | Claude Code | 45-60 min | ⏳ Pending |
| **Task 3: Admin Dashboard** | Claude Code | 2-3 hours | ⏳ Pending |
| **Testing & Polish** | Manual | 30 min | ⏳ Pending |
| **TOTAL** | Mixed | **5-6 hours** | 20% Complete |

---

## 💰 Value Delivered

### Immediate Benefits
- ✅ Professional client management
- ✅ Accurate billing based on usage
- ✅ Conversation history for debugging
- ✅ Usage analytics for optimization
- ✅ Centralized bot control

### Long-term Benefits
- 📈 Scale to 100+ bots efficiently
- 💵 Transparent billing for clients
- 🔍 Insights into bot performance
- 🎯 Data-driven improvements
- 🏢 Professional business operations

### ROI
- **Investment**: ~6 hours of development
- **Savings**: Hours per week in manual management
- **Revenue**: Enables accurate billing and scaling
- **Worth**: Foundational piece for entire business

---

## 🧪 Testing Checklist

After completing all tasks, verify:

**Database**:
- [ ] Can connect to PostgreSQL
- [ ] All tables exist with correct schema
- [ ] Initial data is present
- [ ] Indexes are created

**Bot Integration**:
- [ ] Conversations are logged
- [ ] Messages are stored
- [ ] API usage is tracked
- [ ] Bot works if database is down

**Admin Dashboard**:
- [ ] Dashboard loads and shows stats
- [ ] Can view all clients and bots
- [ ] Can start/stop bots
- [ ] Usage reports display correctly
- [ ] Can view conversation logs

**End-to-End**:
- [ ] Send test message via widget
- [ ] Verify it appears in database
- [ ] Check admin dashboard shows it
- [ ] Verify API usage is tracked
- [ ] Confirm costs are calculated

---

## 🔐 Security Notes

**Current Setup** (Development):
- ✅ Database only accessible locally
- ✅ Password-protected access
- ✅ No external connections allowed

**Production Requirements** (Future):
- 🔒 HTTPS for admin dashboard
- 🔒 User authentication
- 🔒 CSRF protection
- 🔒 Rate limiting
- 🔒 Audit logging
- 🔒 Backup system

---

## 🎓 Learning Resources

If you want to understand the components:

**PostgreSQL**:
- Official docs: https://www.postgresql.org/docs/
- Tutorial: https://www.postgresqltutorial.com/

**psycopg2** (Python PostgreSQL):
- Docs: https://www.psycopg.org/docs/
- Tutorial: https://pynative.com/python-postgresql-tutorial/

**Flask** (Admin Dashboard):
- Official docs: https://flask.palletsprojects.com/
- Mega tutorial: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

---

## 📝 Next Steps

### Today:
1. **Review** all documentation
2. **Understand** the architecture
3. **Plan** when to run each Claude Code task

### Tomorrow:
1. **Execute Task 1** - Database module (Claude Code)
2. **Test** database functions work
3. **Commit** to GitHub

### This Week:
1. **Execute Task 2** - Bot integration (Claude Code)
2. **Test** logging works end-to-end
3. **Execute Task 3** - Admin dashboard (Claude Code)
4. **Deploy** everything to server
5. **Test** complete system

### Success Criteria:
- ✅ All code tasks completed
- ✅ Tests passing
- ✅ Admin dashboard running
- ✅ Keystone bot logging to database
- ✅ Can view stats in dashboard
- ✅ Ready to add more bots!

---

## 🤝 Support

**If you get stuck**:

1. **Check troubleshooting** section in SPRINT2.5_DATABASE_SETUP.md
2. **Review error messages** carefully
3. **Test individual components** in isolation
4. **Ask Claude** for specific debugging help
5. **Check database** directly with `psql`

**Common issues already documented**:
- Permission denied for schema public
- Peer authentication failed
- psycopg2 not found
- Relation already exists
- Connection refused

---

## 🎉 What You've Accomplished

**Infrastructure (Today)**:
- ✅ Professional PostgreSQL database
- ✅ Complete schema for scaling
- ✅ Proper authentication and security
- ✅ Ready for production workloads

**Foundation Built For**:
- 📊 Analytics and reporting
- 💰 Usage-based billing
- 🎯 Client management
- 🤖 Bot control and monitoring
- 📈 Business scaling

**Next Sprint Preview**:
- Sprint 3: RAG Implementation (document-based knowledge)
- Sprint 4: Advanced Capabilities (lead capture, booking)
- Sprint 5: Full billing automation (Stripe integration)

---

## 📦 File Checklist

Verify you have all documentation:

- [ ] SPRINT2.5_DATABASE_SETUP.md (Main guide)
- [ ] SPRINT2.5_TASK1_integration.md (Database module)
- [ ] SPRINT2.5_TASK2_bot_integration.md (Bot integration)
- [ ] SPRINT2.5_TASK3_admin_dashboard.md (Admin UI)
- [ ] SPRINT2.5_SUMMARY.md (This file)

All files should be in your `my-bot-army` repository under a `docs/` or `sprints/` folder.

---

## 🚀 Ready to Code!

**Your database infrastructure is complete!**

The next steps are all code generation with Claude Code using the three task prompts provided. Each prompt is:
- ✅ Complete and detailed
- ✅ Production-ready specs
- ✅ Security best practices included
- ✅ Testing guidance included
- ✅ Ready to copy/paste to Claude Code

**Estimated completion time**: 4-5 hours of Claude Code work spread over 1-2 days.

**Result**: A professional, scalable bot platform with full database integration and management capabilities.

---

**Sprint 2.5 Documentation Complete!** 🎯

Database foundation is solid. Time to build on it with Claude Code! 🤖

---

*Generated: 2025-01-07*  
*Version: 1.0*  
*Status: Ready for Implementation*
