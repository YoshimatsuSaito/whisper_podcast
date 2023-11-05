import os
from dataclasses import dataclass
from pathlib import Path

import requests
from pydub import AudioSegment


def _download_audio(url: str, title: str, output_dir: Path) -> Path:
    """Downloads the audio from the podcast"""
    r = requests.get(url)

    output_path = output_dir / f"{title}.mp3"
    with open(output_path, "wb") as f:
        f.write(r.content)

    return output_path


def _chunk_audio(file_path_to_chunk: Path, chunk_size: int) -> Path:
    """Chunks the audio file into chunks (default 10 minutes)"""
    if file_path_to_chunk.exists() and file_path_to_chunk.suffix == ".mp3":
        title_audio = file_path_to_chunk.name.split(".")[0]
        output_chunk_dir = file_path_to_chunk.parent / title_audio
        os.makedirs(output_chunk_dir, exist_ok=True)

        audio_segment = AudioSegment.from_mp3(file_path_to_chunk)
        for i, chunk in enumerate(audio_segment[::chunk_size]):
            idx = i if i >= 10 else f"0{i}"
            chunk.export(f"{output_chunk_dir}/audio_{idx}.mp3", format="mp3")

        # delete the original file
        os.remove(file_path_to_chunk)

        return output_chunk_dir


def download_and_chunk_audio(
    url: str, title: str, output_dir: Path, chunk_size: int = 10 * 60 * 1000
) -> Path:
    """Downloads the audio from url and chunks it into chunks
    Input: url or list of url about the mp3 files
    Output: AudioPathDataCollection
    """
    file_path_to_chunk = _download_audio(url=url, title=title, output_dir=output_dir)
    chunk_dir = _chunk_audio(file_path_to_chunk, chunk_size=chunk_size)
    return chunk_dir
