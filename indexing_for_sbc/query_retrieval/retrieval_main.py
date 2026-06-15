# indexing_for_sbc/query_retrieval/Retrieval_main.py
import sys
import os
from pathlib import Path
from typing import Dict, Any

current_file = Path(__file__).resolve()
project_root = current_file.parent
sys.path.insert(0, str(project_root))

from query_retrieval.retrieval_engine import ExplainableTreeRAG
from query_retrieval.chat_history import SessionLogger


class RetrievalAgentRunner:
    """Wrapper to manage and execute the Explainable Tree RAG engine for SBC."""

    def __init__(self, index_path: str):
        self.index_path = index_path
        print(" EXPLAINABLE TREE RAG ENGINE — SBC")
        print("   Vectorless • Hierarchical • Fully Transparent Retrieval")
        print("=" * 85)
        self.rag = ExplainableTreeRAG(index_path=self.index_path)
        self.logger = SessionLogger()

    def query_once(self, question: str) -> Dict[str, Any]:
        """Single query — used by agent tools."""
        result = self.rag.query(question)
        self.rag.pretty_query(question, result=result)
        return result

    def run(self):
        """Interactive standalone query loop."""
        self.rag.display_full_json_tree(truncate_words=20)
        turn_count = 1
        print(f" Tree loaded successfully ({len(self.rag._title_tree.splitlines())} sections)")
        print(f" Logging session to: {self.logger.file_path}")
        print("   Ready for natural language queries.\n")

        while True:
            print("-" * 85)
            question = input(" Ask anything about the document: ").strip()
            if question.lower() in ["exit", "quit", "q"]:
                print("\n Goodbye!")
                break
            if not question:
                continue

            print("\n Searching with full tree reasoning...\n")
            result = self.rag.query(question)
            self.logger.log_interaction(
                turn_number=turn_count,
                question=question,
                rewritten=result.get("rewritten_query", question),
                answer=result.get("answer", "No answer found.")
            )
            self.rag.pretty_query(question, result=result)
            turn_count += 1


if __name__ == "__main__":
    INDEX_PATH = "ingestion_results/sbc/indexing_results/Final_Indexing.json"
    runner = RetrievalAgentRunner(index_path=INDEX_PATH)
    runner.run()