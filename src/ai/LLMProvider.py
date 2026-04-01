from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Abstract Base Class for all LLM Providers.
    Ensures that every client implements the 'generate_response' method.
    """

    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Takes a user prompt and returns a full response from the AI.
        """
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs):
        """
        Yields chunks of text as they arrive from the AI provider.
        """
        pass

    def get_model_info(self) -> str:
        """
        Optional: Returns metadata about the provider and model.
        """
        return "Unknown Provider"