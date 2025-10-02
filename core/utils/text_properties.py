import re


def normalize_content(text: str) -> str:
    # Trim whitespace, but keep the original case and characters.
    # normalized_text = " ".join(text.strip().split())
    # # You can add a simple lowercase step if you want, but be aware it
    # normalized_text = normalized_text.lower()
    # return normalized_text
    """
    Normalize for storage and embeddings.
    - Lowercase
    - Collapse whitespace
    """
    if not text:
        return ""
    return " ".join(text.strip().split()).lower()


def clean_text(text: str) -> str:
    """
    Clean for display (presentation layer only).
    Removes formatting noise, artifacts, etc.
    """
    if not text:
        return ""

    # Remove Rich formatting tags like [bold], [yellow], etc.
    text = re.sub(r"\[/?[a-z]+\]", "", text, flags=re.IGNORECASE)

    # Fix common OCR issues and line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"\n+", " ", text)

    # Remove URLs, mentions, hashtags
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)

    # Remove runs of symbols like ######, $$$$$, ,,,, etc.
    text = re.sub(r"[^\w\s\.\,\!\?\-]{2,}", " ", text)

    # Remove isolated special characters
    text = re.sub(r"\s[^\w\s\.\,\!\?\-]\s", " ", text)

    # remove period
    text = re.sub(r"\.", "", text)
    # remove dollar sign
    text = re.sub(r"[#$]", "", text)

    # Keep single allowed punctuation but collapse duplicates (e.g., "....." → ".")
    text = re.sub(r"([.,!?-])\1{1,}", r"\1", text)

    # Remove page numbers and headers
    text = re.sub(r"\bPage\s+\d+\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{1,3}\s+of\s+\d{1,3}\b", "", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text.strip()
