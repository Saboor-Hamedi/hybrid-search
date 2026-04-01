from sentence_transformers import SentenceTransformer
import threading

# Thread-safe Singleton for AI Model
_model_instance = None
_model_lock = threading.Lock()

def get_embedder(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    """Returns a singleton instance of the SentenceTransformer model."""
    global _model_instance
    if _model_instance is None:
        with _model_lock:
            if _model_instance is None:
                print(f"🚀 Initializing AI Model: {model_name}...")
                _model_instance = SentenceTransformer(model_name)
                print("✅ Model initialized successfully.")
    return _model_instance
