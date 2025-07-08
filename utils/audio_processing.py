import os
from pydub import AudioSegment
from moviepy import VideoFileClip
import tempfile

def extract_audio(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.wav':
        return file_path

    elif ext == '.mp4':
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            clip = VideoFileClip(file_path)
            clip.audio.write_audiofile(tmp_audio.name, codec='pcm_s16le')
            clip.close()
            return tmp_audio.name
    else:
        raise ValueError("Unsupported file type")
