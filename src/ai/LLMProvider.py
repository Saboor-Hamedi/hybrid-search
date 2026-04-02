from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

class LLMProvider(ABC):
    """
    Abstract Base Class for all LLM Providers.
    Ensures that every client implements core generation primitives.
    """

    @abstractmethod
    def generate_response(self, prompt: str, system_instruction: str = "You are a helpful assistant.", **kwargs) -> str:
        """
        Takes a user prompt and returns a full response from the AI.
        """
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, system_instruction: str = "You are a helpful assistant.", **kwargs):
        """
        Yields chunks of text as they arrive from the AI provider.
        """
        pass

    def generate_rag_response(self, query: str, contexts: List[Dict[str, str]]) -> str:
        """
        Standardized RAG generation for all providers.
        """
        context_block, system_instruction = self._prepare_rag_prompt(query, contexts)
        return self.generate_response(
            prompt=f"Context Data:\n{context_block}\n\nUser Question: {query}",
            system_instruction=system_instruction,
            temperature=0.3
        )

    def generate_rag_stream(self, query: str, contexts: List[Dict[str, str]]):
        """
        Standardized Streaming RAG generation for all providers.
        """
        context_block, system_instruction = self._prepare_rag_prompt(query, contexts)
        return self.generate_stream(
            prompt=f"Context Data:\n{context_block}\n\nUser Question: {query}",
            system_instruction=system_instruction,
            temperature=0.3
        )

    def _prepare_rag_prompt(self, query: str, contexts: List[Dict[str, str]]) -> Tuple[str, str]:
        """Shared logic for RAG prompt construction."""
        context_block = ""
        for i, item in enumerate(contexts):
            context_block += f"DOC_ID: {item.get('doc_id')} (Search Rank: {i+1})\nCONTENT: {item.get('content')}\n\n"
        
        system_instruction = (
            "You are an expert Academic Research Assistant. "
            "Your task is to critically evaluate the provided Context Sources and synthesize a comprehensive, high-quality answer. "
            "Think deeply about the connections between the documents. "
            "Use **Markdown** for formatting (structure with headers, bold terms). "
            "Cite sources inline strictly using the format `[Doc ID]` (e.g., [Doc 123]). "
            "Structure your response as follows:\n"
            "1. **Synthesis**: A rigorous, academic-quality answer identifying key findings.\n"
            "2. **Evaluation**: A concluding paragraph starting with 'In my analysis,' where you critically assess the quality and relevance of the sources used (especially the Best Source).\n"
            "CRITICAL: At the very end, on a new line, add the tag: `BEST_SOURCE_ID: <ID>` for the single most authoritative document. "
            "Do NOT show this ID anywhere else."
        )
        return context_block, system_instruction

    def get_model_info(self) -> str:
        """
        Optional: Returns metadata about the provider and model.
        """
        return "Unknown Provider"