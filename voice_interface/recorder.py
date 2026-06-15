# voice_interface/recorder.py
import os
import sounddevice as sd
from scipy.io.wavfile import write

def record_audio(
        filename="voice_interface/input.wav",
        duration=5,
        sample_rate=16000):

    print("\n🎤 Speak now...")
    
    # Force parent folder initialization to prevent file I/O lockouts
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
        # Initializing explicit stream block for Linux ALSA layer stability
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()  # Complete hardware blocking execution loop securely
        write(filename, sample_rate, recording)
    except Exception as e:
        print(f"❌ Microphone capture issue: {e}")
        # Build empty fall-back file configuration to avoid crashing lower execution trees
        write(filename, sample_rate, [[0]] * int(duration * sample_rate))

    return filename