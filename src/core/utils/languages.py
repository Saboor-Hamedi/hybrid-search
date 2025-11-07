from langdetect import detect


def detect_language(text):
    """Detect language of text."""
    try:
        return detect(text)
    except Exception as e:
        print(f"Error detecting language: {e}")

        return "unknown"
