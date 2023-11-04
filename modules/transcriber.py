from pathlib import Path

import dotenv
import openai


dotenv.load_dotenv()



def transcribe(audio_file_path: Path, model_name: str = "whisper-1", language: str = "en") -> str:
    """Transcribes the audio file using the OpenAI API"""
    audio_file = open(audio_file_path, "rb")
    transcript = openai.Audio.transcribe(model_name, audio_file, verbose=True, language=language)
    return transcript["text"]





