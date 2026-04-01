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
)

cs = ColorScheme()
model = get_embedder("paraphrase-multilingual-MiniLM-L12-v2")

HEADER_PATTERNS = [
    r"^chapter\s+\d+.*$",  # e.g., "Chapter 2: ..."
    r"^ai engineering.*$",  # book title repeating
]

FOOTER_PATTERNS = [
    r"^\s*\d+\s*$",  # page numbers only
    r"^\s*page\s+\d+\s*$",  # "Page 23"
]

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50





def remove_header_footer(text: str, header_patterns=None, footer_patterns=None) -> str:
    """
    Remove headers and footers from the given text using regex patterns.
    - `header_patterns`: list of regex patterns to match headers
    - `footer_patterns`: list of regex patterns to match footers
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

    # Get meaningful sample for language detection
    meaningful_samples = []
    for element in raw_elements[:5]:  # Check first 5 elements
        text = element["raw_text"].strip()
        if len(text) > 100:  # Only use substantial text samples
            meaningful_samples.append(text)

    if not meaningful_samples:
        # Fallback: use any text we have
        meaningful_samples = [
            element["raw_text"].strip()
            for element in raw_elements[:3]
            if element["raw_text"].strip()
        ]

    sample_content = " ".join(meaningful_samples)

    if sample_content:
        pdf_language = detect_language(normalize_content(sample_content))
        print(f"{cs.BLUE}📄 Detected PDF language: {pdf_language}{cs.RESET}")
    else:
        pdf_language = "unknown"
        print(f"{cs.YELLOW}⚠️  Could not detect PDF language{cs.RESET}")

    # Chunking with better settings
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,  # Smaller chunks for better quality
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )

    stats = {
        "total_elements": len(raw_elements),
        "successful_inserts": 0,
        "failed_inserts": 0,
        "skipped_short": 0,
        "skipped_quality": 0,
        "total_chunks_created": 0,
    }

    print(f"{cs.BLUE}📊 Processing {stats['total_elements']} elements...{cs.RESET}")

    # Process elements
    for i, element in enumerate(raw_elements):
        content = element["raw_text"].strip()

        # remove the header and footer and footer from each element
        content = remove_header_footer(content, HEADER_PATTERNS, FOOTER_PATTERNS)

        # Skip very short content
        if len(content) < 15:
            stats["skipped_short"] += 1
            continue

        # Clean the text more aggressively
        normalized_content = normalize_content(content)
        if not normalized_content or len(normalized_content) < 15:
            stats["skipped_short"] += 1
            continue

        # Split into chunks
        chunks = text_splitter.split_text(normalized_content)
        stats["total_chunks_created"] += len(chunks)

        for chunk_text in chunks:
            chunk_text = chunk_text.strip()

            # Skip empty or low-quality chunks

            if len(chunk_text) < 25:
                stats["skipped_quality"] += 1
                continue

            # clean_chunk = chunk_text
            clean_chunk = normalize_content(chunk_text)
            if len(clean_chunk) < 25:
                stats["skipped_quality"] += 1
                continue

            current_total = stats["successful_inserts"] + stats["failed_inserts"]
            if current_total > 0 and current_total % 50 == 0:
                print(f"  {cs.CYAN}🔄 Processed {current_total} chunks...{cs.RESET}")

            # Try to insert
            if insert_document(
                clean_chunk, conn, cursor, model, commit=False, silent=True
            ):
                stats["successful_inserts"] += 1
            else:
                stats["failed_inserts"] += 1

            # Batch commit
            # Show element progress every 20 elements
            if (i + 1) % 20 == 0:
                print(
                    f"  {cs.BLUE}📝 Processed {i + 1}/{stats['total_elements']} elements...{cs.RESET}"
                )

            # Check for Global Stop Request
            if (i + 1) % 10 == 0 and is_stop_requested():
                print(f"  {cs.RED}🛑 BREAK: System Stop requested. Halting middle-of-file...{cs.RESET}")
                break
    # Final commit
    conn.commit()
    # if stats["successful_inserts"] > 0:
    #     bm25_utils.needs_update = True

    # Display comprehensive summary

    print(f"\n{cs.CYAN}📊 PDF INGESTION SUMMARY{cs.RESET}")
    print(f"{cs.CYAN}{'=' * 50}{cs.RESET}")
    print(f"  📄 PDF File: {os.path.basename(file_path)}")
    print(f"  🌐 Primary Language: {pdf_language}")
    print(f"  📝 Elements Processed: {stats['total_elements']}")
    print(f"  🧩 Chunks Created: {stats['total_chunks_created']}")
    print(f"{cs.CYAN}{'─' * 50}{cs.RESET}")
    print(
        f"  ✅ {cs.GREEN}Successfully Inserted: {stats['successful_inserts']}{cs.RESET}"
    )
    print(f"  ❌ {cs.RED}Failed Inserts: {stats['failed_inserts']}{cs.RESET}")
    print(f"  ⏭️  {cs.YELLOW}Skipped (Too Short): {stats['skipped_short']}{cs.RESET}")
    print(
        f"  🗑️  {cs.YELLOW}Skipped (Low Quality): {stats['skipped_quality']}{cs.RESET}"
    )

    total_processed = (
        stats["successful_inserts"]
        + stats["failed_inserts"]
        + stats["skipped_short"]
        + stats["skipped_quality"]
    )
    success_rate = (
        (stats["successful_inserts"] / total_processed * 100)
        if total_processed > 0
        else 0
    )
    print(f"{cs.CYAN}{'─' * 50}{cs.RESET}")
    print(f"  📈 Success Rate: {success_rate:.1f}%")
    print(f"  🎯 Total Processed: {total_processed}. Time: {get_elapsed()}")
    print(f"{cs.CYAN}{'=' * 50}{cs.RESET}")

    return stats["successful_inserts"] > 0


# C:\Users\saboor\Desktop\random1.pdf
