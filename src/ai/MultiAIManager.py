from typing import Dict
try:
    from .LLMProvider import LLMProvider
    from .ChatGPTClient import ChatGPTClient
    from .ClaudeClient import ClaudeClient
    from .DeepSeekClient import DeepSeekClient
    from .GeminiClient import GeminiClient
    from .OllamaClient import OllamaClient
except ImportError:
    from LLMProvider import LLMProvider
    from ChatGPTClient import ChatGPTClient
    from ClaudeClient import ClaudeClient
    from DeepSeekClient import DeepSeekClient
    from GeminiClient import GeminiClient

class MultiAIManager:
    """
    Orchestrates multiple LLM providers.
    Allows for structured comparison and parallel execution.
    """
    def __init__(self):
        self.clients: Dict[str, LLMProvider] = {}

    @staticmethod
    def create_client(provider_name: str, api_key: str = "", **kwargs) -> LLMProvider:
        """Centralized factory for instantiating clinical LLM providers."""
        name = provider_name.lower()
        if "chatgpt" in name: return ChatGPTClient(api_key)
        if "claude" in name: return ClaudeClient(api_key)
        if "deepseek" in name: return DeepSeekClient(api_key)
        if "gemini" in name: return GeminiClient(api_key)
        if "ollama" in name: return OllamaClient(model=kwargs.get("model", "qwen2.5:0.5b"), base_url=kwargs.get("base_url", "http://localhost:11434"))
        return None

    def add_client(self, name: str, client: LLMProvider):
        self.clients[name.lower()] = client

    def ask_all(self, prompt: str) -> Dict[str, str]:
        """Queries all registered clients and returns their responses."""
        results = {}
        for name, client in self.clients.items():
            results[name] = client.generate_response(prompt)
        return results

    def get_streaming_response(self, provider_name, prompt, **kwargs):
        """Streams the response from a specific clinical provider."""
        provider = str(provider_name).lower()
        if provider in self.clients:
            return self.clients[provider].generate_stream(prompt, **kwargs)
        return None

# --- SETUP & USAGE EXAMPLE ---
if __name__ == "__main__":
    manager = MultiAIManager()
    # Populate with keys if needed
    # manager.add_client("deepseek", DeepSeekClient(api_key="..."))
    # manager.add_client("gpt", ChatGPTClient(api_key="..."))
    # results = manager.ask_all("Hello World")
    # print(results)