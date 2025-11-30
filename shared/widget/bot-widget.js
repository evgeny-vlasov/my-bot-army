(function() {
  'use strict';

  // ============================================================================
  // CONFIGURATION
  // ============================================================================

  const scriptTag = document.currentScript || document.querySelector('script[data-bot-id]');
  if (!scriptTag) {
    console.warn('Bot widget: script tag not found');
    return;
  }

  const config = {
    botId: scriptTag.getAttribute('data-bot-id'),
    botName: scriptTag.getAttribute('data-bot-name') || 'Assistant',
    position: scriptTag.getAttribute('data-position') || 'bottom-right',
    theme: scriptTag.getAttribute('data-theme') || 'light',
    apiUrl: scriptTag.getAttribute('data-api-url') || ''
  };

  if (!config.botId) {
    console.warn('Bot widget: data-bot-id is required');
    return;
  }

  // ============================================================================
  // UTILITIES
  // ============================================================================

  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function getSessionId() {
    const storageKey = `bot_session_${config.botId}`;
    let sessionId = localStorage.getItem(storageKey);
    if (!sessionId) {
      sessionId = generateUUID();
      localStorage.setItem(storageKey, sessionId);
    }
    return sessionId;
  }

  // ============================================================================
  // CSS INJECTION
  // ============================================================================

  function injectStyles() {
    const isMobile = window.innerWidth < 480;
    const bubbleSize = isMobile ? '50px' : 'var(--bot-bubble-size, 60px)';

    const css = `
      :root {
        --bot-primary-color: #0066cc;
        --bot-text-color: #333;
        --bot-bg-color: #fff;
        --bot-bubble-size: 60px;
      }

      .bot-widget-container {
        position: fixed;
        ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
        bottom: 20px;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      }

      .bot-widget-bubble {
        width: ${bubbleSize};
        height: ${bubbleSize};
        border-radius: 50%;
        background: var(--bot-primary-color);
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
      }

      .bot-widget-bubble:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
      }

      .bot-widget-bubble svg {
        width: 60%;
        height: 60%;
        fill: white;
      }

      .bot-widget-window {
        display: none;
        flex-direction: column;
        position: fixed;
        ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
        bottom: 20px;
        width: ${isMobile ? '100%' : '380px'};
        height: ${isMobile ? '70vh' : '600px'};
        max-height: 90vh;
        ${isMobile ? 'left: 0; right: 0; margin: 0 auto;' : ''}
        background: var(--bot-bg-color);
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        overflow: hidden;
      }

      .bot-widget-window.open {
        display: flex;
      }

      .bot-widget-header {
        background: var(--bot-primary-color);
        color: white;
        padding: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .bot-widget-header h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }

      .bot-widget-close {
        background: none;
        border: none;
        color: white;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        min-height: 44px;
      }

      .bot-widget-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        background: ${config.theme === 'dark' ? '#1a1a1a' : '#f5f5f5'};
      }

      .bot-message, .user-message {
        margin-bottom: 12px;
        display: flex;
        align-items: flex-start;
      }

      .user-message {
        justify-content: flex-end;
      }

      .message-bubble {
        padding: 10px 14px;
        border-radius: 18px;
        max-width: 75%;
        word-wrap: break-word;
        line-height: 1.4;
      }

      .bot-message .message-bubble {
        background: white;
        color: var(--bot-text-color);
        border-bottom-left-radius: 4px;
      }

      .user-message .message-bubble {
        background: var(--bot-primary-color);
        color: white;
        border-bottom-right-radius: 4px;
      }

      .bot-widget-typing {
        display: none;
        padding: 10px 14px;
        background: white;
        border-radius: 18px;
        width: 60px;
        margin-bottom: 12px;
      }

      .bot-widget-typing.active {
        display: block;
      }

      .typing-dots {
        display: flex;
        gap: 4px;
        align-items: center;
      }

      .typing-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #999;
        animation: typing 1.4s infinite;
      }

      .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
      }

      .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
      }

      @keyframes typing {
        0%, 60%, 100% { opacity: 0.3; }
        30% { opacity: 1; }
      }

      .bot-widget-input-area {
        padding: 16px;
        background: var(--bot-bg-color);
        border-top: 1px solid ${config.theme === 'dark' ? '#333' : '#e0e0e0'};
        display: flex;
        gap: 8px;
      }

      .bot-widget-input {
        flex: 1;
        padding: 10px 14px;
        border: 1px solid ${config.theme === 'dark' ? '#444' : '#ddd'};
        border-radius: 20px;
        font-size: 14px;
        outline: none;
        background: ${config.theme === 'dark' ? '#2a2a2a' : 'white'};
        color: ${config.theme === 'dark' ? 'white' : 'var(--bot-text-color)'};
      }

      .bot-widget-input:focus {
        border-color: var(--bot-primary-color);
      }

      .bot-widget-send {
        background: var(--bot-primary-color);
        color: white;
        border: none;
        border-radius: 50%;
        width: 44px;
        height: 44px;
        min-width: 44px;
        min-height: 44px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: opacity 0.2s;
      }

      .bot-widget-send:hover:not(:disabled) {
        opacity: 0.9;
      }

      .bot-widget-send:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .bot-widget-send svg {
        width: 20px;
        height: 20px;
        fill: white;
      }

      .bot-widget-error {
        background: #fee;
        color: #c33;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 13px;
        margin-bottom: 12px;
      }

      @media (max-width: 480px) {
        .bot-widget-container {
          right: 10px;
          bottom: 10px;
        }

        .bot-widget-window {
          width: calc(100% - 20px) !important;
          right: 10px !important;
          left: 10px !important;
        }
      }
    `;

    const styleElement = document.createElement('style');
    styleElement.textContent = css;
    document.head.appendChild(styleElement);
  }

  // ============================================================================
  // HTML TEMPLATE
  // ============================================================================

  function createWidgetHTML() {
    const container = document.createElement('div');
    container.className = 'bot-widget-container';
    container.innerHTML = `
      <div class="bot-widget-bubble" id="bot-widget-bubble">
        <svg viewBox="0 0 24 24">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        </svg>
      </div>

      <div class="bot-widget-window" id="bot-widget-window">
        <div class="bot-widget-header">
          <h3>${escapeHTML(config.botName)}</h3>
          <button class="bot-widget-close" id="bot-widget-close" aria-label="Close chat">×</button>
        </div>

        <div class="bot-widget-messages" id="bot-widget-messages">
          <div class="bot-message">
            <div class="message-bubble">
              Hello! How can I help you today?
            </div>
          </div>
          <div class="bot-widget-typing" id="bot-widget-typing">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        <div class="bot-widget-input-area">
          <input
            type="text"
            class="bot-widget-input"
            id="bot-widget-input"
            placeholder="Type a message..."
            aria-label="Message input"
          />
          <button class="bot-widget-send" id="bot-widget-send" aria-label="Send message">
            <svg viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    `;

    return container;
  }

  // ============================================================================
  // API COMMUNICATION
  // ============================================================================

  async function sendMessage(message, sessionId) {
    const apiUrl = config.apiUrl || window.location.origin;
    const endpoint = `${apiUrl}/api/chat`;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
          bot_id: config.botId
        })
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'success' || data.response) {
        return { success: true, response: data.response };
      } else {
        throw new Error('Invalid API response format');
      }
    } catch (error) {
      console.warn('Bot widget API error:', error);
      return {
        success: false,
        error: 'Sorry, I\'m having trouble connecting. Please try again later.'
      };
    }
  }

  // ============================================================================
  // MESSAGE HANDLING
  // ============================================================================

  function addMessage(text, isUser) {
    const messagesContainer = document.getElementById('bot-widget-messages');
    const typingIndicator = document.getElementById('bot-widget-typing');

    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'user-message' : 'bot-message';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = escapeHTML(text);

    messageDiv.appendChild(bubble);
    messagesContainer.insertBefore(messageDiv, typingIndicator);

    // Auto-scroll to latest message
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function showTyping(show) {
    const typingIndicator = document.getElementById('bot-widget-typing');
    if (show) {
      typingIndicator.classList.add('active');
    } else {
      typingIndicator.classList.remove('active');
    }

    // Auto-scroll when showing typing indicator
    if (show) {
      const messagesContainer = document.getElementById('bot-widget-messages');
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  function showError(message) {
    const messagesContainer = document.getElementById('bot-widget-messages');
    const typingIndicator = document.getElementById('bot-widget-typing');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'bot-widget-error';
    errorDiv.textContent = message;

    messagesContainer.insertBefore(errorDiv, typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Remove error after 5 seconds
    setTimeout(() => {
      errorDiv.remove();
    }, 5000);
  }

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  function setupEventHandlers() {
    const bubble = document.getElementById('bot-widget-bubble');
    const window = document.getElementById('bot-widget-window');
    const closeBtn = document.getElementById('bot-widget-close');
    const input = document.getElementById('bot-widget-input');
    const sendBtn = document.getElementById('bot-widget-send');

    // Toggle chat window
    bubble.addEventListener('click', () => {
      window.classList.add('open');
      bubble.style.display = 'none';
      input.focus();
    });

    closeBtn.addEventListener('click', () => {
      window.classList.remove('open');
      bubble.style.display = 'flex';
    });

    // Send message function
    async function handleSendMessage() {
      const message = input.value.trim();
      if (!message) return;

      // Disable input while processing
      input.disabled = true;
      sendBtn.disabled = true;

      // Add user message
      addMessage(message, true);
      input.value = '';

      // Show typing indicator
      showTyping(true);

      // Send to API
      const sessionId = getSessionId();
      const result = await sendMessage(message, sessionId);

      // Hide typing indicator
      showTyping(false);

      // Handle response
      if (result.success) {
        addMessage(result.response, false);
      } else {
        showError(result.error);
      }

      // Re-enable input
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }

    // Send on button click
    sendBtn.addEventListener('click', handleSendMessage);

    // Send on Enter key
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        handleSendMessage();
      }
    });
  }

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  function initialize() {
    try {
      // Inject styles
      injectStyles();

      // Create and append widget
      const widget = createWidgetHTML();
      document.body.appendChild(widget);

      // Setup event handlers
      setupEventHandlers();

      console.log('Bot widget initialized successfully');
    } catch (error) {
      console.warn('Bot widget initialization failed:', error);
    }
  }

  // Wait for DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }

})();
