"""
Keystone Hardscapes Bot - Flask Application

Main Flask application for the Keystone Hardscapes AI chatbot.
Provides API endpoints for chat functionality and serves the widget.
"""

import os
import sys
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Add the parent directory to the path so we can import from shared/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.claude_client import ClaudeClient
from config import Config
from prompts import SYSTEM_PROMPT

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for cross-origin requests
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize Claude client
try:
    claude_client = ClaudeClient()
    print(f"✓ Claude client initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Claude client: {e}")
    print(f"  Please check your .env file and ANTHROPIC_API_KEY")
    sys.exit(1)


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

        return send_file(
            widget_path,
            mimetype='application/javascript'
        )
    except Exception as e:
        print(f"Error serving widget: {e}")
        return jsonify({
            'error': 'Failed to serve widget'
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint - processes user messages and returns bot responses

    Request body:
        {
            "message": str,
            "conversation_history": list (optional)
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

        # Get conversation history
        conversation_history = data.get('conversation_history', [])

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

        # Call Claude API
        try:
            response = claude_client.chat(
                message=message,
                system_prompt=SYSTEM_PROMPT,
                conversation_history=conversation_history
            )

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
