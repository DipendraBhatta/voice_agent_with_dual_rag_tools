import re
import sys
from bs4 import BeautifulSoup
from pathlib import Path


class HTMLCleaner:
    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------------- CLEAN CORE ----------------
    def clean_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. Remove head, style, script
        if soup.head:
            soup.head.decompose()

        for style in soup.find_all("style"):
            style.decompose()

        for script in soup.find_all("script"):
            script.decompose()

        # 2. Keep only important attributes for structural layouts
        for tag in soup.find_all(True):
            tag.attrs = {
                k: v for k, v in tag.attrs.items()
                if k in ['colspan', 'rowspan']
            }

        # 3. Extract body safely
        if soup.body:
            return soup.body.prettify()

        return soup.prettify().strip()

    # ---------------- FILE PROCESS ----------------
    def process_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_html = f.read()

            cleaned_html = self.clean_html(raw_html)
            output_file = self.output_dir / file_path.name

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_html)

            print(f"   Processed: {file_path.name}")

        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")

    # ---------------- BULK PROCESS ----------------
    def process_all(self, ordered=True):
        html_files = list(self.input_dir.glob("*.html"))

        if not html_files:
            print(f"  Warning: No HTML files found in input directory: {self.input_dir}")
            return

        if ordered:
            # FIXED: Robust numerical regex sorting to prevent crashes on varying filename formats
            try:
                html_files = sorted(
                    html_files,
                    key=lambda x: int(re.search(r'\d+', x.name).group()) if re.search(r'\d+', x.name) else 0
                )
            except Exception as sort_err:
                print(f" ⚠️ Sorting check fallback triggered: {sort_err}. Defaulting to standard alphanumeric order.")
                html_files.sort()

        print(f" Found {len(html_files)} files in target workspace.")

        for file_path in html_files:
            self.process_file(file_path)

        print("  Structural HTML cleaning cycle complete.")