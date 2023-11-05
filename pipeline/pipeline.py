import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(currentdir, "../"))

from modules.audio_metadata_retriever import PodcastMetaDataRetriever
from modules.audio_downloader import download_and_chunk_audio


@dataclass(frozen=False)
class PodcastData:
    """Dataclass for the podcast data"""

    # Add data by PodcastMetaDataRetriever
    id : str
    title: str
    enclosure: str
    pubDate: datetime | None = None
    duration: str | None = None
    description: str | None = None
    creator: str | None = None
    
    # Add data by download_and_chunk_audio
    audio_dir_path: Path | None = None
    
    # Add data by transcribe
    transcript: str | None = None
    
    # Add data by article_generator 
    article: str | None = None


@dataclass(frozen=False)
class PodcastDataCollection:
    """Collection of PodcastData"""
    list_podcast_data: list[PodcastData] = field(default_factory=list)


class PodcastDataProcessingPipeline:
    """Pipeline for processing podcast data"""
    def __init__(self, url: str, output_dir: str) -> None:
        self.url = url
        self.output_dir = output_dir
        self.podcast_data_collection = PodcastDataCollection()

    def get_metadata(self) -> None:
        """Get the metadata from the podcast by PodcastMetaDataRetriever"""
        # Get the podcast meta data
        podcast_metadata_retriever = PodcastMetaDataRetriever(self.url)
        podcast_metadata_collection = podcast_metadata_retriever.get_data()

        # Create the podcast data
        for podcast_metadata in podcast_metadata_collection.list_podcast_metadata:
            podcast_data = PodcastData(
                id=podcast_metadata.id,
                title=podcast_metadata.title,
                enclosure=podcast_metadata.enclosure,
                pubDate=podcast_metadata.pubDate,
                duration=podcast_metadata.duration,
                description=podcast_metadata.description,
                creator=podcast_metadata.creator
            )
            self.podcast_data_collection.list_podcast_data.append(podcast_data)

    def download_audio(self, num_download: int | None = 3) -> None:
        """Download the audio from the podcast by download_and_chunk_audio"""

        # Download the audio and add the audio dir path to the podcast data
        if num_download is None:
            num_download = len(self.podcast_data_collection.list_podcast_data)
        for podcast_data in self.podcast_data_collection.list_podcast_data[:num_download]:
            audio_pathdata = download_and_chunk_audio(
                url=podcast_data.enclosure,
                title=f"{podcast_data.id}_{podcast_data.title}",
                output_dir=self.output_dir
            )
            podcast_data.audio_dir_path = audio_pathdata.audio_dir_path

    # def transcribe(self) -> None:
    #     """Transcribe the audio from the podcast"""
    #     chunk_dir = Path("/workspaces/whisper_podcast/data/Max’s sweet 16, Checo’s home heartbreak, Lewis + Lando shine – Mexico City GP review_202310302023")
    #     sorted_audio_paths = sorted(chunk_dir.iterdir(), key=lambda path: str(path).lower())
    #     for audio_path in sorted_audio_paths:
    #         transcript = transcribe(audio_path, language="en")
