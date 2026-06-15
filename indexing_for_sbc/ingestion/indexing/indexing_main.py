# indexing_main.py
import os
import subprocess
import logging
import sys
import importlib
from pathlib import Path
import time

# Import updated dynamic configuration module
import ingestion.config as cfg

# --- LOGGER SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Orchestrator")


def run_step(script_name, *args):
    """Utility to run a script and check for success."""
    logger.info(f"  EXECUTING: {script_name}")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd() 

        command = [sys.executable, script_name] + [str(arg) for arg in args]
        
        subprocess.run(command, check=True, capture_output=True, text=True, env=env)
        logger.info(f"    {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"    CRITICAL ERROR in {script_name}")
        logger.error(f"    Error details: {e.stderr}")
        return False


def main():
    print("\n" + "="*60)
    print("   AI DOCUMENT INDEXING PIPELINE  ")
    print("="*60)

    # Force configurations to reload to register the document slug change safely
    importlib.reload(cfg)

    print(f"\n Active target document: [{cfg.CURRENT_DOC_SLUG}]")
    print("-" * 60)

    # --- WORKSPACE GENERATION ---
    # This now dynamically generates 'indexing_results/slug/debug/extracted_text', etc.
    cfg.ensure_paths_exist([
        cfg.INDEXING_OUTPUT_DIR, 
        cfg.INDEXING_DEBUG_DIR,
        cfg.EXTRACTED_TEXT_DIR,
        cfg.TABLE_SUMMARIES_DIR
    ])

    # Safely convert to string format for standard subprocess handling
    content_html_str = str(cfg.STRUCTURED_HTML_DIR)
    extracted_text_str = str(cfg.EXTRACTED_TEXT_DIR)
    page_content_json_str = str(cfg.PAGE_CONTENT_JSON)
    final_output_json_str = str(cfg.FINAL_OUTPUT_JSON)
    summarized_json_str = str(cfg.SUMMARIZED_JSON)

    # --- EXECUTION PIPELINE STEPS ---

    # STEP 1: Content Extraction
    if not run_step("ingestion/indexing/semantic_page_extractor.py", content_html_str, page_content_json_str):
        sys.exit(1)

    # STEP 2: ROOT NODE SUMMARY
    # Notice: Passes the newly nested isolated 'extracted_text_str' folder path
    if not run_step("ingestion/indexing/root_node_summary.py", page_content_json_str, content_html_str, extracted_text_str, summarized_json_str):
        sys.exit(1)

    # STEP 3: HIERARCHICAL AGGREGATION
    if not run_step("ingestion/indexing/indexing_aggregator.py", summarized_json_str, final_output_json_str):
        sys.exit(1)

    print("\n" + "="*60)
    print("  SUCCESS! Your document has been perfectly indexed.")
    print(f" Output Location: {final_output_json_str}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()