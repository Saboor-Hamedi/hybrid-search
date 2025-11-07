from rich.console import Console
from rich.table import Table
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime
import re
from rich.text import Text
from utils.ColorScheme import ColorScheme
from utils.text_properties import repair_fragments
from rich.panel import Panel
from rich.columns import Columns

cs = ColorScheme()
console = Console()


def fix_arabic_text(text):
    """
    Fixes the visual display of Arabic/Persian text for a left-to-right console.
    This function should be called ONLY for display purposes, after all
    string manipulation and highlighting has been completed.
    """
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)


def highlight_query(content, query: str) -> Text:
    """
    Highlights query terms in the given content.
    Accepts either a plain string or a rich.Text object.
    """
    if isinstance(content, Text):
        txt = content
        plain_text = txt.plain
    else:
        txt = Text(content)
        plain_text = content

    if not query:
        return txt

    for term in query.split():
        for match in re.finditer(re.escape(term), plain_text, re.IGNORECASE):
            txt.stylize("bold yellow", match.start(), match.end())

    return txt



def truncate_text(text: str, max_length: int =300)-> str:
    if len(text) <= max_length:
        return text
    
    # try to find space before max_length 
    truncated  = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.7: # Only if we have reasonable space
        return truncated[:last_space] + "..."
    else:
        return truncated[:-3] + "..." # Hard truncate

def display_in_table(results, query=""):
    """
    Prints the search results in a well-formatted rich table.
    """
    table = Table(title="Search Results", show_header=True, header_style="bold magenta")
    table.add_column("Doc ID", style="cyan", width=8)
    table.add_column("Score", style="magenta", width=13)
    table.add_column("Content", style="white", width=100, overflow="fold")
    table.add_column("Language", style="green", width=12)
    table.add_column("Created At", style="blue", width=18)

    lang_map = {"en": "English", "fa": "Persian", "id": "Indonesian", None: "Unknown"}

    for doc_id, content, score, language, created_at in results:
        # cleaned_content  = clean_text(content)
        cleaned_content = repair_fragments(content) # Optional, see below
        truncated_content = truncate_text(cleaned_content, 300)
        content_display = highlight_query(truncated_content, query)
        # content_display.truncate(300, overflow="ellipsis")

        # Step 3: Handle Arabic/Persian shaping after truncation
        if language == "fa":
            content_display = Text(
                fix_arabic_text(content_display.plain), style="white"
            )

        # Score color
        score_style = "green" if score > 0.7 else "yellow" if score > 0.4 else "red"
        language_display = lang_map.get(language, language or "Unknown").capitalize()
        created_at_str = (
            created_at.strftime("%Y-%m-%d")
            if isinstance(created_at, datetime)
            else str(created_at)
        )

        # Add row
        table.add_row(
            str(doc_id),
            f"[{score_style}]{score:.3f}[/{score_style}]",
            content_display,  # Pass Text directly
            language_display,
            created_at_str,
        )

    console.print(table)



def display_in_paragraph(results, query=""):
    """
    Display search results in simple paragraph format using print statements.
    """
    if not results:
        print(f"{cs.RED}No relevant results found.{cs.RESET}")
        return
    
    print(f"\n{cs.BOLD}📄 Search Results for: '{query}'{cs.RESET}")
    print(f"{cs.CYAN}Found {len(results)} documents{cs.RESET}\n")
    
    lang_map = {"en": "English", "fa": "Persian", "id": "Indonesian", None: "Unknown"}
    
    for i, (doc_id, content, score, language, created_at) in enumerate(results, 1):
        # Clean the content for display
        cleaned_content = repair_fragments(content)
        
        # Score with color
        score_color = cs.GREEN if score > 0.7 else cs.YELLOW if score > 0.4 else cs.RED
        score_display = f"{score_color}{score:.3f}{cs.RESET}"
        
        # Format metadata
        language_display = lang_map.get(language, language or "Unknown")
        created_at_str = (
            created_at.strftime("%Y-%m-%d %H:%M")
            if isinstance(created_at, datetime)
            else "Unknown date"
        )
        
        # Print result header
        print(f"{cs.BOLD}┌─ Result {i} {'─' * 60}{cs.RESET}")
        print(f"{cs.BOLD}│{cs.RESET}")
        print(f"{cs.BOLD}│{cs.RESET} {cs.CYAN}Document ID:{cs.RESET} {doc_id}")
        print(f"{cs.BOLD}│{cs.RESET} {cs.CYAN}Relevance Score:{cs.RESET} {score_display}")
        print(f"{cs.BOLD}│{cs.RESET} {cs.CYAN}Language:{cs.RESET} {language_display}")
        print(f"{cs.BOLD}│{cs.RESET} {cs.CYAN}Added:{cs.RESET} {created_at_str}")
        print(f"{cs.BOLD}│{cs.RESET}")
        
        # Print content
        print(f"{cs.BOLD}│{cs.RESET} {cs.CYAN}Content:{cs.RESET}")
        print(f"{cs.BOLD}│{cs.RESET} {cleaned_content}")
        print(f"{cs.BOLD}│{cs.RESET}")
        print(f"{cs.BOLD}└{'─' * 70}{cs.RESET}\n")