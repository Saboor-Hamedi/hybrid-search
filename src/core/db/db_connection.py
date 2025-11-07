import os

import psycopg2
from dotenv import load_dotenv
from models.ai_model import get_embedder

load_dotenv()
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
    em_model = os.getenv("EMBEDDER_MODEL")
    if em_model is not None:
        return get_embedder(em_model)
    else:
        return None
