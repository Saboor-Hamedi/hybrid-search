import os
import re

# 1. Unstructured_pdf_elements
from ingestion.unstructured_pdf_elements import parse_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.helper_functions import measure_time

from core.db.operations.document_management import insert_document
from core.models.ai_model import get_embedder

# Import the ColorScheme for colored console output
from core.utils.ColorScheme import ColorScheme
from core.utils.languages import detect_language
from core.utils.system_state import is_stop_requested # Import Stop Flag
from core.utils.text_properties import (
    normalize_content,
    clean_text, # Import the advanced cleaner
)

cs = ColorScheme()
model = get_embedder("paraphrase-multilingual-MiniLM-L12-v2")

# Expanded patterns for common PDF noise
HEADER_PATTERNS = [
    r"^chapter\s+\d+.*$",
    r"^ai engineering.*$",
    r"^section\s+\d+.*$",
    r"^figure\s+\d+.*$",
]

FOOTER_PATTERNS = [
    r"^\s*\d+\s*$",
    r"^\s*page\s+\d+\s*$",
    r"^\s*confidential\s*$",
    r"^\s*all rights reserved\s*$",
]

# Categories from 'unstructured' that we should generally ignore
NOISE_CATEGORIES = ["Header", "Footer", "PageNumber", "Image", "Caption"]

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def remove_header_footer(text: str, header_patterns=None, footer_patterns=None) -> str:
    """
    Remove headers and footers from the given text using regex patterns.
    """
    if not text:
        return ""

    header_patterns = header_patterns or []
    footer_patterns = footer_patterns or []

    for pattern in header_patterns + footer_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)

    return text.strip()


def insert_pdf(file_path: str, conn, cursor):
    get_elapsed = measure_time()
    if not os.path.exists(file_path):
        print(f"{cs.RED}File does not exist: {file_path}{cs.RESET}")
        return False
    print(
        f"\n{cs.CYAN}--- Starting PDF Ingestion: {os.path.basename(file_path)} ---{cs.RESET}"
    )

    # Parse PDF to elements
    raw_elements = parse_pdf(file_path)
    if not raw_elements:
        print(f"{cs.YELLOW}No elements extracted. Aborting.{cs.RESET}")
        return False

    # Detection logic for PDF language
    sample_texts = [e["raw_text"] for e in raw_elements[:10] if len(e["raw_text"]) > 100]
    sample_content = " ".join(sample_texts)

    if sample_content:
        pdf_language = detect_language(sample_content[:2000])
        print(f"{cs.BLUE}📄 Detected PDF language: {pdf_language}{cs.RESET}")
    else:
        pdf_language = "unknown"

    # Chunking with better settings
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    stats = {
        "total_elements": len(raw_elements),
        "successful_inserts": 0,
        "failed_inserts": 0,
        "skipped_short": 0,
        "skipped_noise": 0,
        "total_chunks_created": 0,
    }

    print(f"{cs.BLUE}📊 Processing {stats['total_elements']} elements...{cs.RESET}")

    # Process elements
    for i, element in enumerate(raw_elements):
        content = element["raw_text"].strip()
        category = element.get("element_type", "Text")

        # 1. Structural Noise Filter (Skip Headers, Footers, etc based on Unstructured labels)
        if category in NOISE_CATEGORIES:
            stats["skipped_noise"] += 1
            continue

        # 2. Content Cleaning (Advanced regex + ToC detection)
        # We use clean_text which now includes is_toc_content check
        cleaned_content = clean_text(content)

        if not cleaned_content or len(cleaned_content) < 30:
            stats["skipped_short"] += 1
            continue

        # 3. Secondary Header/Footer removal (Regex based fallback)
        cleaned_content = remove_header_footer(cleaned_content, HEADER_PATTERNS, FOOTER_PATTERNS)

        if len(cleaned_content) < 30:
            stats["skipped_short"] += 1
            continue

        # 4. Split into chunks
        chunks = text_splitter.split_text(cleaned_content)
        
        for chunk_text in chunks:
            # Final deep clean on the chunk
            final_chunk = clean_text(chunk_text)
            
            if len(final_chunk) < 30:
                continue

            # Real-time progress display
            current_total = stats["successful_inserts"] + stats["failed_inserts"]
            if current_total > 0 and current_total % 50 == 0:
                print(f"  {cs.CYAN}🔄 Processed {current_total} chunks...{cs.RESET}")

            # Insert into database
            if insert_document(final_chunk, conn, cursor, model, commit=False, silent=True):
                stats["successful_inserts"] += 1
                
                if stats["successful_inserts"] % 100 == 0:
                    conn.commit()
                    print(f"  {cs.GREEN}✅ Auto-committed {stats['successful_inserts']} chunks.{cs.RESET}")
            else:
                stats["failed_inserts"] += 1

            # Stop request check
            if is_stop_requested():
                print(f"  {cs.RED}🛑 BREAK: System Stop requested.{cs.RESET}")
                conn.commit()
                return stats["successful_inserts"] > 0

    # Final commit
    conn.commit()

    print(f"\n{cs.CYAN}📊 PDF INGESTION SUMMARY{cs.RESET}")
    print(f"{cs.CYAN}{'=' * 50}{cs.RESET}")
    print(f"  📄 File: {os.path.basename(file_path)}")
    print(f"  ✅ {cs.GREEN}Inserted: {stats['successful_inserts']}{cs.RESET}")
    print(f"  🗑️  {cs.YELLOW}Noise/ToC Skipped: {stats['skipped_noise']}{cs.RESET}")
    print(f"  ⏭️  {cs.YELLOW}Short/Low Quality: {stats['skipped_short']}{cs.RESET}")
    print(f"{cs.CYAN}{'─' * 50}{cs.RESET}")
    print(f"  ⏱️  Time: {get_elapsed()}")
    print(f"{cs.CYAN}{'=' * 50}{cs.RESET}")

    return stats["successful_inserts"] > 0


# C:\Users\saboor\Desktop\random1.pdf
