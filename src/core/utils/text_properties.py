import re
import unicodedata


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

def repair_fragments(text):
    # Remove leading/trailing punctuation fragments
    text = re.sub(r'^[.?,\-–]+', '', text)
    text = re.sub(r'[.?,\-–]+$', '', text)
    # Remove orphaned short fragments
    if len(text.split()) < 1:
        return ''
    return text.lstrip()
def clean_text(text: str, preserve_format: bool = True)-> True:
    if not text:
        return ""
    # Step 1: Basic normalization
    text = unicodedata.normalize('NFKC', text)  # Normalize unicode characters

    # Step 2: Remove Rich formatting tags (keep this)
    text = re.sub(r"\[/?[a-z]+\]", "", text, flags=re.IGNORECASE)

    # Step 3: Fix hyphenated word breaks (improved)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # Fix word breaks
    text = re.sub(r"(\w)\s*-\s*(\w)", r"\1-\2", text)   # Clean up hyphens

    # Step 4: Handle line breaks intelligently
    if preserve_format:
        # Replace multiple newlines with paragraph breaks
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        # Single newlines become spaces (within paragraphs)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    else:
        # Replace all newlines with spaces
        text = re.sub(r'\n+', ' ', text)

    # Step 5: Remove URLs, emails, and social media artifacts
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'\b\w+@\w+\.\w+\b', '', text)  # emails
    text = re.sub(r'@\w+', '', text)  # mentions
    text = re.sub(r'#\w+', '', text)  # hashtags

    # Step 6: Clean up excessive whitespace (but preserve paragraph breaks)
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # Trim line starts
    text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)  # Trim line ends

    # Step 7: Smart punctuation cleaning (preserve meaningful punctuation)
    # Remove repeated punctuation (except ellipsis)
    text = re.sub(r'([!?])\1+', r'\1', text)  # !! → !, ??? → ?
    text = re.sub(r'\.{4,}', '...', text)  # .... → ...

    # Fix spaced punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # "word ." → "word."
    text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)  # ". word" → ". word"

    # Step 8: Remove common PDF/OCR artifacts (more targeted)
    text = re.sub(r'\bPage\s+\d+\s*(?:of\s*\d+)?\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{1,3}\s*/\s*\d{1,3}\b', '', text)  # page numbers like "1/10"
    text = re.sub(r'^\s*[\divx]+\s*$', '', text, flags=re.MULTILINE)  # standalone page numbers

    # Step 9: Remove isolated special characters but keep meaningful ones
    text = re.sub(r'\s[^\w\s.,!?;:()\-"]\s', ' ', text)  # Isolated garbage chars

    # Step 10: Final cleanup
    text = text.strip()

    # Step 11: Ensure proper sentence spacing
    text = re.sub(r'\.([a-zA-Z])', r'. \1', text)  # Add space after period if missing

    return text
