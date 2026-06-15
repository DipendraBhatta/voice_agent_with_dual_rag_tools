import os
import time
import json
import logging
import importlib
from pathlib import Path

# Import your dynamic configuration module
import ingestion.config as cfg
from ingestion.parsing.to_structured_html import HTMLCleaner

# Initialize logger to track progress and errors
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    from ingestion.parsing.parse import DoclingEngine

    # 1. Use the input directory defined in your central configuration
    data_dir = cfg.DATA_DIR
    
    # 2. Automatically detect all PDF files in the target directory
    pdf_files = list(data_dir.glob("*.pdf"))

    # 3. Exit early if no documents are found to process
    if not pdf_files:
        logger.warning(f"No PDF files found in {data_dir}. Exiting.")
        return

    # 4. Load the AI parsing engine with GPU acceleration enabled
    engine = DoclingEngine(use_gpu=True)

    # 5. Start the main loop to process each detected PDF
    for input_file in pdf_files:
        overall_start = time.time()
        
        # 6. Extract the filename without extension to use as a unique folder name
        file_slug = input_file.stem 
        
        # 7. Dynamically update the Environment Context with the current document slug
        os.environ["CURRENT_DOC_NAME"] = file_slug
        
        # 8. Force reload the config module to re-evaluate all dynamic paths for this slug
        importlib.reload(cfg)
    
        # 9. Ensure all required dynamic output and log directories exist physically on disk
        cfg.ensure_paths_exist([
            cfg.RAW_HTML_DIR, 
            cfg.STRUCTURED_HTML_DIR, 
            cfg.MARKDOWN_DIR, 
            cfg.JSON_DIR, 
            cfg.LOG_DIR
        ])

        # OPTIONAL: Attach a file handler dynamically to save logs inside your current workspace
        file_handler = logging.FileHandler(cfg.LOG_DIR / "parsing_process.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
        logger.addHandler(file_handler)

        try:
            # 10. Notify that the AI conversion process has started
            logger.info(f"--- Starting AI parsing for: {input_file.name} ---")
            parse_start = time.time()
            
            # 11. Use the engine to convert the PDF into a structured document object
            doc = engine.convert_file(input_file)
            
            # 12. Record the number of pages and time taken for the heavy AI lift
            parse_duration = time.time() - parse_start
            num_pages = len(doc.pages)
            logger.info(f"AI Parsing complete. Pages: {num_pages} | Time: {parse_duration:.2f}s")

            # 13. Iterate through each page to extract specific format data
            for page_no in range(1, num_pages + 1):
                page_total_start = time.time()

                # 14. Generate Markdown content for the current page
                md_content = engine.get_markdown(doc, page_no)
                
                # 15. Generate HTML content for the current page
                html_content = engine.get_html(doc, page_no) 

                # 16. Save the Markdown output to the configuration-managed path
                with open(cfg.MARKDOWN_DIR / f"page_{page_no}.md", "w", encoding="utf-8") as f:
                    f.write(md_content)
                
                # 17. Save the HTML output to the configuration-managed path
                with open(cfg.RAW_HTML_DIR / f"page_{page_no}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)

                # 18. Filter document elements to find items belonging to the current page
                page_elements = [e for e in doc.texts if e.prov and e.prov[0].page_no == page_no]
                
                # 19. Count text elements identified by the AI as headings
                headings = [e for e in page_elements if "heading" in (getattr(e, 'label', '') or '').lower()]
                
                # 20. Count complex table structures present on the current page
                tables = [t for t in doc.tables if t.prov and t.prov[0].page_no == page_no]

                # 21. Assemble metadata and performance stats for the current page
                page_log = {
                    "page_no": page_no,
                    "file_name": input_file.name,
                    "times": {
                        "total_page_sec": round(time.time() - page_total_start, 4)
                    },
                    "stats": {"headings": len(headings), "tables": len(tables)}
                }

                # 22. Write the page-specific metadata to a config-managed JSON log file
                with open(cfg.LOG_DIR / f"log_page_{page_no}.json", "w", encoding="utf-8") as f:
                    json.dump(page_log, f, indent=4)

            # 23. Export the entire document's structured data into a master JSON
            json_dict = engine.get_json_data(doc)
            with open(cfg.JSON_DIR / f"{file_slug}_full.json", "w", encoding="utf-8") as f:
                json.dump(json_dict, f)
            
            # 24. Perform structured HTML cleaning based on configuration directories
            logger.info(f" Handing over to HTMLCleaner for: {file_slug}")
            cleaner = HTMLCleaner(input_dir=cfg.RAW_HTML_DIR, output_dir=cfg.STRUCTURED_HTML_DIR)
            cleaner.process_all(ordered=True)
            
            # 25. Log the final success message for the specific file
            logger.info(f"Finished {input_file.name} in {time.time() - overall_start:.2f}s")

        except Exception as e:
            logger.error(f"Error processing {input_file.name}: {e}")
        finally:
            # Clean up handler for the next loop iteration file slug
            logger.removeHandler(file_handler)
            file_handler.close()

if __name__ == "__main__":
    main()