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
        
        # 1. Construct Prompt with explicit numeric IDs
        context_block = ""
        for item in contexts:
            # Use a very clear delimiter that the model can't miss
            context_block += f"DOC_ID: {item.get('doc_id')}\nCONTENT: {item.get('content')}\n\n"
        
        system_prompt = (
            "You are a helpful academic research assistant. "
            "Answer the user's question explicitly using ONLY the provided Context Sources. "
            "Do not hallucinate. If the answer is not found, say so.\n"
            "Provide a comprehensive and detailed explanation in your answer.\n"
            "CRITICAL INSTRUCTION: At the very end of your response, you must identify the Single Best Source ID that contributed most to your answer.\n"
            "Format your output exactly like this:\n"
            "<Your Answer Here>\n\n"
            "BEST_SOURCE_ID: <DocID Number Only>"
        )
        
        full_prompt = f"System: {system_prompt}\n\nContext:\n{context_block}\n\nUser Question: {query}\n\nAnswer:"

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
