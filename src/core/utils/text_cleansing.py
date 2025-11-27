import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_page_content(text: str) -> str:
    """
    Cleans raw PDF text before chunking.
    Removes headers, footers, page numbers, and specific artifacts.
    """
    # 1. Remove specific artifacts like "3----------"
    # Matches a number, followed by 3 or more dashes
    text = re.sub(r'\d+-{3,}', '', text)
    
    # 2. Remove Table of Contents dots (e.g., "Introduction ........... 1")
    # Matches lines ending in a number preceeded by 5+ dots
    text = re.sub(r'.*\.{5,}\s*\d+.*', '', text)
    
    # 3. Remove standalone page numbers (common in headers/footers)
    # Matches lines that are just numbers (e.g., " 4 ")
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # 4. Remove generic headers/footers (short lines at start/end of pages)
    # This removes lines shorter than 20 chars that look like headers
    # (Be careful: this might remove short titles, adjust '20' as needed)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if len(line.strip()) < 5: # Remove very short noise lines
            continue
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines)

def ingest_pdf(pdf_path):
    # 1. LOAD
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    cleaned_docs = []
    
    # 2. CLEAN (The missing step)
    for page in pages:
        raw_text = page.page_content
        
        # Skip pages that are likely just Table of Contents
        if "table of contents" in raw_text.lower()[0:100]:
            print(f"Skipping TOC page: {page.metadata.get('page')}")
            continue
            
        cleaned_text = clean_page_content(raw_text)
        
        # Update the page content
        page.page_content = cleaned_text
        cleaned_docs.append(page)

    # 3. CHUNK
    # Use RecursiveCharacterTextSplitter instead of fixed size
    # It respects sentence boundaries better than hard 500 chars
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_documents(cleaned_docs)
    
    return chunks

# Run this on your data
# chunks = ingest_pdf("your_book.pdf")
# pgvector.add_documents(chunks)