import anthropic
from typing import List, Dict, Optional
try:
    from .LLMProvider import LLMProvider
except ImportError:
    from LLMProvider import LLMProvider

class ClaudeClient(LLMProvider):
    """
    Advanced Claude Client implementation.
    Integrates with Anthropic's 'Messages' API.
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_response(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Sends a prompt to Anthropic Claude and returns the text response."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_instruction,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Claude Error: {str(e)}"

    def generate_stream(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1024):
        """Yields chunks of text as they arrive from Anthropic."""
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_instruction,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"Claude Stream Error: {str(e)}"

    def get_model_info(self) -> str:
        return f"Provider: Anthropic | Model: {self.model}"