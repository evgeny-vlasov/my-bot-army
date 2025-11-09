from typing import List, Optional, Dict, Any
import httpx
from app.schemas.conversation import Message
from app.schemas.bot import Bot


class ClaudeService:
    """Service for interacting with Anthropic Claude API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def get_response(
        self,
        bot: Bot,
        conversation_history: List[Message],
        user_message: str,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get response from Claude API.

        Returns:
            Dict with 'content' (response text) and 'usage' (token counts)
        """
        # Build messages array from conversation history
        messages = []

        # Add conversation history (limit to last 20 messages to stay within context)
        history_messages = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
        for msg in history_messages:
            if msg.role in ["user", "assistant"]:  # Skip system messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Prepare system prompt
        system_prompt = bot.system_prompt

        # If we have RAG context, add it to system prompt
        if context:
            system_prompt += f"\n\nRelevant context from knowledge base:\n{context}"

        # Get config from bot
        config = bot.config or {}
        model = config.get("model", "claude-sonnet-4-20250514")
        max_tokens = config.get("max_tokens", 1000)
        temperature = config.get("temperature", 0.7)

        # Make API request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_prompt,
                    "messages": messages,
                }
            )

            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")

            data = response.json()

            return {
                "content": data["content"][0]["text"],
                "usage": data.get("usage", {}),
            }
