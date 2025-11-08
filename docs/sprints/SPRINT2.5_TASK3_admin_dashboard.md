# Sprint 2.5 - Task 3: Admin Dashboard

**Claude Code Prompt**: Build a web-based admin dashboard for managing the Bot Army

---

## Context

We now have:
- ✅ Database tracking clients, bots, and usage
- ✅ Bots logging conversations and API calls
- ✅ Data accumulating in database

Now we need a dashboard to:
- View all clients and their bots
- Monitor usage and costs
- Control bot status (start/stop)
- Generate reports
- Manage subscriptions

---

## Prerequisites

- Sprint 2.5 Tasks 1 & 2 completed
- Flask knowledge
- Database has data to display

---

## Task: Create Admin Dashboard Application

### File Structure

Create these new files:

```
/opt/bot-farm/
├── admin/
│   ├── app.py                    # Flask admin application
│   ├── templates/
│   │   ├── base.html            # Base template with navigation
│   │   ├── dashboard.html       # Main dashboard view
│   │   ├── clients.html         # Client list and details
│   │   ├── bots.html            # Bot list and control
│   │   ├── usage.html           # Usage statistics and reports
│   │   └── conversations.html   # View conversation logs
│   └── static/
│       ├── css/
│       │   └── admin.css        # Admin styling
│       └── js/
│           └── admin.js         # Client-side interactions
```

---

## Part 1: Admin Flask Application

### Create `admin/app.py`

