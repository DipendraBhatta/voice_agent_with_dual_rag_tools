# voice_interface/voice_rag.py
from .recorder import record_audio
from .transcriber import transcribe_audio
from .tts import speak_text

def start_voice_chat(rag_chain):
    while True:
        audio_file = record_audio()
        query = transcribe_audio(audio_file)
        print("User:", query)

        # Minor fix: prevent empty loops if static transcribes as nothing
        if not query.strip():
            print("🎤 (No clear audio detected, listening again...)")
            continue

        if "exit" in query.lower() or "quit" in query.lower():
            print("Goodbye!")
            break

        answer = rag_chain.invoke(query)
        print("Assistant:", answer)
        speak_text(answer)