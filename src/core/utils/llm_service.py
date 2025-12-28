import requests
import json
import os
from typing import List, Dict, Optional

class OllamaService:
    def __init__(self, model: str = "qwen3:0.6b", base_url: str = "http://localhost:11434"):
        # Allow env var override
        self.model = os.environ.get("OLLAMA_MODEL", model)
        self.base_url = os.environ.get("OLLAMA_URL", base_url)
        self.api_generate = f"{self.base_url}/api/generate"
    
    def check_model_exists(self) -> bool:
        """Check if the configured model is available locally"""
        try:
            # List local models
            res = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if res.status_code == 200:
                models = [m['name'] for m in res.json().get('models', [])]
                # Check for exact match or match with :latest tag
                return any(self.model in m or m in self.model for m in models)
            return False
        except:
            return False

    def check_health(self) -> bool:
        try:
            res = requests.get(f"{self.base_url}/", timeout=1)
            return res.status_code == 200
        except:
            return False

    def generate_rag_response(self, query: str, contexts: List[Dict[str, str]]) -> str:
        """
        Generates an answer based on the provided query and context chunks.
        contexts: List of dicts with 'doc_id', 'content'
        """
        
        # 1. Construct Prompt with explicit numeric IDs and Rank
        context_block = ""
        for i, item in enumerate(contexts):
            # Use a very clear delimiter that the model can't miss
            # Include Rank to guide the model (Rank 1 is top retrieval result)
            context_block += f"DOC_ID: {item.get('doc_id')} (Search Rank: {i+1})\nCONTENT: {item.get('content')}\n\n"
        
        system_prompt = (
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
        
        full_prompt = f"System: {system_prompt}\n\nContext Data:\n{context_block}\n\nUser Question: {query}\n\nAnswer:"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3, # Low temp for factual answers
                "num_ctx": 4096     # Ensure enough context window
            }
        }

        try:
            response = requests.post(self.api_generate, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "Error: No response text found.")
            else:
                return f"Error: Ollama API returned {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to local Ollama (is it running at port 11434?)"
        except Exception as e:
            return f"Error generating answer: {str(e)}"
