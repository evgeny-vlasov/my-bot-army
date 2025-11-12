"""
Keystone Hardscapes Bot - Flask Application

Main Flask application for the Keystone Hardscapes AI chatbot.
Provides API endpoints for chat functionality and serves the widget.
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Add the parent directory to the path so we can import from shared/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.claude_client import ClaudeClient
from config import Config
from prompts import SYSTEM_PROMPT

# Import RAG components
try:
    from shared.rag import VoyageClient, RAGRetriever
    from shared.database import DatabaseConnection
    import rag_config
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Warning: RAG modules not available: {e}")
    RAG_AVAILABLE = False

# Import database functions for conversation logging
try:
    from shared.database import (
        get_bot_by_id,
        create_conversation,
        save_message,
        get_conversation_history,
        execute_query
    )
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Warning: Database module not available: {e}")
    DATABASE_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for cross-origin requests
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize Claude client with bot_id for usage tracking
try:
    claude_client = ClaudeClient(bot_id=Config.BOT_ID)
    print(f"✓ Claude client initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Claude client: {e}")
    print(f"  Please check your .env file and ANTHROPIC_API_KEY")
    sys.exit(1)

# Initialize RAG components
rag_retriever = None
if RAG_AVAILABLE and rag_config.get_rag_enabled():
    try:
        voyage_client = VoyageClient(model=rag_config.VOYAGE_MODEL)
        db_connection = DatabaseConnection()
        rag_retriever = RAGRetriever(voyage_client, db_connection)
        print(f"✓ RAG system initialized (model: {rag_config.VOYAGE_MODEL})")
    except Exception as e:
        print(f"⚠ Warning: Failed to initialize RAG: {e}")
        print(f"  Bot will run without RAG functionality")
        rag_retriever = None
else:
    if not RAG_AVAILABLE:
        print(f"⚠ RAG not available - missing dependencies")
    else:
        print(f"⚠ RAG disabled in configuration")

# Verify bot exists in database on startup
if DATABASE_AVAILABLE:
    try:
        bot_info = get_bot_by_id(Config.BOT_ID)
        if bot_info:
            print(f"✓ Bot '{bot_info['bot_name']}' connected to database")
        else:
            print(f"⚠ Warning: Bot '{Config.BOT_ID}' not found in database")
    except Exception as e:
        print(f"⚠ Warning: Could not verify bot in database: {e}")
else:
    print(f"⚠ Database logging disabled - bot will run without persistence")


@app.route('/', methods=['GET'])
def home():
    """
    Welcome endpoint - confirms the bot is running
    """
    return jsonify({
        'message': 'Keystone Hardscapes Bot API',
        'status': 'running',
        'bot_id': Config.BOT_ID,
        'bot_name': Config.BOT_NAME
    })


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint for monitoring
    """
    return jsonify({
        'status': 'healthy',
        'bot': Config.BOT_ID
    })


