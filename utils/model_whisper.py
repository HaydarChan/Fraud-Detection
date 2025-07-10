# utils/model_whisper.py

import whisper

# Load Whisper model sekali saja (bisa ganti "base" ke "small", "medium", "large" jika mau)
whisper_model = whisper.load_model("base")

def transcribe_audio(audio_path: str, language: str = "indonesian") -> str:
    """
    Transkripsi audio menggunakan Whisper lokal.
    Args:
        audio_path: path ke file audio (wav/mp3/mp4/ogg/dll)
        language: bahasa audio (default: "indonesian")
    Returns:
        transcript: hasil transkripsi (string)
    """
    result = whisper_model.transcribe(audio_path, language=language)
    return result["text"]