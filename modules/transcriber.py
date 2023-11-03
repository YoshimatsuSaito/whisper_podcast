import dotenv
import openai

dotenv.load_dotenv()


def transcribe(audio_file_path: str, model_name: str = "whisper-1", language: str = "en") -> str:
    """Transcribes the audio file using the OpenAI API"""
    transcript = openai.Audio.transcribe(model_name, audio_file_path, verbose=True, language=language)
    return transcript