@app.route('/test', methods=['GET'])
def serve_test_page():
    """
    Serve a test page for the widget
    """
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Widget Test - Keystone Hardscapes</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .demo-box {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #2563eb; }
        .status {
            background: #e0f2fe;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border: 2px solid #2563eb;
        }
        .error { background: #fef2f2; border-color: #dc2626; color: #dc2626; }
        .success { background: #f0fdf4; border-color: #16a34a; color: #16a34a; }
        ul { line-height: 1.8; }
        #console {
            margin-top: 20px;
            padding: 10px;
            background: #1f2937;
            color: #10b981;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-line { margin: 2px 0; }
        .log-error { color: #ef4444; }
        .log-warn { color: #f59e0b; }
        .log-success { color: #10b981; }
    </style>
</head>
<body>
    <div class="demo-box">
        <h1>🔧 Widget Debug Test</h1>
        <p>This page tests the chat widget and displays detailed debugging information.</p>

        <div id="status" class="status">
            ⏳ Loading widget...
        </div>

        <p><strong>What to check:</strong></p>
        <ul>
            <li>Widget script should load without errors</li>
            <li>Chat bubble should appear in bottom-right corner</li>
            <li>Console below shows debugging information</li>
        </ul>

        <div id="console"></div>
    </div>

    <script>
        const consoleDiv = document.getElementById('console');
        const statusDiv = document.getElementById('status');

        function log(message, type = 'info') {
            const time = new Date().toLocaleTimeString();
            const className = type === 'error' ? 'log-error' : type === 'warn' ? 'log-warn' : type === 'success' ? 'log-success' : '';
            consoleDiv.innerHTML += `<div class="log-line ${className}">[${time}] ${message}</div>`;
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
            console.log(message);
        }

        // Capture console errors
        window.onerror = function(msg, url, line, col, error) {
            log(`ERROR: ${msg} at ${url}:${line}:${col}`, 'error');
            statusDiv.className = 'status error';
            statusDiv.innerHTML = '❌ JavaScript error occurred - check console below';
        };

        log('Page loaded');
        log('Loading widget.js from: ' + window.location.origin + '/widget.js');

        // Store original error handler
        const originalOnError = window.onerror;

        // Track if widget script loaded
        window.widgetScriptLoaded = false;
    </script>

    <script src="/widget.js" onerror="log('ERROR: widget.js failed to load!', 'error')" onload="window.widgetScriptLoaded = true; log('widget.js file loaded successfully');"></script>

    <script>
        log('Widget script tag processed');
        log('widgetScriptLoaded: ' + window.widgetScriptLoaded);

        function initWidget() {
            log('Checking for BotWidget...');

            if (typeof BotWidget === 'undefined') {
                log('BotWidget not found, retrying in 100ms...', 'warn');
                setTimeout(initWidget, 100);
                return;
            }

            log('BotWidget object found!', 'success');

            try {
                BotWidget.init({
                    apiUrl: window.location.origin,
                    botId: 'keystone-landscaping',
                    position: 'bottom-right',
                    primaryColor: '#2563eb',
                    title: 'Chat with Keystone'
                });

                log('BotWidget.init() called successfully', 'success');

                setTimeout(() => {
                    const bubble = document.querySelector('.bot-widget-bubble');
                    const chatWindow = document.querySelector('.bot-widget-window');

                    if (bubble) {
                        log('✓ Chat bubble found in DOM!', 'success');
                        log('Bubble visible: ' + (bubble.offsetParent !== null), 'success');
                        statusDiv.className = 'status success';
                        statusDiv.innerHTML = '✅ Widget loaded successfully! Look for the chat bubble in the bottom-right corner.';
                    } else {
                        log('✗ Chat bubble NOT found in DOM', 'error');
                        statusDiv.className = 'status error';
                        statusDiv.innerHTML = '❌ Widget initialized but bubble not created';
                    }

                    if (chatWindow) {
                        log('✓ Chat window found in DOM', 'success');
                    }
                }, 500);

            } catch (error) {
                log('ERROR initializing widget: ' + error.message, 'error');
                statusDiv.className = 'status error';
                statusDiv.innerHTML = '❌ Error: ' + error.message;
            }
        }

        // Start initialization
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initWidget);
        } else {
            initWidget();
        }
    </script>
</body>
</html>'''
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/widget.js', methods=['GET'])
def serve_widget():
    """
    Serve the JavaScript widget file
    """
    try:
        widget_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../shared/widget/bot-widget.js')
        )

        if not os.path.exists(widget_path):
            return jsonify({
                'error': 'Widget file not found'
            }), 404

        response = send_file(
            widget_path,
            mimetype='application/javascript'
        )
        # Add cache control headers to prevent stale cached versions
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error serving widget: {e}")
        return jsonify({
            'error': 'Failed to serve widget'
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint - processes user messages and returns bot responses
    with database logging for conversations and messages

    Request body:
        {
            "message": str,
            "conversation_history": list (optional),
            "session_id": str (optional)
        }

    Response:
        {
            "response": str,
            "status": "success"
        }
    """
    try:
        # Parse request data
        data = request.get_json()

        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400

        # Validate message field
        message = data.get('message')
        if not message:
            return jsonify({
                'error': 'Message field is required',
                'status': 'error'
            }), 400

        if not isinstance(message, str):
            return jsonify({
                'error': 'Message must be a string',
                'status': 'error'
            }), 400

        # Check message length
        if len(message) > Config.MAX_MESSAGE_LENGTH:
            return jsonify({
                'error': f'Message too long (max {Config.MAX_MESSAGE_LENGTH} characters)',
                'status': 'error'
            }), 400

        # Get conversation history and session_id
        conversation_history = data.get('conversation_history', [])
        session_id = data.get('session_id')

        # Validate conversation history format
        if not isinstance(conversation_history, list):
            return jsonify({
                'error': 'Conversation history must be a list',
                'status': 'error'
            }), 400

        # Validate each message in history
        for msg in conversation_history:
            if not isinstance(msg, dict):
                return jsonify({
                    'error': 'Each message in history must be an object',
                    'status': 'error'
                }), 400

            if 'role' not in msg or 'content' not in msg:
                return jsonify({
                    'error': 'Each message must have "role" and "content" fields',
                    'status': 'error'
                }), 400

            if msg['role'] not in ['user', 'assistant']:
                return jsonify({
                    'error': 'Message role must be "user" or "assistant"',
                    'status': 'error'
                }), 400

        # Trim conversation history to prevent context overflow
        if len(conversation_history) > Config.MAX_CONVERSATION_HISTORY:
            conversation_history = conversation_history[-Config.MAX_CONVERSATION_HISTORY:]

        # Get or create conversation in database
        conversation_id = None
        if session_id and DATABASE_AVAILABLE:
            try:
                user_ip = request.remote_addr
                conversation_id = create_conversation(Config.BOT_ID, session_id, user_ip)
            except Exception as db_error:
                print(f"Warning: Could not create conversation: {db_error}")

        # Save user message to database
        if conversation_id and DATABASE_AVAILABLE:
            try:
                save_message(conversation_id, 'user', message)
            except Exception as db_error:
                print(f"Warning: Could not save user message: {db_error}")

        # RAG: Search knowledge base for relevant context
        context_chunks = []
        enhanced_system_prompt = SYSTEM_PROMPT

        if rag_retriever:
            try:
                # Search for relevant chunks
                context, chunks = rag_retriever.get_context_for_query(
                    bot_id=Config.BOT_ID,
                    query=message,
                    top_k=rag_config.TOP_K_CHUNKS,
                    similarity_threshold=rag_config.SIMILARITY_THRESHOLD,
                    max_tokens=rag_config.MAX_CONTEXT_TOKENS
                )

                # If we found relevant context, enhance the system prompt
                if context and chunks:
                    enhanced_system_prompt = (
                        f"{SYSTEM_PROMPT}\n\n"
                        f"{rag_config.RAG_SYSTEM_INSTRUCTION}\n\n"
                        f"{context}"
                    )
                    context_chunks = chunks
                    print(f"RAG: Found {len(chunks)} relevant chunks")
                else:
                    print(f"RAG: No relevant chunks found (threshold: {rag_config.SIMILARITY_THRESHOLD})")

            except Exception as rag_error:
                print(f"Warning: RAG search failed: {rag_error}")
                # Continue without RAG if it fails

        # Call Claude API with (possibly enhanced) system prompt
        try:
            response = claude_client.chat(
                message=message,
                system_prompt=enhanced_system_prompt,
                conversation_history=conversation_history
            )

            # Save assistant response to database (with context chunks if available)
            if conversation_id and DATABASE_AVAILABLE:
                try:
                    # Prepare context chunks for storage
                    if rag_config.LOG_CONTEXT_CHUNKS and context_chunks:
                        chunks_json = json.dumps([
                            {
                                'chunk_id': chunk['chunk_id'],
                                'document_id': chunk['document_id'],
                                'document_title': chunk['document_title'],
                                'similarity': chunk['similarity'],
                                'source': chunk.get('source', '')
                            }
                            for chunk in context_chunks
                        ])

                        # Save with context_chunks (requires updated save_message function)
                        # For now, save normally - can enhance later
                        save_message(conversation_id, 'assistant', response)
                    else:
                        save_message(conversation_id, 'assistant', response)

                except Exception as db_error:
                    print(f"Warning: Could not save assistant message: {db_error}")

            return jsonify({
                'response': response,
                'status': 'success'
            })

        except Exception as api_error:
            print(f"Claude API error: {api_error}")
            return jsonify({
                'error': 'Failed to get response from AI service',
                'status': 'error'
            }), 500

    except Exception as e:
        print(f"Unexpected error in /api/chat: {e}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'status': 'error'
        }), 500


@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """
    Get bot statistics for admin dashboard

    Note: In production, this should require authentication!

    Response:
        {
            "bot_id": str,
            "today_usage": dict,
            "total_conversations": int,
            "total_messages": int,
            "status": "success"
        }
    """
    if not DATABASE_AVAILABLE:
        return jsonify({
            'error': 'Database not available',
            'status': 'error'
        }), 503

    try:
        # Get today's usage
        today_usage = execute_query("""
            SELECT
                requests,
                input_tokens,
                output_tokens,
                cost
            FROM api_usage
            WHERE bot_id = %s AND date = CURRENT_DATE
        """, (Config.BOT_ID,))

        # Get total conversations
        total_conversations = execute_query("""
            SELECT COUNT(*) as count
            FROM conversations
            WHERE bot_id = %s
        """, (Config.BOT_ID,))

        # Get total messages
        total_messages = execute_query("""
            SELECT COUNT(*) as count
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.bot_id = %s
        """, (Config.BOT_ID,))

        return jsonify({
            'bot_id': Config.BOT_ID,
            'today_usage': today_usage[0] if today_usage else None,
            'total_conversations': total_conversations[0]['count'] if total_conversations else 0,
            'total_messages': total_messages[0]['count'] if total_messages else 0,
            'status': 'success'
        })

    except Exception as e:
        print(f"Error in /admin/stats: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors
    """
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors
    """
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500


if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"  {Config.BOT_NAME}")
    print(f"{'='*60}")
    print(f"Bot ID:    {Config.BOT_ID}")
    print(f"Host:      {Config.HOST}")
    print(f"Port:      {Config.PORT}")
    print(f"Debug:     {Config.DEBUG}")
    print(f"{'='*60}\n")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
