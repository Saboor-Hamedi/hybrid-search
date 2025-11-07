from sentence_transformers import SentenceTransformer


def get_embedder(text: str="all-MiniLM-L6-v2"):
    return SentenceTransformer(text)
