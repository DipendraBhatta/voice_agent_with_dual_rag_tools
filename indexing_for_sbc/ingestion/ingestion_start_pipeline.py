import subprocess
import sys
import logging
import time
import os
from pathlib import Path
import ingestion.config as cfg

class RAGPipelineOrchestrator:
    """
    Orchestrates the RAG ingestion process with updated folder names:
    Phase 1: Parsing (in ingestion/parsing)
    Phase 2: Indexing (in ingestion/indexing)

    Features smart skip-checking for already processed documents,
    latest-upload tracking, and explicit user confirmation.
    """

    def __init__(self):
        self.root_dir = os.getcwd()
        self.log_file = cfg.LOG_DIR / "pipeline_execution.log"
        cfg.ensure_paths_exist([self.log_file.parent])
        self._setup_logger()

    def _setup_logger(self):
        # Clear existing handlers to prevent log bleeding across environments
        root_logger = logging.getLogger()
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - [PIPELINE] - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.log_file, encoding="utf-8")
            ]
        )
        self.logger = logging.getLogger("Orchestrator")

    def _execute_step(self, script_name, relative_dir, custom_args=None):
        """
        Runs a script in isolation with explicit argument pass-throughs.
        """
        target_dir = Path(self.root_dir) / relative_dir
        script_path = target_dir / script_name

        if not script_path.exists():
            self.logger.error(f"File not found: {script_path}")
            return False

        # Build execution arguments array
        exec_args = [sys.executable, "-c"]
        
        python_logic = f"""
import sys
import os
target = r'{target_dir}'
script = r'{script_path}'
if target in sys.path:
    sys.path.remove(target)
sys.path.append(target)
with open(script, 'r', encoding='utf-8') as f:
    exec(f.read(), {{'__name__': '__main__', '__file__': script}})
"""
        exec_args.append(python_logic)

        # Append additional arguments if passed (e.g. for step 2 positional CLI parameters)
        if custom_args:
            exec_args.extend(custom_args)

        try:
            self.logger.info(f"--- Starting: {script_name} ---")
            start_time = time.time()

            subprocess.run(
                exec_args,
                cwd=self.root_dir,
                check=True,
                env={**os.environ, "PYTHONPATH": self.root_dir}
            )

            duration = time.time() - start_time
            self.logger.info(f"Completed {script_name} in {duration:.2f}s")
            return True

        except subprocess.CalledProcessError:
            self.logger.error(f"Execution failed at {script_name}. Pipeline stopped.")
            return False

    def run(self):
        print("\n" + "="*60)
        print("         DOCUMENT INGESTION & INDEXING SYSTEM")
        print("="*60)

        # 1. Fetch details of the latest uploaded document
        target_slug = cfg.CURRENT_DOC_SLUG
        target_file_name = f"{target_slug}.pdf"
        target_path = cfg.DATA_DIR / target_file_name

        if not target_path.exists():
            self.logger.error(f"Could not find target file: {target_path}")
            return

        # 2. AUTOMATIC SKIP CHECKING LOGIC
        final_output_artifact = cfg.FINAL_OUTPUT_JSON

        if final_output_artifact.exists():
            print(f"\n[⏭  SKIPPING COMPUTATION]")
            print(f" Document [{target_slug}] has already been fully indexed!")
            print(f" Found matching artifact: {final_output_artifact.relative_to(self.root_dir)}")
            print("-" * 60)
            
            force_run = input("Do you want to re-process and overwrite it anyway? (yes/no): ").strip().lower()
            if force_run not in ["yes", "y"]:
                print("\nKeeping existing index data intact. Exiting safely.\n")
                return
            print("\n Overwrite confirmed. Preparing to re-parse the document...")

        # 3. Display metadata dashboard if it's a completely fresh run
        else:
            print(f"\n[DETECTED NEW LATEST UPLOAD]")
            print(f" File Name: {target_file_name}")
            print(f" Directory: {cfg.DATA_DIR.relative_to(self.root_dir)}")
            try:
                print(f" Modified:  {time.ctime(target_path.stat().st_mtime)}")
            except Exception:
                pass
            print("-" * 60)

            user_confirmation = input("Are you going to process this file? (yes/no): ").strip().lower()
            if user_confirmation not in ["yes", "y"]:
                print("\nPipeline execution halted by user choice. Exiting safely.\n")
                return
            print("\n Gateway passed! Initiating worker cycles...")

       # Arguments for semantic_page_extractor.py -> <input_dir> <output_json>
        step_2_args = [
            str(cfg.STRUCTURED_HTML_DIR),     # <input_dir> (Cleaned HTML source files)
            str(cfg.PAGE_CONTENT_JSON)        # <output_json> (Target Page_Indexing.json)
        ]

        # Arguments for root_node_summary.py -> <input_json> <html_dir> <text_dir> <output_json>
        step_3_args = [
            str(cfg.PAGE_CONTENT_JSON),       # <input_json>
            str(cfg.STRUCTURED_HTML_DIR),     # <html_dir> 
            str(cfg.EXTRACTED_TEXT_DIR),      # <text_dir>
            str(cfg.SUMMARIZED_JSON)          # <output_json>
        ]

        # Arguments for final hierarchical aggregation -> <summarized_json> <final_output_json>
        step_4_args = [
            str(cfg.SUMMARIZED_JSON),
            str(cfg.FINAL_OUTPUT_JSON)
        ]

        workflow = [
            ("parse_main.py", "ingestion/parsing", None),
            ("semantic_page_extractor.py", "ingestion/indexing", step_2_args),
            ("root_node_summary.py", "ingestion/indexing", step_3_args),
            ("indexing_aggregator.py", "ingestion/indexing", step_4_args)
        ]

        for script, directory, args in workflow:
            if not self._execute_step(script, directory, custom_args=args):
                return
if __name__ == "__main__":
    orchestrator = RAGPipelineOrchestrator()
    orchestrator.run()