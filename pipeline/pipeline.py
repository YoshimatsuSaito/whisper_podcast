import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(currentdir, "../"))

from modules.audio_downloader import download_and_chunk_audio
from modules.audio_metadata_retriever import PodcastMetaDataRetriever
from modules.transcriber import Transcriber
from modules.article_generator import ArticleGenerator
from modules.translator import translate


# Set up the logger
logger = logging.getLogger("PodcastProcessingLogger")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


@dataclass(frozen=False)
class PodcastData:
    """Dataclass for the podcast data"""

    # Add data by PodcastMetaDataRetriever
    id: str
    title: str
    enclosure: str
    pubDate: datetime | None = None
    duration: str | None = None
    description: str | None = None
    creator: str | None = None

    # Add data by download_and_chunk_audio
    audio_dir_path: Path | None = None

    # Add data by Transcriber
    transcript: str | None = None

    # Add data by article_generator
    article: str | None = None
    list_article_detail: list[str] | None = None

    # Add data by translator
    translated_article: str | None = None
    list_translated_article_detail: list[str] | None = None


@dataclass(frozen=False)
class PodcastDataCollection:
    """Collection of PodcastData"""

    list_podcast_data: list[PodcastData] = field(default_factory=list)

    def sort_by_id(self, reverse: bool = True) -> None:
        """Sort the list of PodcastData by id"""
        self.list_podcast_data = sorted(
            self.list_podcast_data, key=lambda x: x.id, reverse=reverse
        )


class PodcastDataProcessingPipeline:
    """Pipeline for processing podcast data"""

    def __init__(self, url: str, output_dir: str) -> None:
        self.url = url
        self.output_dir = output_dir
        self.podcast_data_collection = PodcastDataCollection()

    def get_metadata(self) -> None:
        """Get the metadata from the podcast by PodcastMetaDataRetriever"""
        # Get the podcast meta data
        logger.info("Getting the podcast metadata...")
        podcast_metadata_retriever = PodcastMetaDataRetriever(self.url)
        podcast_metadata_collection = podcast_metadata_retriever.get_data()

        # Create the podcast data
        logger.info("Adding the podcast metadata to the podcast data...")
        for podcast_metadata in podcast_metadata_collection.list_podcast_metadata:
            podcast_data = PodcastData(
                id=podcast_metadata.id,
                title=podcast_metadata.title,
                enclosure=podcast_metadata.enclosure,
                pubDate=podcast_metadata.pubDate,
                duration=podcast_metadata.duration,
                description=podcast_metadata.description,
                creator=podcast_metadata.creator,
            )
            self.podcast_data_collection.list_podcast_data.append(podcast_data)

    def download_audio(
        self, num_download: int | None = None, from_now: bool = True
    ) -> None:
        """Download the audio from the podcast by download_and_chunk_audio"""
        # Sort the podcast data by id
        if from_now:
            logger.info("Download audios from now to past...")
            self.podcast_data_collection.sort_by_id(reverse=from_now)

        # Download the audio and add the audio dir path to the podcast data
        if num_download is None:
            num_download = len(self.podcast_data_collection.list_podcast_data)
        logger.info(
            f"Downloading {num_download} audios and adding downloaded dir to podcast data..."
        )
        for podcast_data in self.podcast_data_collection.list_podcast_data[
            :num_download
        ]:
            chunk_dir = download_and_chunk_audio(
                url=podcast_data.enclosure,
                title=f"{podcast_data.id}_{podcast_data.title}",
                output_dir=self.output_dir,
            )
            podcast_data.audio_dir_path = chunk_dir

    def transcribe(
        self, num_transcript: int | None = None, from_now: bool = True
    ) -> None:
        """Transcribe the audio from the podcast"""
        # Sort the podcast data by id
        if from_now:
            logger.info("Transcribing audios from now to past...")
            self.podcast_data_collection.sort_by_id(reverse=from_now)

        # Transcribe the audio and add the transcript to the podcast data
        if num_transcript is None:
            num_transcript = len(self.podcast_data_collection.list_podcast_data)
        logger.info(
            f"Transcribing {num_transcript} audios and adding transcript to podcast data..."
        )
        for podcast_data in self.podcast_data_collection.list_podcast_data[
            :num_transcript
        ]:
            list_audio_path = sorted(
                podcast_data.audio_dir_path.iterdir(),
                key=lambda path: str(path).lower(),
            )
            if len(list_audio_path) == 0:
                podcast_data.transcript = None
            else:
                transcriber = Transcriber(list_audio_path=list_audio_path)
                podcast_data.transcript = transcriber.get_full_transcript()

    def generate_article(self, model_name: str = "gpt-3.5-turbo-1106", max_tokens_detail: int = 2048, max_tokens_concat: int = 4096) -> None:
        """Generate article from the transcript"""
        for podcast_data in self.podcast_data_collection.list_podcast_data:
            article_generator = ArticleGenerator(
                title=podcast_data.title,
                text=podcast_data.transcript, 
                model_name=model_name,
            )
            list_article_detail = article_generator.generate_articles(max_tokens=max_tokens_detail)
            article = article_generator.concat_articles(texts=list_article_detail, max_tokens=max_tokens_concat)

            podcast_data.article = article
            podcast_data.list_article_detail = list_article_detail
    
    def translate_article(self, language: str, model_name: str = "gpt-3.5-turbo-1106", max_tokens_detail: int = 2048, max_tokens_concat: int = 4096) -> None:
        """Translate article from the transcript"""
        for podcast_data in self.podcast_data_collection.list_podcast_data:
            translated_article = translate(text=podcast_data.article, language=language, model_name=model_name, max_tokens=max_tokens_concat)
            list_translated_article_detail = []
            for article_detail in podcast_data.list_article_detail:
                translated_article_detail = translate(text=article_detail, language=language, model_name=model_name, max_tokens=max_tokens_detail)
                list_translated_article_detail.append(translated_article_detail)
            
            podcast_data.translated_article = translated_article
            podcast_data.list_translated_article_detail = list_translated_article_detail