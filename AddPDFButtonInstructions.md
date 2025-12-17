# Quick PDF Upload Button Instructions

## Add this to chat_base.html

**Location**: In `chat_base.html`, find the search button section (around line 690)

**Replace this:**

```html
              <button type="submit" class="search-btn">
                <i class="bi bi-search"></i> Search
              </button>
            </div>
          </div>
```

**With this:**

```html
              <div class="d-flex gap-2 align-items-center">
                <button type="button" class="btn btn-outline-secondary" onclick="document.getElementById('quickPdfInput').click()" title="Upload PDF" style="padding: 0.5rem 0.75rem; border-color: #d1d5db;">
                  <i class="bi bi-file-pdf"  style="font-size: 1rem;"></i>
                </button>
                <input type="file" id="quickPdfInput" accept=".pdf" style="display: none;">

                <button type="submit" class="search-btn">
                  <i class="bi bi-search"></i> Search
                </button>
              </div>
            </div>
          </div>
```

This adds a PDF icon button next to the search button!
