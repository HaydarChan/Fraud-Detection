import os
import librosa
import soundfile as sf
import tempfile
import subprocess

def extract_audio(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.wav':
        return file_path
    elif ext == '.mp4':
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            # Ekstrak audio pakai ffmpeg
            command = [
                "ffmpeg", "-i", file_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                tmp_audio.name, "-y"
            ]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return tmp_audio.name
    else:
        raise ValueError("Unsupported file type")

def preprocess_audio(input_path: str, output_path: str = None, target_sr: int = 16000) -> str:
    """
    Preprocess audio: resample to target_sr (default 16kHz), convert to mono, and save.
    Returns the path to the preprocessed file.
    If output_path is None, will save to a temp file.
    """
    y, sr = librosa.load(input_path, sr=target_sr, mono=True)
    if output_path is None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, y, target_sr)
            return tmp.name
    else:
        sf.write(output_path, y, target_sr)
        return output_path