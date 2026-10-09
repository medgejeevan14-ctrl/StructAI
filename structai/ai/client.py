"""
Anthropic API Client Wrapper for StructAI AI Layer.
Loads ANTHROPIC_API_KEY safely from os.environ.
"""

import os
from typing import Optional


class StructAIAIClientError(Exception):
    """Base exception for StructAI AI client errors."""
    pass


class StructAIConfigurationError(StructAIAIClientError):
    """Raised when ANTHROPIC_API_KEY environment variable is missing."""
    pass


class AnthropicAIClient:
    """
    Wrapper around official Anthropic SDK client.
    Strictly loads API key from environment variable ANTHROPIC_API_KEY.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise StructAIConfigurationError(
                "Environment variable 'ANTHROPIC_API_KEY' is not set. "
                "Please configure ANTHROPIC_API_KEY in your environment before invoking AI explanation features."
            )
        
        self._api_key = key
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=key)
        except ImportError:
            raise StructAIAIClientError(
                "The 'anthropic' Python package is required for AI features. "
                "Install it via: pip install anthropic"
            )

    def generate_message(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> str:
        """
        Sends message request to Anthropic Claude API.
        """
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if not response or not getattr(response, "content", None):
                raise StructAIAIClientError("Received empty response payload from Anthropic API.")
            
            first_content = response.content[0]
            if hasattr(first_content, "text"):
                return first_content.text
            return str(first_content)
        except Exception as e:
            if isinstance(e, StructAIAIClientError):
                raise
            error_msg = str(e)
            if self._api_key and self._api_key in error_msg:
                error_msg = error_msg.replace(self._api_key, "[REDACTED_API_KEY]")
            raise StructAIAIClientError(f"Anthropic API request failed: {error_msg}")
