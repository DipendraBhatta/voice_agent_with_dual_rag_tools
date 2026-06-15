# agent/agent.py - CORRECT ORDER
import sys
import os
from pathlib import Path
from typing import List
import json

# PATH SETUP MUST COME FIRST
current_file = Path(__file__).resolve()
agent_dir = current_file.parent
project_root = agent_dir.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "indexing_for_sbc"))
sys.path.insert(0, str(project_root / "indexing_for_spd"))

os.environ["LD_LIBRARY_PATH"] = str(project_root / "piper_libs") + ":" + os.environ.get("LD_LIBRARY_PATH", "")

# ALL OTHER IMPORTS AFTER sys.path is set
from voice_interface.recorder import record_audio
from voice_interface.transcriber import transcribe_audio
from voice_interface.tts import speak_text
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from agent.tools import tools

load_dotenv()

_SBC_INDEX_PATH = project_root / "indexing_for_sbc/ingestion_results/local_level_health_ppo_health_plan_sbc/indexing_results/Final_Indexing.json"
_SPD_INDEX_PATH = project_root / "indexing_for_spd/ingestion_results/local_level_health_ppo_health_plan_spd (1)/indexing_results/master_indexing.json"
_SUMMARY_CACHE = project_root / "agent" / "tool_summaries_cache.json"



def _get_tool_summaries() -> dict:
    if _SUMMARY_CACHE.exists():
        return json.load(open(_SUMMARY_CACHE))

    def extract(path):
        data = json.load(open(path))
        nodes = data if isinstance(data, list) else data.get("nodes", [])
        for node in nodes:
            if node.get("node_id") == "0001":
                return node.get("summary", "")
        return ""

    def condense(raw_summary: str, doc_name: str) -> str:
        groq_key = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0, groq_api_key=groq_key)  # CHANGED: "MODEL" → actual model name
        prompt = f"""You are summarizing a healthcare benefits document called '{doc_name}' for tool selection purposes.

    Below is the full document summary:
    {raw_summary}

    Generate a SHORT summary (20-30 sentences max based on the content, longer for spd) that:
    - Lists the main topics and section titles covered
    - Includes key terms and keywords a user might ask about
    - Helps decide if a user question is relevant to this document

    Return only the summary, no preamble."""
        return llm.invoke(prompt).content.strip()

    print("Building tool summary cache...")
    sbc_raw = extract(_SBC_INDEX_PATH)
    spd_raw = extract(_SPD_INDEX_PATH)

    cache = {
        "sbc": condense(sbc_raw, "Summary of Benefits and Coverage (SBC)"),
        "spd": condense(spd_raw, "Summary Plan Description (SPD)")
    }
    json.dump(cache, open(_SUMMARY_CACHE, "w"), indent=2)
    print("Tool summary cache saved.")
    return cache

_SUMMARIES = _get_tool_summaries()

# 3. Replace your existing SYSTEM_PROMPT with this
SYSTEM_PROMPT = f"""You are a helpful general assistant with access to two healthcare benefit document search tools.

SBC document covers: {_SUMMARIES['sbc']}

SPD document covers: {_SUMMARIES['spd']}

RULES:
- If the question relates to the SBC document → use search_sbc only.
- If the question relates to the SPD document → use search_spd only.
- If it relates to both → call both.
- If the question is unrelated to either document → answer from your own knowledge, do not call any tool.
- Never fabricate benefit information — only use what the tools return for benefit questions.
- Return ONLY the plain answer text. No markdown headers, no bullet formatting unless the question specifically asks for a list.
"""

# ── Color/Style constants ─────────────────────────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"
RED     = "\033[91m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
DIM     = "\033[2m"


def _print_hr(char="─", color=CYAN, width=85):
    print(f"{color}{char * width}{RESET}")


