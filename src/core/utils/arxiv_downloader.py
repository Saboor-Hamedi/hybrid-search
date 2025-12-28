import os
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# No external dependencies besides requests
# pip install requests

def download_2025_papers(category="cs.AI", max_results=100, save_dir="./pdf_2025"):
    """
    Downloads papers from arXiv API for a given category, strictly filtering for 2025.
    """
    
    # Resolve save_dir absolute path to avoid confusion
    # logic: if save_dir is relative, make it relative to THIS script or CWD? 
    # Let's use a fixed folder in the workspace root or local.
    cwd = os.getcwd()
    full_save_path = os.path.join(cwd, save_dir)
    
    if not os.path.exists(full_save_path):
        os.makedirs(full_save_path)
        print(f"Created directory: {full_save_path}")

    base_url = "http://export.arxiv.org/api/query?"
    
    # Query: cat:cs.AI, sorted by submittedDate descending (newest first)
    # We ask for a batch (e.g. 100 or 200) to ensure we cover enough ground
    query = f"search_query=cat:{category}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    
    print(f"Querying arXiv API: {base_url}{query}")
    print("Filter: ONLY papers published/updated in 2025.\n")
    
    try:
        response = requests.get(base_url + query)
        if response.status_code != 200:
            print("Error connecting to arXiv API")
            return

        # Parse XML
        root = ET.fromstring(response.content)
        
        # XML Namespace for Atom
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entries = root.findall('atom:entry', ns)
        print(f"Fetched metadata for {len(entries)} papers. Filtering for 2025...")
        
        download_count = 0
        
        for i, entry in enumerate(entries):
            # Extract Date
            # Format: 2024-03-05T14:02:05Z
            published_str = entry.find('atom:published', ns).text
            # updated_str = entry.find('atom:updated', ns).text
            
            # Use 'published' date to decide "2025 paper"
            dt = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
            
            if dt.year != 2025:
                # print(f"Skipping paper from {dt.year}: {published_str}")
                continue

            # It is a 2025 paper!
            title = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
            # Clean title
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ','-','_','.','+')]).rstrip()
            
            # Get PDF Link
            pdf_link = None
            links = entry.findall('atom:link', ns)
            for link in links:
                if link.attrib.get('title') == 'pdf':
                    pdf_link = link.attrib['href']
                    break
            
            if not pdf_link:
                id_url = entry.find('atom:id', ns).text
                pdf_link = id_url.replace('/abs/', '/pdf/') + ".pdf"
            
            filename = os.path.join(full_save_path, f"{safe_title[:150]}.pdf")
            
            if os.path.exists(filename):
                print(f"[Exist] {safe_title[:60]}...")
                download_count += 1
                continue
                
            print(f"[Downloading 2025] {safe_title[:60]}...")
            
            try:
                r = requests.get(pdf_link, stream=True)
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                download_count += 1
                time.sleep(3) # Be polite
                
            except Exception as e:
                print(f"Failed: {e}")

        print(f"\nDownload Process Complete. Total 2025 Papers in '{save_dir}': {download_count}")
        
    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    download_2025_papers(max_results=100)
