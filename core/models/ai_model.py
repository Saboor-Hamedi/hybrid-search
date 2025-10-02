from sentence_transformers import SentenceTransformer


def get_embedder(text="all-MiniLM-L6-v2"):
    return SentenceTransformer(text)
