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
# Cache the model in models.ai_model now
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

from core.models.ai_model import get_embedder

def get_model():
    """
    Delegates to the centralized get_embedder singleton.
    Uses 'EMBEDDER_MODEL' env var if available.
    """
    model_name = os.getenv("EMBEDDER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    return get_embedder(model_name)