```python
"""
Admin Dashboard for Bot Army Platform

A web interface for managing clients, bots, and monitoring usage.

Run with: python admin/app.py
Access at: http://localhost:5001/admin
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import sys
sys.path.insert(0, '/opt/bot-farm')

from shared.database import (
    get_all_clients,
    get_all_bots,
    get_bot_by_id,
    update_bot_status,
    get_usage_by_bot,
    get_usage_by_client,
    execute_query,
    get_overdue_subscriptions
)
import os
import subprocess
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Configuration
ADMIN_PORT = 5001

# ============================================================================
# Dashboard Routes
# ============================================================================

@app.route('/')
@app.route('/admin')
def dashboard():
    """Main dashboard with overview statistics"""
    try:
        # Get summary statistics
        total_clients = len(get_all_clients())
        all_bots = get_all_bots()
        total_bots = len(all_bots)
        active_bots = len([b for b in all_bots if b['status'] == 'active'])
        
        # Get today's usage across all bots
        today_usage = execute_query("""
            SELECT 
                SUM(requests) as total_requests,
                SUM(cost) as total_cost
            FROM api_usage
            WHERE date = CURRENT_DATE
        """)
        
        # Get this month's usage
        month_usage = execute_query("""
            SELECT 
                SUM(requests) as total_requests,
                SUM(cost) as total_cost
            FROM api_usage
            WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
        """)
        
        # Get overdue subscriptions
        overdue = get_overdue_subscriptions()
        
        # Get recent conversations
        recent_conversations = execute_query("""
            SELECT 
                c.session_id,
                c.message_count,
                c.started_at,
                b.bot_name
            FROM conversations c
            JOIN bots b ON c.bot_id = b.bot_id
            ORDER BY c.started_at DESC
            LIMIT 10
        """)
        
        return render_template('dashboard.html',
            total_clients=total_clients,
            total_bots=total_bots,
            active_bots=active_bots,
            today_usage=today_usage[0] if today_usage else {'total_requests': 0, 'total_cost': 0},
            month_usage=month_usage[0] if month_usage else {'total_requests': 0, 'total_cost': 0},
            overdue_count=len(overdue),
            recent_conversations=recent_conversations
        )
    except Exception as e:
        return f"Error loading dashboard: {e}", 500

# ============================================================================
# Client Management
# ============================================================================

@app.route('/admin/clients')
def clients():
    """List all clients with their bots and subscriptions"""
    try:
        clients_data = execute_query("""
            SELECT 
                c.id,
                c.name,
                c.email,
                c.company_name,
                c.status,
                c.created_at,
                s.plan_name,
                s.price,
                s.current_period_end,
                s.status as subscription_status,
                COUNT(b.id) as bot_count
            FROM clients c
            LEFT JOIN subscriptions s ON c.id = s.client_id
            LEFT JOIN bots b ON c.id = b.client_id
            GROUP BY c.id, c.name, c.email, c.company_name, c.status, 
                     c.created_at, s.plan_name, s.price, s.current_period_end, s.status
            ORDER BY c.created_at DESC
        """)
        
        return render_template('clients.html', clients=clients_data)
    except Exception as e:
        return f"Error loading clients: {e}", 500

# ============================================================================
# Bot Management
# ============================================================================

@app.route('/admin/bots')
def bots():
    """List all bots with control options"""
    try:
        bots_data = execute_query("""
            SELECT 
                b.id,
                b.bot_id,
                b.bot_name,
                b.port,
                b.status,
                c.name as client_name,
                c.email as client_email,
                b.created_at
            FROM bots b
            JOIN clients c ON b.client_id = c.id
            ORDER BY b.created_at DESC
        """)
        
        # Check if services are actually running
        for bot in bots_data:
            service_name = f"bot-{bot['bot_id'].replace('_', '-')}"
            is_running = check_service_status(service_name)
            bot['service_running'] = is_running
        
        return render_template('bots.html', bots=bots_data)
    except Exception as e:
        return f"Error loading bots: {e}", 500

@app.route('/admin/bot/<bot_id>/toggle', methods=['POST'])
def toggle_bot(bot_id):
    """Start or stop a bot service"""
    try:
        # Get current status
        bot = get_bot_by_id(bot_id)
        if not bot:
            return jsonify({'error': 'Bot not found'}), 404
        
        service_name = f"bot-{bot_id.replace('_', '-')}"
        
        # Toggle service
        if bot['status'] == 'active':
            # Stop bot
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', service_name],
                capture_output=True,
                text=True
            )
            update_bot_status(bot_id, 'inactive')
            action = 'stopped'
        else:
            # Start bot
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', service_name],
                capture_output=True,
                text=True
            )
            update_bot_status(bot_id, 'active')
            action = 'started'
        
        if result.returncode != 0:
            return jsonify({
                'error': f'Failed to {action} bot',
                'details': result.stderr
            }), 500
        
        return jsonify({
            'success': True,
            'action': action,
            'bot_id': bot_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Usage & Analytics
# ============================================================================

@app.route('/admin/usage')
def usage():
    """View usage statistics and generate reports"""
    try:
        # Get date range from query params
        days = int(request.args.get('days', 30))
        start_date = datetime.now().date() - timedelta(days=days)
        
        # Usage by bot
        usage_by_bot = execute_query("""
            SELECT 
                b.bot_name,
                b.bot_id,
                c.name as client_name,
                SUM(u.requests) as total_requests,
                SUM(u.input_tokens) as total_input_tokens,
                SUM(u.output_tokens) as total_output_tokens,
                SUM(u.cost) as total_cost
            FROM api_usage u
            JOIN bots b ON u.bot_id = b.bot_id
            JOIN clients c ON b.client_id = c.id
            WHERE u.date >= %s
            GROUP BY b.bot_name, b.bot_id, c.name
            ORDER BY total_cost DESC
        """, (start_date,))
        
        # Daily usage trend
        daily_usage = execute_query("""
            SELECT 
                date,
                SUM(requests) as requests,
                SUM(cost) as cost
            FROM api_usage
            WHERE date >= %s
            GROUP BY date
            ORDER BY date
        """, (start_date,))
        
        # Total for period
        period_total = execute_query("""
            SELECT 
                SUM(requests) as total_requests,
                SUM(cost) as total_cost
            FROM api_usage
            WHERE date >= %s
        """, (start_date,))
        
        return render_template('usage.html',
            usage_by_bot=usage_by_bot,
            daily_usage=daily_usage,
            period_total=period_total[0] if period_total else {},
            days=days,
            start_date=start_date
        )
    except Exception as e:
        return f"Error loading usage: {e}", 500

# ============================================================================
# Conversations
# ============================================================================

@app.route('/admin/conversations')
def conversations():
    """View conversation logs"""
    try:
        bot_id = request.args.get('bot_id')
        limit = int(request.args.get('limit', 50))
        
        query = """
            SELECT 
                c.id,
                c.session_id,
                c.message_count,
                c.started_at,
                c.ended_at,
                c.user_ip,
                b.bot_name,
                b.bot_id
            FROM conversations c
            JOIN bots b ON c.bot_id = b.bot_id
        """
        
        params = []
        if bot_id:
            query += " WHERE c.bot_id = %s"
            params.append(bot_id)
        
        query += " ORDER BY c.started_at DESC LIMIT %s"
        params.append(limit)
        
        conversations_data = execute_query(query, tuple(params))
        
        # Get list of bots for filter
        bots_list = execute_query("SELECT bot_id, bot_name FROM bots")
        
        return render_template('conversations.html',
            conversations=conversations_data,
            bots=bots_list,
            selected_bot=bot_id
        )
    except Exception as e:
        return f"Error loading conversations: {e}", 500

@app.route('/admin/conversation/<int:conversation_id>')
def conversation_detail(conversation_id):
    """View messages in a specific conversation"""
    try:
        messages = execute_query("""
            SELECT 
                m.role,
                m.content,
                m.tokens_used,
                m.created_at
            FROM messages m
            WHERE m.conversation_id = %s
            ORDER BY m.created_at
        """, (conversation_id,))
        
        # Get conversation info
        conversation_info = execute_query("""
            SELECT 
                c.*,
                b.bot_name
            FROM conversations c
            JOIN bots b ON c.bot_id = b.bot_id
            WHERE c.id = %s
        """, (conversation_id,))
        
        return render_template('conversation_detail.html',
            messages=messages,
            conversation=conversation_info[0] if conversation_info else None
        )
    except Exception as e:
        return f"Error loading conversation: {e}", 500

# ============================================================================
# Helper Functions
# ============================================================================

def check_service_status(service_name):
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except:
        return False

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Bot Army Admin Dashboard")
    print("=" * 60)
    print(f"Starting admin server on port {ADMIN_PORT}")
    print(f"Access at: http://localhost:{ADMIN_PORT}/admin")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=ADMIN_PORT,
        debug=True
    )
```

