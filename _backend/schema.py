from pydantic import BaseModel
from typing import List, Optional

class TextQueryRequest(BaseModel):
    prompt: str
    provider: str = "gemini"  # or "groq"

class VoiceQueryResponse(BaseModel):
    transcribed_text: str
    answer: str
    status: str
    audio_url: str  # frontend fetches this to play TTS audio

class TextQueryResponse(BaseModel):
    answer: str
    status: str
    logs: Optional[List[str]] = []