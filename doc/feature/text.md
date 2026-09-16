# Text Processing Utilities

**Files**: `src/core/utils/`
- `text_properties.py` (108 lines) — Cleaning, normalization, ToC detection
- `text_cleansing.py` (87 lines) — LangChain PDF loader wrapper
- `languages.py` (11 lines) — Language detection
- `helper_functions.py` (32 lines) — Time measurement, input validation
- `bm25_utils.py` (39 lines) — Global BM25 cache

## `clean_text(text, preserve_format=False)`

11-step cleaning pipeline:

```python
def clean_text(text, preserve_format=False):
    # Step 0: ToC detection — return "" if Table of Contents
    if is_toc_content(text): return ""

    # Step 1: Unicode normalization
    text = unicodedata.normalize('NFKC', text)

    # Step 2: Remove formatting tags like [/b], [/i]
    text = re.sub(r"\[/?[a-z]+\]", "", text, flags=re.IGNORECASE)

    # Step 3: Fix hyphenated line breaks  "word-\nbreak" → "wordbreak"
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Step 4: Handle newlines (collapse or preserve)
    if preserve_format:
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    else:
        text = re.sub(r'\n+', ' ', text)

    # Step 5: Remove URLs, emails, @mentions, #hashtags
    text = re.sub(r'http[s]?://(?:...)+', '', text)
    text = re.sub(r'\b\w+@\w+\.\w+\b', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)

    # Step 6: Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)

    # Step 7: Smart punctuation
    text = re.sub(r'([!?])\1+', r'\1', text)  # "!!!" → "!"
    text = re.sub(r'\.{4,}', ' ', text)         # "...." → " "

    # Step 8: Remove PDF artifacts
    text = re.sub(r'\bPage\s+\d+\s*(?:of\s*\d+)?\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{1,3}\s*/\s*\d{1,3}\b', '', text)
    text = re.sub(r'^\s*[\divx]+\s*$', '', text, flags=re.MULTILINE)

    # Step 9: Remove isolated special characters
    text = re.sub(r'\s[^\w\s.,!?;:()\-"]\s', ' ', text)

    # Step 10: Final cleanup
    text = text.strip().lower()

    # Step 11: Fix sentence spacing  ".word" → ". word"
    text = re.sub(r'\.([a-zA-Z])', r'. \1', text)

    return text
```

## `normalize_content(text)`

Used for embedding generation and BM25 indexing:

```python
def normalize_content(text):
    return " ".join(text.strip().split()).lower()
```

Simple: lowercase + collapse all whitespace.

## `is_toc_content(text)`

Detects Table of Contents:

```python
# Pattern 1: Lines with 4+ dots leading to a number
re.search(r'\.{4,}\s*\d+', text) → True

# Pattern 2: Lines starting with chapter/section/number ending with a digit
# If >60% of lines match → True
re.search(r'^\s*(?:\d+|chapter|section|part)\b.*\d+$', line.strip(), re.IGNORECASE)
```

## `repair_fragments(text)`

Cleans display artifacts:

```python
text = re.sub(r'^[.?,\-–]+', '', text)     # Leading punctuation
text = re.sub(r'[.?,\-–]+$', '', text)      # Trailing punctuation
if len(text.split()) < 1: return ''          # Orphaned fragments
```

## `detect_language(text)`

```python
from langdetect import detect
detect("Hello world")  → "en"
detect("مرحبا")        → "ar"
```

Returns `"unknown"` on error.

## `measure_time()`

```python
get_elapsed = measure_time()
# ... work ...
elapsed = get_elapsed()  # → "0.45 seconds" or "1 minutes 23.45 seconds"
```

## BM25 Cache

```python
bm25_corpus = []      # [(doc_id, normalized_content), ...]
bm25_index = None     # BM25Okapi instance
needs_update = True   # Set True by insert_document/delete_document

def update_bm25_index(cursor, normalize_content):
    """Rebuild BM25 index from database. Skips empty token lists."""
    cursor.execute("SELECT id, content FROM document")
    bm25_corpus = [(id, normalize_content(content)) for id, content in rows]
    tokenized = [content.split() for _, content in bm25_corpus]
    bm25_index = BM25Okapi([t for t in tokenized if t])
    needs_update = False
```

## `check_if_empty_input(text)`

```python
def check_if_empty_input(text):
    return len(text.strip()) == 0
```

## `go_back(text)`

```python
def go_back(text):
    return text.lower() in ["back", "b"]
```
