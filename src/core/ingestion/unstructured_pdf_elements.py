from unstructured.partition.pdf import partition_pdf
import os
import tempfile
import shutil
from core.utils.ColorScheme import ColorScheme

cs = ColorScheme()


def parse_pdf(pdf_path: str):
    """
    Partitions a PDF file into structured elements with proper cleanup.
    """
    file_name = os.path.basename(pdf_path)
    temp_dir = None

    try:
        # Create a dedicated temp directory that we control
        temp_dir = tempfile.mkdtemp(prefix="pdf_parse_")

        print(f"{cs.BLUE}📄 Parsing PDF: {file_name}{cs.RESET}")

        # Use simpler settings to avoid OCR issues
        elements = partition_pdf(
            filename=pdf_path,
            languages=["eng"],  # Start with just English to avoid warnings
            strategy="fast",  # Use 'fast' instead of 'hi_res' to avoid OCR
            extract_images=False,  # Disable image extraction
            infer_table_structure=False,  # Disable table extraction (can cause issues)
            chunking_strategy=None,  # Disable chunking - we'll do our own
            max_characters=4000,
            temp_dir=temp_dir,  # Use our controlled temp directory
        )

        # Process elements
        structured_data = []
        for element in elements:
            text = str(element).strip()
            if not text or len(text) < 10:  # Filter very short elements
                continue

            metadata = element.metadata.to_dict()

            structured_data.append(
                {
                    "book_id": file_name,
                    "book_title": metadata.get("filename", file_name),
                    "page_number": metadata.get("page_number", "N/A"),
                    "element_type": element.category,
                    "raw_text": text,
                }
            )

        print(
            f"{cs.GREEN}✅ Successfully parsed {len(structured_data)} elements from {file_name}{cs.RESET}"
        )
        return structured_data

    except Exception as e:
        print(f"{cs.RED}❌ Error partitioning {file_name}: {e}{cs.RESET}")
        return []
    finally:
        # Always clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"{cs.BLUE}🧹 Cleaned up temporary files{cs.RESET}")
            except Exception as cleanup_error:
                print(
                    f"{cs.YELLOW}⚠️  Could not clean up temp files: {cleanup_error}{cs.RESET}"
                )
