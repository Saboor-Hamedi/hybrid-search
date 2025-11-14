# export_onnx.py
import os

from dotenv import load_dotenv
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

load_dotenv()

# Model config
MODEL_NAME = os.getenv("EMBEDDER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
HF_MODEL_ID = f"sentence-transformers/{MODEL_NAME}"
ONNX_DIR = "./model_onnx"

print(f"📥 Exporting '{HF_MODEL_ID}' to ONNX at '{ONNX_DIR}'...")

# Export and save
ort_model = ORTModelForFeatureExtraction.from_pretrained(
    HF_MODEL_ID,
    export=True,
    provider="CPUExecutionProvider"
)
tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_ID)

# Save both
ort_model.save_pretrained(ONNX_DIR)
tokenizer.save_pretrained(ONNX_DIR)

print(f"✅ ONNX model & tokenizer saved to {ONNX_DIR}")
print("💡 Next: Update `get_model()` to load from this directory.")
