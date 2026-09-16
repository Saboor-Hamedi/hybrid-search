# CLI — Command-Line Interface

**File**: `src/main.py` (307 lines)

## Menu

```
============================================================
   DOCUMENT MANAGER & THESIS ENGINE
============================================================
  [I] Insert             : Add new document text manually.
  [U] Upload PDF         : Bulk ingest folder or single PDF.
  [H] Hybrid Search      : Semantic + keyword (BM25).
  [S] Semantic Search    : AI embeddings (vector similarity).
  [K] Keyword Search     : Traditional full-text search.
  [P] Paragraph Search   : Results in readable paragraphs.
  [E] Evaluate           : Auto Thesis Evaluation (AI/Data).
  [T] Thesis Compare     : All algorithms side-by-side.
  [C] Count              : Total document count.
  [D] Delete             : Delete document by ID.
  [?] Help               : Show usage guide.
  [Q] Quit               : Exit program.
```

## Command Details

| Key | Action | Calls | Notes |
|-----|--------|-------|-------|
| `i` | Insert | `insert_document()` | Encodes + stores, returns doc_id |
| `u` | Upload PDF | `insert_pdf()` | Single file or full directory batch with Rich progress bar |
| `h` | Hybrid Search | `search_hybrid()` | Default alpha=0.5 |
| `s` | Semantic Search | `search_semantic()` | Vector only |
| `k` | Keyword Search | `search_keyword()` | FTS only |
| `p` | Paragraph | `search_hybrid()` + `display_in_paragraph()` | Readable paragraph view |
| `e` | Evaluate | `auto_eval.run_evaluation()` | Prompts for mode (data/ai) + query limit |
| `t` | Thesis Compare | `thesis_comparator.compare_algorithms()` | Runs all 7 algorithms, Rich comparison table |
| `c` | Count | `get_document_count()` | SELECT COUNT(*) FROM document |
| `d` | Delete | `delete_document()` | Cascade deletes document + embedding |
| `?` | Help | `display_menu()` | Shows menu again |
| `q` | Quit | `sys.exit(0)` | |

## Startup Sequence

1. Print start time
2. Load SentenceTransformer model via `get_model()` with Rich spinner
3. Print model load time
4. Enter main loop: display menu → get choice → execute action

## Features

| Feature | Library | Details |
|---------|---------|---------|
| Tables | `rich.table` | Score-colored, query-term highlighted, RTL Arabic support |
| Progress bars | `rich.progress.track` | Bulk PDF ingestion progress |
| Colors | `ColorScheme` | ANSI escape codes (27 colors) |
| Logging | `logging` | `cli_activity.log` with timestamps |
| Input safety | `safe_input()` | Catches EOFError and KeyboardInterrupt |
| Language detection | `langdetect` | Auto-detect on document insert |

## Color Scheme

```python
# ColorScheme — 21 ANSI codes
HEADER, OKBLUE, OKCYAN, OKGREEN, WARNING, FAIL
BOLD, NORMAL, UNDERLINE, ITALIC, BLACK, RED
GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET
```

## Display Modes

| Mode | Function | Output |
|------|----------|--------|
| Table | `display_in_table()` | Rich Table with Doc ID, Score, Content, Language, Date |
| Paragraph | `display_in_paragraph()` | Boxed paragraphs with metadata header |

Both support query term highlighting and Arabic text reshaping.
