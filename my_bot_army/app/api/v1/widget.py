from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

router = APIRouter()

# Path to the widget JavaScript file
WIDGET_JS_PATH = Path(__file__).parent.parent.parent.parent.parent / "shared" / "widget" / "bot-widget.js"


@router.get("/widget.js")
async def get_widget_js():
    """
    Serve the embeddable chat widget JavaScript file.

    This file can be embedded on any website using:
    <script src="https://botfarm.qzz.io/widget.js" data-bot-id="therapist" async></script>
    """
    return FileResponse(
        path=WIDGET_JS_PATH,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Access-Control-Allow-Origin": "*"  # Allow cross-origin requests
        }
    )


@router.get("/chat-widget/{bot_id}", response_class=HTMLResponse)
async def chat_widget(bot_id: int):
    """
    Simple HTML chat widget for testing bots.

    Embed this in a webpage to test your bot.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat Widget - Bot {bot_id}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
            }}
            #chat-container {{
                border: 1px solid #ccc;
                height: 400px;
                overflow-y: auto;
                padding: 10px;
                margin-bottom: 10px;
                background: #f9f9f9;
            }}
            .message {{
                margin: 10px 0;
                padding: 8px;
                border-radius: 5px;
            }}
            .user {{
                background: #007bff;
                color: white;
                text-align: right;
            }}
            .bot {{
                background: #e9ecef;
                color: black;
            }}
            #input-container {{
                display: flex;
                gap: 10px;
            }}
            #message-input {{
                flex: 1;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            #send-button {{
                padding: 10px 20px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
            #send-button:hover {{
                background: #0056b3;
            }}
        </style>
    </head>
    <body>
        <h2>Chat with Bot {bot_id}</h2>
        <div id="chat-container"></div>
        <div id="input-container">
            <input type="text" id="message-input" placeholder="Type your message...">
            <button id="send-button">Send</button>
        </div>

        <script>
            const botId = {bot_id};
            let conversationId = null;

            const chatContainer = document.getElementById('chat-container');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');

            // Initialize conversation
            async function initConversation() {{
                const response = await fetch('/api/v1/conversations/', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        bot_id: botId,
                        source: 'web_widget'
                    }})
                }});
                const data = await response.json();
                conversationId = data.id;
            }}

            // Send message
            async function sendMessage() {{
                const message = messageInput.value.trim();
                if (!message) return;

                if (!conversationId) {{
                    await initConversation();
                }}

                // Display user message
                addMessage(message, 'user');
                messageInput.value = '';

                // Send to API
                const response = await fetch('/api/v1/conversations/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        conversation_id: conversationId,
                        message: message
                    }})
                }});

                const data = await response.json();
                addMessage(data.bot_message.content, 'bot');
            }}

            // Add message to chat
            function addMessage(text, role) {{
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${{role}}`;
                messageDiv.textContent = text;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }}

            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {{
                if (e.key === 'Enter') sendMessage();
            }});

            // Initialize on load
            initConversation();
        </script>
    </body>
    </html>
    """
    return html_content
