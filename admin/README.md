# Bot Army Admin Dashboard

A comprehensive web-based admin dashboard for managing the Bot Army platform.

## Features

- **Dashboard**: Overview statistics and real-time metrics
- **Client Management**: View all clients, subscriptions, and bot counts
- **Bot Control**: Start/stop bots via systemctl integration
- **Usage Analytics**: Track API usage, costs, and token consumption
- **Conversation Logs**: View and search conversation history
- **Responsive Design**: Mobile-friendly interface

## Installation

### 1. Install Dependencies

```bash
cd /opt/bot-farm/admin
pip install -r requirements.txt
```

Or if using a virtual environment:

```bash
cd /opt/bot-farm
source venv/bin/activate
pip install -r admin/requirements.txt
```

### 2. Verify Database Connection

The admin dashboard uses the shared database module. Ensure your database is configured:

```bash
# Check database connection
python -c "from shared.database import get_all_clients; print(len(get_all_clients()))"
```

## Running the Dashboard

### Start the Admin Server

```bash
cd /opt/bot-farm
python admin/app.py
```

The dashboard will be available at:
- Local: http://localhost:5001/admin
- Network: http://192.168.1.66:5001/admin (replace with your IP)

### Run as Background Service (Optional)

Create a systemd service for the admin dashboard:

```bash
sudo nano /etc/systemd/system/bot-admin.service
```

Add the following content:

```ini
[Unit]
Description=Bot Army Admin Dashboard
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bot-farm
Environment="PATH=/opt/bot-farm/venv/bin"
ExecStart=/opt/bot-farm/venv/bin/python admin/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bot-admin
sudo systemctl start bot-admin
sudo systemctl status bot-admin
```

## Dashboard Pages

### 1. Dashboard (`/admin`)
- Total clients, bots, and active bots
- Today's and month-to-date usage
- Overdue subscription alerts
- Recent conversations feed
- Quick action buttons

### 2. Clients (`/admin/clients`)
- List of all clients with details
- Subscription status indicators
- Bot count per client
- Monthly recurring revenue (MRR)
- Active/inactive statistics

### 3. Bots (`/admin/bots`)
- All bots with status information
- Database status vs. service status
- Start/stop controls
- Client information
- Port assignments

### 4. Usage (`/admin/usage`)
- Date range selector (7, 30, 90 days)
- Daily usage trend charts
- Usage by bot table
- Request and cost metrics
- Token consumption statistics

### 5. Conversations (`/admin/conversations`)
- List of all conversation sessions
- Filter by bot
- Message counts and duration
- Click to view detailed messages
- Active conversation indicator

### 6. Conversation Detail (`/admin/conversation/<id>`)
- Full message history
- User and assistant messages
- Token usage per message
- Conversation metadata
- Session information

## Bot Control

The dashboard allows you to start and stop bots:

1. Navigate to **Bots** page
2. Find the bot you want to control
3. Click the **Start** or **Stop** button
4. Confirm the action
5. The page will reload with updated status

**Requirements**:
- Bots must have systemd services configured
- Service names follow pattern: `bot-<bot_id>`
- User running admin must have sudo privileges for systemctl

## Security Notes

**IMPORTANT**: This is a basic admin dashboard without authentication.

### Current Security:
- No login/authentication
- No user roles or permissions
- No CSRF protection
- Runs on HTTP (not HTTPS)

### Recommended for Production:

1. **Add Authentication**:
   - Implement Flask-Login
   - Password protection
   - Session management

2. **Enable HTTPS**:
   - Use nginx reverse proxy
   - SSL/TLS certificates
   - Force HTTPS redirect

3. **Network Security**:
   - Firewall rules (allow only internal IPs)
   - VPN access requirement
   - IP whitelisting

4. **Add Authorization**:
   - Role-based access control
   - Audit logging
   - API rate limiting

5. **Security Headers**:
   - CSRF tokens
   - Content Security Policy
   - XSS protection

### For Development:
Run only on localhost or internal network:
```bash
# Restrict to localhost only
# In app.py, change:
app.run(host='127.0.0.1', port=5001, debug=True)
```

## Configuration

### Port Configuration

Edit `admin/app.py` to change the port:

```python
ADMIN_PORT = 5001  # Change to your preferred port
```

### Database Path

The admin uses the shared database module at `/opt/bot-farm/shared/database.py`.

If you need to adjust the database connection, edit the shared module.

## Troubleshooting

### Dashboard Won't Start

**Error**: Module not found
```bash
# Ensure path is correct
cd /opt/bot-farm
python admin/app.py
```

**Error**: Database connection failed
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify database credentials in shared/database.py
```

### Bot Toggle Not Working

**Error**: Permission denied
```bash
# Ensure user has sudo access
sudo visudo
# Add: your_user ALL=(ALL) NOPASSWD: /bin/systemctl
```

**Error**: Service not found
```bash
# Verify service exists
systemctl list-units | grep bot-
```

### Charts Not Displaying

**Error**: Chart.js not loading
- Check internet connection (CDN required)
- Or download Chart.js locally to static/js/

### Static Files Not Loading

**Error**: 404 on CSS/JS files
```bash
# Verify file structure
ls -la admin/static/css/
ls -la admin/static/js/

# Ensure Flask can find static directory
```

## Development

### File Structure

```
admin/
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── templates/
│   ├── base.html            # Base template
│   ├── dashboard.html       # Main dashboard
│   ├── clients.html         # Client management
│   ├── bots.html            # Bot control
│   ├── usage.html           # Usage analytics
│   ├── conversations.html   # Conversation list
│   └── conversation_detail.html  # Message viewer
└── static/
    ├── css/
    │   └── admin.css        # Styling
    └── js/
        └── admin.js         # JavaScript interactions
```

### Adding New Features

1. **New Route**: Add route in `app.py`
2. **New Template**: Create HTML in `templates/`
3. **New Styles**: Add CSS to `static/css/admin.css`
4. **New JS**: Add functions to `static/js/admin.js`

### Custom Queries

Add new database queries in `app.py`:

```python
custom_data = execute_query("""
    SELECT * FROM your_table
    WHERE condition = %s
""", (param,))
```

## Future Enhancements

Planned features for future versions:

- User authentication and authorization
- Advanced charts and analytics
- Email alerts for issues
- Bot deployment wizard
- Configuration editor
- Export reports to PDF
- Wave payment integration
- Mobile app
- Predictive analytics
- Real-time WebSocket updates

## Support

For issues or questions:
1. Check this README
2. Review Sprint 2.5 Task 3 documentation
3. Examine application logs
4. Verify database connectivity

## License

Part of the Bot Army Platform.
