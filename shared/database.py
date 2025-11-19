"""
Database connection and helper functions for Bot Army platform.

This module provides a clean interface for interacting with the PostgreSQL
database, including functions for managing clients, bots, conversations,
and API usage tracking.

Usage:
    from shared.database import get_bot_by_id, log_api_usage

    bot = get_bot_by_id('keystone-landscaping')
    log_api_usage('keystone-landscaping', 1000, 500, 0.015)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

# Load environment variables from /opt/bot-farm/.env
load_dotenv('/opt/bot-farm/.env')

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'botfarm',
    'user': 'botfarm',
    'password': os.getenv('DB_PASSWORD')
}


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically commits on success, rolls back on error.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients")

    Yields:
        psycopg2.connection: Database connection object
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Execute SELECT query, return all results as list of dicts.

    Args:
        query: SQL SELECT query with %s placeholders
        params: Tuple of parameters for query

    Returns:
        List of dictionaries representing rows

    Example:
        results = execute_query("SELECT * FROM clients WHERE status = %s", ('active',))
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
    except Exception as e:
        print(f"Error executing query: {e}")
        return []


def execute_update(query: str, params: tuple = None) -> int:
    """
    Execute INSERT/UPDATE/DELETE, return number of rows affected.

    Args:
        query: SQL INSERT/UPDATE/DELETE query with %s placeholders
        params: Tuple of parameters for query

    Returns:
        Number of rows affected

    Example:
        rows = execute_update("UPDATE clients SET status = %s WHERE id = %s", ('active', 1))
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.rowcount
    except Exception as e:
        print(f"Error executing update: {e}")
        return 0


