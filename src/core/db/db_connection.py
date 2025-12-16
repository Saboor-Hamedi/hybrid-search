import os

import numpy as np
import psycopg2
from dotenv import load_dotenv
from optimum.onnxruntime import ORTModelForFeatureExtraction
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

# Load environment variables explicitly from the repository `src/.env` file
try:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dotenv_path = os.path.join(base_dir, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded environment from {dotenv_path}")
    else:
        # Fallback to default behavior (load first .env found)
        load_dotenv()
        print("No src/.env found; loaded default .env if present")
except Exception as e:
    print("Error loading .env:", e)
# Cache the model to avoid reloading it every time
_cached_model=None
# source C:/ProgramData/miniconda3/Scripts/activate base
def db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
    except KeyError as e:
        print(f"Error: Missing configuration key in db_config.ini. Details: {e}")
        return None
    except Exception as e:
        print(f"Error connecting to PostgreSQL database. Details: {e}")
        return None


def get_db_cursor(conn):
    return conn.cursor() if conn else None

def get_model():
    """
    Loads the Sentence Transformer model only once (Lazy Singleton)
    using the model name from the environment variable 'EMBEDDER_MODEL'.
    """
    global _cached_model

    # 2. Check if the model is already loaded (Cache Hit)
    if _cached_model is not None:
        return _cached_model

    # 3. Get the model name from the environment variable
    # It will fetch 'paraphrase-multilingual-MiniLM-L12-v2'
    MODEL_NAME = os.getenv("EMBEDDER_MODEL")

    if not MODEL_NAME:
        print("❌ Error: EMBEDDER_MODEL environment variable not set.")
        return None

    print(f"⏳ Loading Sentence Transformer model from ENV: **{MODEL_NAME}**...")

    try:
        # 4. Load the model for the first time (Cache Miss)
        _cached_model = SentenceTransformer(MODEL_NAME)
        print(f"✅ Model **{MODEL_NAME}** loaded and cached successfully.")
        return _cached_model

    except Exception as e:
        print(f"❌ Error loading model '{MODEL_NAME}': {e}")
        # This often happens if the model name is incorrect or network access is an issue
        return None