def _extract_text(content) -> str:
    """Safely extract plain text from agent response content."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", "").strip())
            elif isinstance(block, str):
                parts.append(block.strip())
        return "\n".join(parts).strip()
    return str(content).strip()


def _get_tools_called(messages) -> List[str]:
    """Extract which tool names were called from the message history."""
    tools_called = []
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name and name not in tools_called:
                    tools_called.append(name)
    return tools_called


def _display_agent_step(question: str, tools_called: List[str], answer: str):
    print()
    _print_hr("═", CYAN)
    print(f"{BOLD}{CYAN}  AGENT QUERY RESULT{RESET}")
    _print_hr("═", CYAN)
    print()

    print(f"{BOLD}  Step 1  ◈ Relevance Check{RESET}")

    if tools_called:
        tool_labels = {
            "search_sbc": "SBC (Summary of Benefits and Coverage)",
            "search_spd": "SPD (Summary Plan Description)"
        }
        tool_names = " + ".join(tool_labels.get(t, t) for t in tools_called)
        print(f"  {GREEN}✓ Related to benefit document → {tool_names}{RESET}")
        print()

        for tool_name in tools_called:
            doc = "SBC Document" if tool_name == "search_sbc" else "SPD Document"
            print(f"{BOLD}  Step 2  ◆ Calling Tool → {MAGENTA}@{tool_name}{RESET}  [{DIM}{doc}{RESET}]")
        print()

        # ADDED: show answer block for tool-based responses too
        _print_hr("─", GREEN)
        print(f"{BOLD}{GREEN}  ANSWER{RESET}")
        _print_hr("─", GREEN)
        words = answer.split()
        line = "  "
        for word in words:
            if len(line) + len(word) + 1 > 83:
                print(line)
                line = "  " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)
        print()
        _print_hr("═", CYAN)
        print()

    else:
        print(f"  {YELLOW}✗ Not related to any benefit document → General knowledge question{RESET}")
        print()
        print(f"{BOLD}  Step 2  ◆ General Answer{RESET}")
        print()
        _print_hr("─", YELLOW)
        print(f"{BOLD}{YELLOW}  ANSWER{RESET}")
        _print_hr("─", YELLOW)
        words = answer.split()
        line = "  "
        for word in words:
            if len(line) + len(word) + 1 > 83:
                print(line)
                line = "  " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)
        print()
        _print_hr("═", CYAN)
        print()


def get_dynamic_model(provider: str):
    prov = provider.lower().strip()
    if prov == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY in .env")
        model_name = os.getenv("MODEL", "gemini-2.5-flash").strip()
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            google_api_key=api_key.strip()
        )
    elif prov == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY in .env")
        model_name = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile").strip()
        return ChatGroq(
            model_name=model_name,
            temperature=0,
            groq_api_key=api_key.strip()
        )
    else:
        raise ValueError(f"Unsupported provider: '{provider}'")


# def run_agent_with_config(query: str, provider: str) -> str:
#     llm = get_dynamic_model(provider=provider)
#     agent = create_react_agent(llm, tools=tools, prompt=SYSTEM_PROMPT)
#     inputs = {"messages": [HumanMessage(content=query)]}
#     response = agent.invoke(inputs)
#     all_messages = response["messages"]
#     tools_called = _get_tools_called(all_messages)

#     # REVERTED: all_messages[-1] was giving polished answer before
#     answer = _extract_text(all_messages[-1].content)

#     _display_agent_step(query, tools_called, answer)
#     print(f"\n[DEBUG] Speaking: {repr(answer)}\n")  # confirm what gets spoken
#     return answer

def run_agent_with_config(query: str, provider: str) -> str:
    llm = get_dynamic_model(provider=provider)
    agent = create_react_agent(llm, tools=tools, prompt=SYSTEM_PROMPT)
    inputs = {"messages": [HumanMessage(content=query)]}
    response = agent.invoke(inputs)
    all_messages = response["messages"]
    tools_called = _get_tools_called(all_messages)
    answer = _extract_text(all_messages[-1].content)
    _display_agent_step(query, tools_called, answer)
    # REMOVED: debug line
    return answer

if __name__ == "__main__":
    print(f"{BOLD}  Voice Agent with Dual RAG Tools{RESET}")
    print("=" * 60)
    print("Choose LLM Provider:\n[1] Gemini\n[2] Groq")
    choice = input("Select Option (1-2): ").strip()

    if choice == "1":
        active_provider = "gemini"
    elif choice == "2":
        active_provider = "groq"
    else:
        print("Invalid selection.")
        sys.exit(1)

    print(f"\n{GREEN}Active Provider: {active_provider.upper()}{RESET}")
    print("=" * 60)

    print("[1] Text Mode")
    print("[2] Voice Mode")
    print("[q] Quit")
    mode = input("Select Mode: ").strip()
    
    if mode.lower() in ["q", "exit", "quit"]:
        print("Goodbye.")
        sys.exit(0)

    while True:
        try:
            if mode == "2":
                audio_file = record_audio()
                question = transcribe_audio(audio_file)
                
                if not question.strip():
                    print(f"{DIM}🎤 (No distinct voice input captured, skipping processing...){RESET}")
                    
                    print("\n[1] Text Mode\n[2] Voice Mode\n[q] Quit")
                    mode = input("Select Mode (or press enter to try listening again): ").strip()
                    if mode.lower() in ["q", "exit", "quit"]:
                        print("Goodbye.")
                        break
                    if not mode:
                        mode = "2"
                    continue
                    
                print(f"\n🎤 You said: {question}")
            else:
                question = input("\nAsk a question: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not question:
            continue

        if question.lower() in ["exit", "quit", "goodbye", "q"]:
            print("Goodbye.")
            break

        print(f"{DIM}Thinking ({active_provider})...{RESET}\n")

        try:
            answer = run_agent_with_config(question, active_provider)

            if mode == "2" and answer.strip():
                speak_text(answer)

        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            
        # ── SAFETY POSITION ADJUSTMENT ────────────────────────────────
        # Move the mode picker menu outside the try block so that even if an 
        # API or model execution fails, the script safely stops and asks you 
        # what to do next instead of spinning into an infinite record loop.
        print("\n[1] Text Mode\n[2] Voice Mode\n[q] Quit")
        next_mode = input("Select Mode for next turn (Leave blank to keep current): ").strip()
        if next_mode in ["1", "2"]:
            mode = next_mode
        elif next_mode.lower() in ["q", "exit", "quit"]:
            print("Goodbye.")
            break