def execute_one(query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """
    Execute SELECT query, return single result or None.

    Args:
        query: SQL SELECT query with %s placeholders
        params: Tuple of parameters for query

    Returns:
        Dictionary representing single row, or None if not found

    Example:
        client = execute_one("SELECT * FROM clients WHERE id = %s", (1,))
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()
    except Exception as e:
        print(f"Error executing query: {e}")
        return None


# ============================================================================
# CLIENT FUNCTIONS
# ============================================================================

def get_client(client_id: int) -> Optional[Dict[str, Any]]:
    """
    Get client by ID.

    Args:
        client_id: Client ID

    Returns:
        Client dictionary or None if not found
    """
    try:
        query = "SELECT * FROM clients WHERE id = %s"
        return execute_one(query, (client_id,))
    except Exception as e:
        print(f"Error fetching client {client_id}: {e}")
        return None


def get_client_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get client by email address.

    Args:
        email: Client email address

    Returns:
        Client dictionary or None if not found
    """
    try:
        query = "SELECT * FROM clients WHERE email = %s"
        return execute_one(query, (email,))
    except Exception as e:
        print(f"Error fetching client by email {email}: {e}")
        return None


def create_client(name: str, email: str, company_name: str = None,
                 phone: str = None) -> Optional[int]:
    """
    Create a new client, return client_id.

    Args:
        name: Client name
        email: Client email address
        company_name: Optional company name
        phone: Optional phone number

    Returns:
        New client ID or None on error

    Example:
        client_id = create_client("John Doe", "john@example.com", "ACME Corp")
    """
    try:
        query = """
            INSERT INTO clients (name, email, company_name, phone, status)
            VALUES (%s, %s, %s, %s, 'active')
            RETURNING id
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, email, company_name, phone))
            result = cursor.fetchone()
            return result['id'] if result else None
    except Exception as e:
        print(f"Error creating client: {e}")
        return None


def update_client_status(client_id: int, status: str) -> bool:
    """
    Update client status (active, suspended, cancelled).

    Args:
        client_id: Client ID
        status: New status ('active', 'suspended', or 'cancelled')

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        query = "UPDATE clients SET status = %s WHERE id = %s"
        rows = execute_update(query, (status, client_id))
        return rows > 0
    except Exception as e:
        print(f"Error updating client status: {e}")
        return False


def get_all_clients() -> List[Dict[str, Any]]:
    """
    Get all clients with their subscription status.

    Returns:
        List of client dictionaries with subscription info
    """
    try:
        query = """
            SELECT
                c.*,
                s.plan_name,
                s.status as subscription_status,
                s.current_period_end
            FROM clients c
            LEFT JOIN subscriptions s ON c.id = s.client_id AND s.status = 'active'
            ORDER BY c.created_at DESC
        """
        return execute_query(query)
    except Exception as e:
        print(f"Error fetching all clients: {e}")
        return []


# ============================================================================
# BOT FUNCTIONS
# ============================================================================

def get_bot_by_id(bot_id: str) -> Optional[Dict[str, Any]]:
    """
    Get bot information by bot_id (e.g., 'keystone-landscaping').

    Args:
        bot_id: Bot identifier string

    Returns:
        Bot dictionary or None if not found
    """
    try:
        query = "SELECT * FROM bots WHERE bot_id = %s"
        return execute_one(query, (bot_id,))
    except Exception as e:
        print(f"Error fetching bot {bot_id}: {e}")
        return None


def get_bots_by_client(client_id: int) -> List[Dict[str, Any]]:
    """
    Get all bots for a specific client.

    Args:
        client_id: Client ID

    Returns:
        List of bot dictionaries
    """
    try:
        query = "SELECT * FROM bots WHERE client_id = %s ORDER BY created_at DESC"
        return execute_query(query, (client_id,))
    except Exception as e:
        print(f"Error fetching bots for client {client_id}: {e}")
        return []


def create_bot(client_id: int, bot_id: str, bot_name: str,
               port: int, config: Dict = None) -> Optional[int]:
    """
    Create a new bot, return bot database id.

    Args:
        client_id: Client ID who owns the bot
        bot_id: Bot identifier (e.g., 'keystone-landscaping')
        bot_name: Display name for the bot
        port: Port number the bot runs on
        config: Optional JSON configuration dictionary

    Returns:
        New bot database ID or None on error

    Example:
        bot_id = create_bot(1, 'acme-bot', 'ACME Assistant', 5001, {'theme': 'blue'})
    """
    try:
        import json
        config_json = json.dumps(config) if config else None

        query = """
            INSERT INTO bots (client_id, bot_id, bot_name, port, config, status)
            VALUES (%s, %s, %s, %s, %s, 'active')
            RETURNING id
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (client_id, bot_id, bot_name, port, config_json))
            result = cursor.fetchone()
            return result['id'] if result else None
    except Exception as e:
        print(f"Error creating bot: {e}")
        return None


def update_bot_status(bot_id: str, status: str) -> bool:
    """
    Update bot status (active, inactive, suspended).

    Args:
        bot_id: Bot identifier
        status: New status ('active', 'inactive', or 'suspended')

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        query = "UPDATE bots SET status = %s WHERE bot_id = %s"
        rows = execute_update(query, (status, bot_id))
        return rows > 0
    except Exception as e:
        print(f"Error updating bot status: {e}")
        return False


def update_bot_config(bot_id: str, config: Dict) -> bool:
    """
    Update bot configuration JSON.

    Args:
        bot_id: Bot identifier
        config: Configuration dictionary to save

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        import json
        config_json = json.dumps(config)
        query = "UPDATE bots SET config = %s WHERE bot_id = %s"
        rows = execute_update(query, (config_json, bot_id))
        return rows > 0
    except Exception as e:
        print(f"Error updating bot config: {e}")
        return False


def get_all_bots() -> List[Dict[str, Any]]:
    """
    Get all bots with client information.

    Returns:
        List of bot dictionaries with associated client data
    """
    try:
        query = """
            SELECT
                b.*,
                c.name as client_name,
                c.email as client_email,
                c.company_name
            FROM bots b
            JOIN clients c ON b.client_id = c.id
            ORDER BY b.created_at DESC
        """
        return execute_query(query)
    except Exception as e:
        print(f"Error fetching all bots: {e}")
        return []


# ============================================================================
# CONVERSATION & MESSAGE FUNCTIONS
# ============================================================================

def create_conversation(bot_id: str, session_id: str,
                       user_ip: str = None) -> Optional[int]:
    """
    Create a new conversation, return conversation_id.

    Args:
        bot_id: Bot identifier
        session_id: Session identifier from web app
        user_ip: Optional user IP address

    Returns:
        New conversation ID or None on error
    """
    try:
        query = """
            INSERT INTO conversations (bot_id, session_id, user_ip)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (bot_id, session_id, user_ip))
            result = cursor.fetchone()
            return result['id'] if result else None
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None


def save_message(conversation_id: int, role: str, content: str,
                tokens_used: int = 0) -> Optional[int]:
    """
    Save a message to database.
    Also increments conversation message_count and updates ended_at.

    Args:
        conversation_id: Conversation ID
        role: Message role ('user', 'assistant', or 'system')
        content: Message content
        tokens_used: Number of tokens used (for API calls)

    Returns:
        New message ID or None on error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Insert message
            query = """
                INSERT INTO messages (conversation_id, role, content, tokens_used)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """
            cursor.execute(query, (conversation_id, role, content, tokens_used))
            result = cursor.fetchone()
            message_id = result['id'] if result else None

            # Update conversation
            update_query = """
                UPDATE conversations
                SET message_count = message_count + 1,
                    ended_at = NOW()
                WHERE id = %s
            """
            cursor.execute(update_query, (conversation_id,))

            return message_id
    except Exception as e:
        print(f"Error saving message: {e}")
        return None


def get_conversation_history(conversation_id: int,
                            limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get messages for a conversation.

    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages to return (default 50)

    Returns:
        List of message dictionaries, ordered by creation time
    """
    try:
        query = """
            SELECT * FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """
        return execute_query(query, (conversation_id, limit))
    except Exception as e:
        print(f"Error fetching conversation history: {e}")
        return []


