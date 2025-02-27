from pathlib import Path

from openai import OpenAI


def transcribe(
    client: OpenAI, audio_file_path: Path, model_name: str = "whisper-1"
) -> str:
    """Transcribes the audio file using the OpenAI API"""
    with audio_file_path.open("rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=model_name, file=audio_file
        )
    return transcript.text