---

## Part 2: HTML Templates

### Base Template Structure

All templates should extend a base template with:
- Navigation menu
- Consistent styling
- Mobile responsive
- Bootstrap or Tailwind CSS (your choice)

### Key Features for Each Template:

**dashboard.html**:
- Summary cards (clients, bots, usage, costs)
- Quick stats (today's activity, month-to-date)
- Alerts for overdue payments
- Recent activity feed

**clients.html**:
- Table of all clients
- Subscription status indicators
- Bot count per client
- Quick actions (view details, suspend)

**bots.html**:
- Table of all bots with status
- Start/Stop buttons
- Service status indicators
- Links to bot stats

**usage.html**:
- Charts (daily usage, cost trends)
- Table of usage by bot
- Date range selector
- Export to CSV button

**conversations.html**:
- List of recent conversations
- Filter by bot
- Click to view messages
- Session duration and message count

---

## Part 3: Styling

Create simple, clean CSS:

```css
/* admin/static/css/admin.css */

:root {
    --primary-color: #2563eb;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background-color: #f3f4f6;
}

.dashboard-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.status-active { background: #d1fae5; color: #065f46; }
.status-inactive { background: #fee2e2; color: #991b1b; }
.status-overdue { background: #fef3c7; color: #92400e; }

/* Add more styles as needed */
```

---

## Part 4: JavaScript Interactions

```javascript
// admin/static/js/admin.js

// Toggle bot status
function toggleBot(botId) {
    if (!confirm('Are you sure you want to toggle this bot?')) {
        return;
    }
    
    fetch(`/admin/bot/${botId}/toggle`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Bot ${data.action} successfully`);
            location.reload();
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        alert('Failed to toggle bot: ' + error);
    });
}

// Add more interactions as needed
```

---

## Security Considerations

**IMPORTANT**: This is a basic admin dashboard. For production:

1. **Add Authentication**:
   - Login system (Flask-Login)
   - Password protection
   - Session management

2. **Add Authorization**:
   - Role-based access
   - Audit logs
   - API tokens

3. **Secure Actions**:
   - CSRF protection
   - Rate limiting
   - Input validation

4. **Network Security**:
   - HTTPS only
   - Firewall rules
   - VPN access

**For now**: Run only on localhost or internal network!

---

## Testing

### Start Admin Dashboard

```bash
cd /opt/bot-farm
source venv/bin/activate
python admin/app.py
```

Access at: http://192.168.1.66:5001/admin

### Test Each Page

1. ✅ Dashboard loads with statistics
2. ✅ Clients page shows all clients
3. ✅ Bots page shows all bots
4. ✅ Toggle bot works (start/stop)
5. ✅ Usage page shows charts and data
6. ✅ Conversations page lists sessions
7. ✅ Can view individual conversation messages

---

## Success Criteria

✅ Admin app runs on port 5001  
✅ Dashboard shows overview statistics  
✅ Can view all clients and bots  
✅ Can start/stop bots via UI  
✅ Usage statistics display correctly  
✅ Can view conversation logs  
✅ All pages are responsive  
✅ No errors in console  
✅ Data updates in real-time  

---

## Future Enhancements

- 📊 Advanced charts (Chart.js)
- 📧 Email alerts for issues
- 🔐 User authentication
- 📱 Mobile app
- 📈 Predictive analytics
- 💳 Wave integration for billing
- 🤖 Bot deployment wizard
- 📝 Configuration editor

---

**Build it with Claude Code!** 🎯

Create a professional, functional admin dashboard that makes managing the Bot Army simple and efficient.
