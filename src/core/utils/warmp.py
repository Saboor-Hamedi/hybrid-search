import os
import sys

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
model_name = os.getenv("EMBEDDER_MODEL")
print(f"📥 Pre-downloading & caching {model_name}...")

model = SentenceTransformer(model_name)
print(f"✅ Cached at: {model._modules['0']}")
_ = model.encode("warmup")
print("🔥 Fully warmed up.")

