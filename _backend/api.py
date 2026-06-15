import sys
import os
from pathlib import Path

# PATH SETUP FIRST — same as agent.py
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "indexing_for_sbc"))
sys.path.insert(0, str(BASE_DIR / "indexing_for_spd"))
os.environ["LD_LIBRARY_PATH"] = str(BASE_DIR / "piper_libs") + ":" + os.environ.get("LD_LIBRARY_PATH", "")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import shutil

load_dotenv(dotenv_path=BASE_DIR / ".env")

# IMPORT YOUR EXISTING FUNCTIONS — no rewrite needed
from agent.agent import run_agent_with_config
from voice_interface.transcriber import transcribe_audio
from voice_interface.tts import speak_text
from _backend.schema import TextQueryRequest, TextQueryResponse, VoiceQueryResponse

app = FastAPI(title="Voice Agent with Dual RAG Tools")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock down to frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = BASE_DIR / "api" / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# ── STARTUP ──────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    print(" Voice Agent API ready.")

# ── HEALTH CHECK ─────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}

# ── TEXT QUERY ───────────────────────────────────────────────
@app.post("/query", response_model=TextQueryResponse)
async def text_query(request: TextQueryRequest):
    try:
        answer = run_agent_with_config(request.prompt, request.provider)
        return TextQueryResponse(answer=answer, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── VOICE QUERY ──────────────────────────────────────────────
# Frontend sends audio file → transcribe → agent → TTS → return audio
@app.post("/voice", response_model=VoiceQueryResponse)
async def voice_query(
    audio: UploadFile = File(...),
    provider: str = Form(default="gemini")
):
    try:
        # 1. Save uploaded audio
        input_path = str(TEMP_DIR / "input.wav")
        with open(input_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        # 2. Transcribe
        question = transcribe_audio(input_path)
        if not question.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio.")

        # 3. Run agent
        answer = run_agent_with_config(question, provider)

        # 4. TTS — speak_text saves to voice_interface/output.wav
        speak_text(answer)
        output_path = BASE_DIR / "voice_interface" / "output.wav"

        return VoiceQueryResponse(
            transcribed_text=question,
            answer=answer,
            status="success",
            audio_url="/audio/output"  # frontend calls this to get the wav
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── SERVE TTS AUDIO FILE TO FRONTEND ─────────────────────────
@app.get("/audio/output")
async def get_audio():
    output_path = BASE_DIR / "voice_interface" / "output.wav"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(str(output_path), media_type="audio/wav")