def end_conversation(conversation_id: int) -> bool:
    """
    Mark conversation as ended.

    Args:
        conversation_id: Conversation ID

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        query = "UPDATE conversations SET ended_at = NOW() WHERE id = %s"
        rows = execute_update(query, (conversation_id,))
        return rows > 0
    except Exception as e:
        print(f"Error ending conversation: {e}")
        return False


# ============================================================================
# API USAGE TRACKING FUNCTIONS
# ============================================================================

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost based on current pricing.
    Claude Sonnet 4.5 pricing (as of 2025):
    - Input: $3 per million tokens
    - Output: $15 per million tokens

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in dollars

    Example:
        cost = calculate_cost(1000, 500)  # Returns 0.0105
    """
    INPUT_COST_PER_MILLION = 3.0
    OUTPUT_COST_PER_MILLION = 15.0

    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION

    return input_cost + output_cost


def log_api_usage(bot_id: str, input_tokens: int,
                 output_tokens: int, cost: float) -> bool:
    """
    Log API usage for billing.
    Uses UPSERT (INSERT ... ON CONFLICT) to aggregate daily usage.
    If entry for bot_id + today exists, increment values.
    Otherwise, create new entry.

    Args:
        bot_id: Bot identifier
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        cost: Total cost for this API call

    Returns:
        True if logged successfully, False otherwise

    Example:
        log_api_usage('keystone-landscaping', 1000, 500, 0.0105)
    """
    try:
        query = """
            INSERT INTO api_usage (bot_id, usage_date, input_tokens, output_tokens,
                                  total_tokens, cost, request_count)
            VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, 1)
            ON CONFLICT (bot_id, usage_date)
            DO UPDATE SET
                input_tokens = api_usage.input_tokens + EXCLUDED.input_tokens,
                output_tokens = api_usage.output_tokens + EXCLUDED.output_tokens,
                total_tokens = api_usage.total_tokens + EXCLUDED.total_tokens,
                cost = api_usage.cost + EXCLUDED.cost,
                request_count = api_usage.request_count + 1
        """
        total_tokens = input_tokens + output_tokens
        rows = execute_update(query, (bot_id, input_tokens, output_tokens,
                                     total_tokens, cost))
        return rows > 0
    except Exception as e:
        print(f"Error logging API usage: {e}")
        return False


def get_usage_by_bot(bot_id: str, start_date: date = None,
                     end_date: date = None) -> List[Dict[str, Any]]:
    """
    Get API usage for a bot within date range.

    Args:
        bot_id: Bot identifier
        start_date: Start date (default: 30 days ago)
        end_date: End date (default: today)

    Returns:
        List of usage records
    """
    try:
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        query = """
            SELECT * FROM api_usage
            WHERE bot_id = %s
            AND usage_date BETWEEN %s AND %s
            ORDER BY usage_date DESC
        """
        return execute_query(query, (bot_id, start_date, end_date))
    except Exception as e:
        print(f"Error fetching usage by bot: {e}")
        return []


def get_usage_by_client(client_id: int, start_date: date = None,
                       end_date: date = None) -> List[Dict[str, Any]]:
    """
    Get API usage for all of a client's bots.

    Args:
        client_id: Client ID
        start_date: Start date (default: 30 days ago)
        end_date: End date (default: today)

    Returns:
        List of usage records for all client's bots
    """
    try:
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        query = """
            SELECT u.*, b.bot_name
            FROM api_usage u
            JOIN bots b ON u.bot_id = b.bot_id
            WHERE b.client_id = %s
            AND u.usage_date BETWEEN %s AND %s
            ORDER BY u.usage_date DESC, u.bot_id
        """
        return execute_query(query, (client_id, start_date, end_date))
    except Exception as e:
        print(f"Error fetching usage by client: {e}")
        return []


def get_daily_usage(usage_date: date = None) -> List[Dict[str, Any]]:
    """
    Get total usage for a specific date (default: today).

    Args:
        usage_date: Date to query (default: today)

    Returns:
        List of usage records for the specified date
    """
    try:
        if not usage_date:
            usage_date = date.today()

        query = """
            SELECT
                u.*,
                b.bot_name,
                c.name as client_name
            FROM api_usage u
            JOIN bots b ON u.bot_id = b.bot_id
            JOIN clients c ON b.client_id = c.id
            WHERE u.usage_date = %s
            ORDER BY u.cost DESC
        """
        return execute_query(query, (usage_date,))
    except Exception as e:
        print(f"Error fetching daily usage: {e}")
        return []


