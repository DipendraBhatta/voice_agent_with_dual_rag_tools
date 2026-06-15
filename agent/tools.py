# agent/tools.py
import os
from typing import Dict, Any
from langchain_core.tools import tool
from indexing_for_sbc.query_retrieval.retrieval_main import RetrievalAgentRunner as RetrievalAgentRunner_SBC
from indexing_for_spd.query_retrieval.retrieval_main import RetrievalAgentRunner as RetrievalAgentRunner_SPD

_SBC_INDEX_PATH = "indexing_for_sbc/ingestion_results/local_level_health_ppo_health_plan_sbc/indexing_results/Final_Indexing.json"
_SPD_INDEX_PATH = "indexing_for_spd/ingestion_results/local_level_health_ppo_health_plan_spd (1)/indexing_results/master_indexing.json"

_sbc_runner: RetrievalAgentRunner_SBC = None
_spd_runner: RetrievalAgentRunner_SPD = None

# ── Colors ────────────────────────────────────────────────────
GREEN   = "\033[92m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
DIM     = "\033[2m"
CYAN    = "\033[96m"


def _get_sbc_runner() -> RetrievalAgentRunner_SBC:
    global _sbc_runner
    if _sbc_runner is None:
        if not os.path.exists(_SBC_INDEX_PATH):
            raise FileNotFoundError(f"SBC index not found: {_SBC_INDEX_PATH}")
        _sbc_runner = RetrievalAgentRunner_SBC(index_path=_SBC_INDEX_PATH)
    return _sbc_runner


def _get_spd_runner() -> RetrievalAgentRunner_SPD:
    global _spd_runner
    if _spd_runner is None:
        if not os.path.exists(_SPD_INDEX_PATH):
            raise FileNotFoundError(f"SPD index not found: {_SPD_INDEX_PATH}")
        _spd_runner = RetrievalAgentRunner_SPD(index_path=_SPD_INDEX_PATH)
    return _spd_runner


# ==================== UPDATED DOCSTRINGS ====================
@tool
def search_sbc(query: str) -> str:
    """Search the Summary of Benefits and Coverage (SBC) document.
    
    Best for: deductibles, copays, coinsurance, out-of-pocket maximums, 
    cost sharing, what is covered or not covered, benefit amounts, 
    and coverage summaries.
    
    This is the primary tool for any cost or coverage level questions.
    """
    try:
        # ── Print Step 1 + Step 2 BEFORE RAG runs ────────────
        print(f"{BOLD}  Step 1  ◈ Relevance Check{RESET}")
        print(f"  {GREEN}✓ Related to benefit document → SBC (Summary of Benefits and Coverage){RESET}")
        print()
        print(f"{BOLD}  Step 2  ◆ Calling Tool → {MAGENTA}@search_sbc{RESET}  [{DIM}SBC Document{RESET}]")
        print()

        runner = _get_sbc_runner()
        result: Dict[str, Any] = runner.query_once(query)
        return result.get("answer", "No relevant information found in SBC document.")
    except FileNotFoundError as e:
        return f"SBC index not found. Run ingestion first. Details: {str(e)}"
    except Exception as e:
        return f"SBC Search Error: {str(e)}"


@tool
def search_spd(query: str) -> str:
    """Search the Summary Plan Description (SPD) document.
    
    Best for: detailed plan rules, eligibility, enrollment, exclusions, 
    definitions, appeals, COBRA, HIPAA, legal provisions, and administration.
    
    Do NOT use this tool for questions about deductibles, copays, 
    coinsurance, out-of-pocket maximums or cost sharing.
    """
    try:
        # ── Print Step 1 + Step 2 BEFORE RAG runs ────────────
        print(f"{BOLD}  Step 1  ◈ Relevance Check{RESET}")
        print(f"  {GREEN}✓ Related to benefit document → SPD (Summary Plan Description){RESET}")
        print()
        print(f"{BOLD}  Step 2  ◆ Calling Tool → {MAGENTA}@search_spd{RESET}  [{DIM}SPD Document{RESET}]")
        print()

        runner = _get_spd_runner()
        result: Dict[str, Any] = runner.query_once(query)
        return result.get("answer", "No relevant information found in SPD document.")
    except FileNotFoundError as e:
        return f"SPD index not found. Run ingestion first. Details: {str(e)}"
    except Exception as e:
        return f"SPD Search Error: {str(e)}"
# ==========================================================


tools = [search_sbc, search_spd]