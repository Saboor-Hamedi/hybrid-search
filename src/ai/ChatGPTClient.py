import openai
from typing import List, Dict, Optional
try:
    from .LLMProvider import LLMProvider
except ImportError:
    from LLMProvider import LLMProvider

class ChatGPTClient(LLMProvider):
    """
    Advanced ChatGPT Client implementation.
    Integrates with OpenAI's official API.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        # Default OpenAI client (no custom base_url needed)
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def _prepare_messages(self, prompt: str, system_instruction: str = "You are a helpful assistant.") -> List[Dict[str, str]]:
        """
        Formats the prompt into the OpenAI message structure.
        Includes a system role for better steerability.
        """
        return [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

    def generate_response(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Sends the prompt to OpenAI and returns the text response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._prepare_messages(prompt, system_instruction),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Client Error: {str(e)}"

    def generate_stream(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1000):
        """Yields chunks of text as they arrive from OpenAI."""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self._prepare_messages(prompt, system_instruction),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Stream Error: {str(e)}"

    def get_model_info(self) -> str:
        return f"Provider: OpenAI | Model: {self.model}"