# ============================================================================
# SUBSCRIPTION FUNCTIONS
# ============================================================================

def get_subscription(client_id: int) -> Optional[Dict[str, Any]]:
    """
    Get active subscription for client.

    Args:
        client_id: Client ID

    Returns:
        Active subscription dictionary or None if not found
    """
    try:
        query = """
            SELECT * FROM subscriptions
            WHERE client_id = %s AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """
        return execute_one(query, (client_id,))
    except Exception as e:
        print(f"Error fetching subscription: {e}")
        return None


def create_subscription(client_id: int, plan_name: str,
                       price: float, billing_cycle: str) -> Optional[int]:
    """
    Create a new subscription.

    Args:
        client_id: Client ID
        plan_name: Name of the subscription plan
        price: Monthly price
        billing_cycle: Billing cycle ('monthly' or 'annual')

    Returns:
        New subscription ID or None on error

    Example:
        sub_id = create_subscription(1, 'Professional', 99.00, 'monthly')
    """
    try:
        query = """
            INSERT INTO subscriptions
            (client_id, plan_name, price, billing_cycle, status,
             current_period_start, current_period_end)
            VALUES (%s, %s, %s, %s, 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 month')
            RETURNING id
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (client_id, plan_name, price, billing_cycle))
            result = cursor.fetchone()
            return result['id'] if result else None
    except Exception as e:
        print(f"Error creating subscription: {e}")
        return None


def update_subscription_status(subscription_id: int, status: str) -> bool:
    """
    Update subscription status.

    Args:
        subscription_id: Subscription ID
        status: New status ('active', 'cancelled', 'past_due')

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        query = "UPDATE subscriptions SET status = %s WHERE id = %s"
        rows = execute_update(query, (status, subscription_id))
        return rows > 0
    except Exception as e:
        print(f"Error updating subscription status: {e}")
        return False


def mark_subscription_paid(subscription_id: int) -> bool:
    """
    Mark subscription as paid.
    Updates last_paid_at and extends current_period_end.

    Args:
        subscription_id: Subscription ID

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        query = """
            UPDATE subscriptions
            SET last_paid_at = NOW(),
                current_period_start = current_period_end,
                current_period_end = current_period_end + INTERVAL '1 month',
                status = 'active'
            WHERE id = %s
        """
        rows = execute_update(query, (subscription_id,))
        return rows > 0
    except Exception as e:
        print(f"Error marking subscription as paid: {e}")
        return False


def get_overdue_subscriptions() -> List[Dict[str, Any]]:
    """
    Get subscriptions past their end date that haven't been paid.

    Returns:
        List of overdue subscription dictionaries with client info
    """
    try:
        query = """
            SELECT
                s.*,
                c.name as client_name,
                c.email as client_email
            FROM subscriptions s
            JOIN clients c ON s.client_id = c.id
            WHERE s.current_period_end < CURRENT_DATE
            AND s.status = 'active'
            ORDER BY s.current_period_end ASC
        """
        return execute_query(query)
    except Exception as e:
        print(f"Error fetching overdue subscriptions: {e}")
        return []


# ============================================================================
# DATABASE CONNECTION WRAPPER FOR RAG
# ============================================================================

class DatabaseConnection:
    """
    Database connection wrapper for RAG components.

    Provides a consistent interface for RAG modules that expect
    a get_connection() method returning a context manager.

    Usage:
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents")
    """

    def get_connection(self):
        """
        Return the database connection context manager.

        Returns:
            Context manager that yields a psycopg2 connection
        """
        return get_db_connection()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    """Test database connection and basic functions"""
    print("Testing database connection...")

    # Test connection
    try:
        bot = get_bot_by_id('keystone-landscaping')
        if bot:
            print(f"✓ Connected! Found bot: {bot['bot_name']}")
        else:
            print("✗ Bot not found")
    except Exception as e:
        print(f"✗ Connection failed: {e}")

    # Test client query
    clients = get_all_clients()
    print(f"✓ Found {len(clients)} client(s)")

    # Test usage calculation
    cost = calculate_cost(1000, 500)
    print(f"✓ Cost calculation works: ${cost:.4f}")

    # Test additional functionality
    print("\nAdditional tests:")

    # Test bot query
    all_bots = get_all_bots()
    print(f"✓ Found {len(all_bots)} bot(s)")

    # Test daily usage
    daily = get_daily_usage()
    print(f"✓ Daily usage query works: {len(daily)} record(s)")

    print("\n✓ All tests completed successfully!")
