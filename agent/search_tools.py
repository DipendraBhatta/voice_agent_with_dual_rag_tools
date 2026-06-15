# search_tools.py - Tools for searching SBC and SPD documents using RAG
import os
from indexing_for_sbc.query_retrieval.retrieval_engine import ExplainableTreeRAG
from indexing_for_spd.query_retrieval.retrieval_engine import ExplainableTreeRAG as ExplainableTreeRAG_SPD
def search_sbc(query: str) -> str:
    """Tool for searching SBC (Summary of Benefits and Coverage) document."""
    try:
        index_path = "indexing_for_sbc/ingestion_results/sbc/indexing_results/Final_Indexing.json"
        
        if not os.path.exists(index_path):
            return "Error: SBC index file not found. Please check the path."
        
        rag = ExplainableTreeRAG(index_path=index_path)
        result = rag.query(query)
        return result.get("answer", "No relevant information found in SBC document.")
    except Exception as e:
        return f"SBC Search Error: {str(e)}"


def search_spd(query: str) -> str:
    """Tool for searching SPD (Summary Plan Description) document."""
    try:
        index_path = "indexing_for_spd/ingestion_results/spd/indexing_results/Final_Indexing.json"
        
        if not os.path.exists(index_path):
            return "Error: SPD index file not found. Please check the path."
        
        rag = ExplainableTreeRAG_SPD(index_path=index_path)
        result = rag.query(query)
        return result.get("answer", "No relevant information found in SPD document.")
    except Exception as e:
        return f"SPD Search Error: {str(e)}"
