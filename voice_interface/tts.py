# #
#  voice_interface/tts.py



# voice_interface/tts.py
import subprocess
import os
from pathlib import Path

# CHANGED: removed playsound import entirely — using aplay subprocess instead

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent

PIPER_PATH = str(project_root / "piper")
MODEL_PATH = str(project_root / "voice_interface" / "models" / "en_US-lessac-medium.onnx")
OUTPUT_FILE = str(project_root / "voice_interface" / "output.wav")

def speak_text(text):
    if os.path.exists(OUTPUT_FILE):
        try:
            os.remove(OUTPUT_FILE)
        except Exception:
            pass

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    if not os.path.exists(PIPER_PATH):
        print(f"❌ Error: Piper binary not found at {PIPER_PATH}.")
        return

    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: ONNX voice model missing at {MODEL_PATH}")
        return

    current_env = os.environ.copy()
    current_env["LD_LIBRARY_PATH"] = str(project_root / "piper_libs") + ":" + current_env.get("LD_LIBRARY_PATH", "")
    current_env["ESPEAK_DATA_PATH"] = str(project_root / "piper_libs" / "espeak-ng-data")

    try:
        subprocess.run(
            [PIPER_PATH, "--model", MODEL_PATH, "--output_file", OUTPUT_FILE],
            input=text.encode("utf-8"),
            env=current_env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if os.path.exists(OUTPUT_FILE):
            subprocess.run(["aplay", OUTPUT_FILE], check=True)  # CHANGED: aplay replaces playsound
    except Exception as e:
        print(f"❌ Error while running text-to-speech output generation: {e}")

# import subprocess
# import os
# from pathlib import Path
# from playsound import playsound

# # ── DYNAMIC ABSOLUTE PATH RESOLUTION ──────────────────────────
# current_file = Path(__file__).resolve()
# project_root = current_file.parent.parent

# PIPER_PATH = str(project_root / "piper")
# MODEL_PATH = str(project_root / "voice_interface" / "models" / "en_US-lessac-medium.onnx")
# OUTPUT_FILE = str(project_root / "voice_interface" / "output.wav")

# def speak_text(text):
#     if os.path.exists(OUTPUT_FILE):
#         try:
#             os.remove(OUTPUT_FILE)
#         except Exception:
#             pass

#     os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
#     os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

#     if not os.path.exists(PIPER_PATH):
#         print(f" Error: Piper binary not found at {PIPER_PATH}.")
#         return

#     if not os.path.exists(MODEL_PATH):
#         print(f" Error: ONNX voice model missing at {MODEL_PATH}")
#         return

#     # ── SYSTEM ENVIRONMENT CONFIGURATION ──────────────────────
#     current_env = os.environ.copy()
#     current_env["LD_LIBRARY_PATH"] = str(project_root / "piper_libs") + ":" + current_env.get("LD_LIBRARY_PATH", "")  # CHANGED: piper_libs has all .so files
#     current_env["ESPEAK_DATA_PATH"] = str(project_root / "piper_libs" / "espeak-ng-data")  # NEW: espeak data path

#     try:
#         subprocess.run(
#             [
#                 PIPER_PATH,
#                 "--model", MODEL_PATH,
#                 "--output_file", OUTPUT_FILE
#             ],
#             input=text.encode("utf-8"),
#             env=current_env,
#             check=True,
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL
#         )
#         if os.path.exists(OUTPUT_FILE):
#             playsound(OUTPUT_FILE)
#     except Exception as e:
#         print(f" Error while running text-to-speech output generation: {e}")