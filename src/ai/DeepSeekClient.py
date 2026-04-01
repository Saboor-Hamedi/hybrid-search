import openai
from typing import List, Dict
try:
    from .LLMProvider import LLMProvider
except ImportError:
    from LLMProvider import LLMProvider

class DeepSeekClient(LLMProvider):
    """
    Advanced DeepSeek Client implementation using OOP.
    Connects via the OpenAI-compatible API architecture.
    """

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.client = openai.OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com"
        )
        self.model = model
        self.history: List[Dict[str, str]] = []

    def _prepare_messages(self, prompt: str, system_instruction: str) -> List[Dict[str, str]]:
        """Internal helper to manage chat history/context."""
        return [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

    def generate_response(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Sends a prompt to DeepSeek and returns the string response."""
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
            return f"DeepSeek Error: {str(e)}"

    def generate_stream(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1024):
        """Yields chunks of text as they arrive from DeepSeek."""
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
            yield f"DeepSeek Stream Error: {str(e)}"

    def get_model_info(self) -> str:
        """Returns metadata about the current instance."""
        return f"Provider: DeepSeek | Model: {self.model}"