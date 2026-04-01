import requests
import json
import os
from typing import List, Dict, Optional
try:
    from .LLMProvider import LLMProvider
except ImportError:
    from LLMProvider import LLMProvider

class OllamaClient(LLMProvider):
    """
    Ollama Client implementation.
    Standardizes communication with various local Ollama models.
    """

    def __init__(self, model: str = "qwen2.5:0.5b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_generate = f"{self.base_url}/api/generate"

    def check_health(self) -> bool:
        """Verifies if the Ollama server is responsive."""
        try:
            res = requests.get(f"{self.base_url}/", timeout=1)
            return res.status_code == 200
        except:
            return False

    def generate_response(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Sends a request to the Ollama local API and returns the full response."""
        
        # Combine system instruction and prompt for Ollama's non-chat generate API
        # Better yet, Ollama has a /api/chat as well. 
        # But per the original llm_service.py, we were using /api/generate.
        
        full_prompt = f"System: {system_instruction}\n\nUser: {prompt}\n\nAnswer:"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,
                "num_predict": max_tokens
            }
        }

        try:
            response = requests.post(self.api_generate, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get("response", "Error: No response text found.")
            else:
                return f"Sync Error: Ollama API returned {response.status_code}"
        except Exception as e:
            return f"Client Execution Error: {str(e)}"

    def generate_stream(self, prompt: str, system_instruction: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1000):
        """Yields chunks of text as they arrive from the local Ollama instance."""
        
        full_prompt = f"System: {system_instruction}\n\nUser: {prompt}\n\nAnswer:"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,
                "num_predict": max_tokens
            }
        }

        try:
            response = requests.post(self.api_generate, json=payload, stream=True, timeout=60)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'response' in chunk:
                            yield chunk['response']
                        if chunk.get('done'):
                            break
            else:
                yield f"Stream Error: Ollama API returned {response.status_code}"
        except Exception as e:
            yield f"Stream Execution Error: {str(e)}"

    def generate_rag_response(self, query: str, contexts: List[Dict[str, str]]) -> str:
        """
        Generates an answer based on the provided query and context chunks.
        Used specifically for RAG orchestration in the main app.
        """
        # 1. Construct Prompt with explicit numeric IDs and Rank
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
        
        return self.generate_response(
            prompt=f"Context Data:\n{context_block}\n\nUser Question: {query}",
            system_instruction=system_instruction,
            temperature=0.3
        )

    def get_model_info(self) -> str:
        return f"Provider: Ollama | Model: {self.model} | URL: {self.base_url}"
