"""
Claude API Client
Reusable wrapper for Anthropic Claude API
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from /opt/bot-farm/.env
# This path works for production deployment
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)


class ClaudeClient:
    """
    Wrapper class for interacting with Anthropic's Claude API
    """

    def __init__(self):
        """
        Initialize the Claude client with API key from environment variables
        """
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please check your .env file."
            )

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 1024

    def chat(self, message, system_prompt, conversation_history=None):
        """
        Send a message to Claude and get a response

        Args:
            message (str): The user's message
            system_prompt (str): System prompt defining bot behavior
            conversation_history (list, optional): List of previous messages
                Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Returns:
            str: Claude's text response

        Raises:
            Exception: If API call fails
        """
        # Initialize conversation history if not provided
        if conversation_history is None:
            conversation_history = []

        # Create a copy to avoid modifying the original
        messages = list(conversation_history)

        # Append the current user message
        messages.append({
            "role": "user",
            "content": message
        })

        # Make API call to Claude
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )

            # Extract and return the text response
            return response.content[0].text

        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Claude API error: {str(e)}")
