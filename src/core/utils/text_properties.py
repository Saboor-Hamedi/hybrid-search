import re
import unicodedata

def normalize_content(text: str) -> str:
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

def is_toc_content(text: str) -> bool:
    """
    Detects if a string is likely part of a Table of Contents.
    Looks for repeated dots, numbers at the end of lines, or specific keywords.
    """
    if not text:
        return False
        
    # Pattern 1: Lines with many dots leading to a number (e.g. Introduction .......... 5)
    if re.search(r'\.{4,}\s*\d+', text):
        return True
        
    # Pattern 2: List of chapters/sections with page numbers
    # Matches "Chapter 1...5" or "1. Intro ... 10"
    lines = text.split('\n')
    toc_lines = 0
    for line in lines:
        if re.search(r'^\s*(?:\d+|chapter|section|part)\b.*\d+$', line.strip(), re.IGNORECASE):
            toc_lines += 1
            
    if len(lines) > 0 and (toc_lines / len(lines)) > 0.6:
        return True
        
    return False

def clean_text(text: str, preserve_format: bool = False) -> str:
    if not text:
        return ""
        
    # Step 0: Initial ToC filtering (skip processing if it's noise)
    if is_toc_content(text):
        return ""

    # Step 1: Basic normalization
    text = unicodedata.normalize('NFKC', text)  # Normalize unicode characters

    # Step 2: Remove Rich formatting tags (keep this)
    text = re.sub(r"\[/?[a-z]+\]", "", text, flags=re.IGNORECASE)

    # Step 3: Fix hyphenated word breaks
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # Fix word breaks
    text = re.sub(r"(\w)\s*-\s*(\w)", r"\1-\2", text)   # Clean up hyphens

    # Step 4: Handle line breaks intelligently
    if preserve_format:
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    else:
        text = re.sub(r'\n+', ' ', text)

    # Step 5: Remove URLs, emails, and social media artifacts
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'\b\w+@\w+\.\w+\b', '', text)  # emails
    text = re.sub(r'@\w+', '', text)  # mentions
    text = re.sub(r'#\w+', '', text)  # hashtags

    # Step 6: Clean up excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)

    # Step 7: Smart punctuation cleaning
    text = re.sub(r'([!?])\1+', r'\1', text)
    text = re.sub(r'\.{4,}', ' ', text)  # Replace long dot sequences with space (often ToC noise)

    # Fix spaced punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)

    # Step 8: Remove common PDF/OCR artifacts
    text = re.sub(r'\bPage\s+\d+\s*(?:of\s*\d+)?\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{1,3}\s*/\s*\d{1,3}\b', '', text)
    text = re.sub(r'^\s*[\divx]+\s*$', '', text, flags=re.MULTILINE)

    # Step 9: Remove isolated special characters
    text = re.sub(r'\s[^\w\s.,!?;:()\-"]\s', ' ', text)

    # Step 10: Final cleanup and lowercasing for search consistency
    text = text.strip().lower()

    # Step 11: Ensure proper sentence spacing
    text = re.sub(r'\.([a-zA-Z])', r'. \1', text)

    return text


