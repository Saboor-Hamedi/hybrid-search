from rich.console import Console
from rich.table import Table
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime
import re
from rich.text import Text
from utils.text_properties import clean_text

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


def truncate_at_word(text: str, max_length: int) -> str:
    """
    Truncates a rich-formatted string at a word boundary to a maximum length.
    Preserves rich markup tags while counting characters.
    """
    plain_text_len = 0
    truncated_text = ""
    in_tag = False

    for i, char in enumerate(text):
        if char == "[" and not in_tag:
            # Found start of a tag
            in_tag = True
            truncated_text += char
        elif char == "]" and in_tag:
            # Found end of a tag
            in_tag = False
            truncated_text += char
        elif not in_tag:
            # Regular character
            if plain_text_len >= max_length:
                # Truncation point reached. Find the last space.
                last_space = truncated_text.rfind(" ")
                if last_space != -1:
                    # Truncate at the last space and add ellipsis
                    return truncated_text[:last_space] + "..."
                else:
                    # No space found, truncate directly
                    return truncated_text + "..."

            truncated_text += char
            plain_text_len += 1
        else:
            # Inside a tag, just append character
            truncated_text += char

    # If the whole string fits, return it as is
    return truncated_text


def display_results(results, query=""):
    """
    Prints the search results in a well-formatted rich table.
    """
    table = Table(title="Search Results", show_header=True, header_style="bold magenta")
    table.add_column("Doc ID", style="cyan", width=8)
    table.add_column("Score", style="magenta", width=10)
    table.add_column("Content", style="white", width=100, overflow="fold")
    table.add_column("Language", style="green", width=12)
    table.add_column("Created At", style="blue", width=12)

    lang_map = {"en": "English", "fa": "Persian", "id": "Indonesian", None: "Unknown"}

    for doc_id, content, score, language, created_at in results:
        content_display = clean_text(content)
        content_display = highlight_query(content_display, query)
        content_display.truncate(100, overflow="ellipsis")

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
