import os
from pathlib import Path

# =====================================================================
# 1. BASE SYSTEM ROOTS
# =====================================================================
ROOT_DIR = Path(os.getcwd())
DATA_DIR = ROOT_DIR / "data" / "input_data"
RESULTS_ROOT = ROOT_DIR / "ingestion_results"

# =====================================================================
# 2. DYNAMIC TARGET DISCOVERY (Newest Modified PDF File Selector)
# =====================================================================
CURRENT_DOC_SLUG = os.environ.get("CURRENT_DOC_NAME")

if not CURRENT_DOC_SLUG:
    if DATA_DIR.exists():
        pdf_files = list(DATA_DIR.glob("*.pdf"))
    else:
        pdf_files = []

    if pdf_files:
        # Sort files by modification time: newest first
        pdf_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        CURRENT_DOC_SLUG = pdf_files[0].stem
    else:
        CURRENT_DOC_SLUG = "default_doc"

# Isolated root workspace for the active target document
DOC_BASE_DIR = RESULTS_ROOT / CURRENT_DOC_SLUG

# Primary stage outputs folders
PARSING_OUTPUT_DIR = DOC_BASE_DIR / "parsing_results"
INDEXING_OUTPUT_DIR = DOC_BASE_DIR / "indexing_results"

# =====================================================================
# 3. PARSING DIRECTORY SYSTEM
# =====================================================================
RAW_HTML_DIR = PARSING_OUTPUT_DIR / "html"
STRUCTURED_HTML_DIR = PARSING_OUTPUT_DIR / "structured" / "html"
MARKDOWN_DIR = PARSING_OUTPUT_DIR / "markdown"
JSON_DIR = PARSING_OUTPUT_DIR / "json"
LOG_DIR = ROOT_DIR / "logs" / CURRENT_DOC_SLUG

# =====================================================================
# 4. INDEXING WORKSPACE DIRECTORY SYSTEM
# =====================================================================
INDEXING_DEBUG_DIR = INDEXING_OUTPUT_DIR / "debug"
EXTRACTED_TEXT_DIR = INDEXING_DEBUG_DIR / "extracted_text"
TABLE_SUMMARIES_DIR = INDEXING_DEBUG_DIR / "table_summaries"

# =====================================================================
# 5. ALL TARGET ARTIFACTS AND INTERMEDIATE STORAGE WORKER POINTERS
# =====================================================================

# Step 1: Page-Extractor Production Target
PAGE_CONTENT_JSON = INDEXING_OUTPUT_DIR / "Page_Indexing.json"

# Step 2: Markdown TOC Extraction Asset
ASCII_TOC_TXT = INDEXING_OUTPUT_DIR / "Markdown_to_ASCII_TOC.txt"

# Step 3: Tree Indexing Skeleton Architecture Mapping
TOC_SKELETON_JSON = INDEXING_OUTPUT_DIR / "TOC_to_Indexing.json"

# Step 4: Header Extraction and Mapping Intermediate Assets
H2_EXTRACTED_TXT = INDEXING_OUTPUT_DIR / "h2_extracted_content.txt"
H2_GROUPED_TXT = INDEXING_OUTPUT_DIR / "h2_grouped.txt"

# Step 5: Content Tree Aggregation Output Location
FINAL_OUTPUT_JSON = INDEXING_OUTPUT_DIR / "Final_Indexing.json"

# Step 6: Navigation Synthesizer Core Final Results Logs
SUMMARIZED_JSON = INDEXING_OUTPUT_DIR / "Summarized_Nodes.json"
ROOT_SUMMARY_TXT = INDEXING_OUTPUT_DIR / "root_summary.txt"

# Metrics & Evaluation Telemetry Reports
COST_PERFORMANCE_LOG = ROOT_DIR / "COST_PERFORMANCE.txt"
SUMMARIZER_COST_LOG = ROOT_DIR / "COST_PERFORMANCE_SUMMARIZER.txt"

# =====================================================================
# 6. DIRECTORY UTILITIES
# =====================================================================
def ensure_paths_exist(paths_list):
    """Utility to make sure folders exist on disk before writing files."""
    for path in paths_list:
        Path(path).mkdir(parents=True, exist_ok=True)