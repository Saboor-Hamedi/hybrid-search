from google import genai
from typing import List, Dict, Optional
try:
    from .LLMProvider import LLMProvider
except ImportError:
    from LLMProvider import LLMProvider

class GeminiClient(LLMProvider):
    """
    Advanced Gemini Client implementation.
    Uses the new 'google-genai' SDK (2026 standard).
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        # The new SDK uses a unified Client object
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_response(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Sends a request to Google Gemini and returns the full text content."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    'system_instruction': system_instruction,
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                }
            )
            return response.text if response.text else "Gemini Error: No text returned."
        except Exception as e:
            return f"Gemini Error: {str(e)}"

    def generate_stream(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1024):
        """Yields chunks of text as they arrive from Google Gemini 2."""
        try:
            stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config={
                    'system_instruction': system_instruction,
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                }
            )
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Gemini Stream Error: {str(e)}"

    def get_model_info(self) -> str:
        return f"Provider: Google | Model: {self.model}"