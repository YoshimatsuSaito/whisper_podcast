import os
import sys
from dataclasses import dataclass, field

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(currentdir, "../"))

from modules.transcriber import transcribe
from modules.audio_retriever import PodcastRetriever


@dataclass
class PodcastData:
    """Dataclass for the podcast data"""
    title: str
    enclosure: str
    pubDate: str
    duration: str
    description: str
    creator: str
    transcript: str

@dataclass
class PodcastDataCollection:
    """Collection of PodcastData"""
    list_podcast_data: list[PodcastData] = field(default_factory=list)


def main():
    # Set the podcast url and output directory
    url = "https://anchor.fm/s/260e5c24/podcast/rss"
    output_dir = "/workspaces/whisper_podcast/data"

    # Get the podcast data
    pr = PodcastRetriever(url)
    pr.parse_data()
    pr.format_data()

    # Transcribe the audio
    podcastdata_collection = PodcastDataCollection()
    for idx in pr.df_podcast.index[:2]:
        audio_path = pr.download_audio(output_dir, idx)
        audio_file= open(audio_path, "rb")
        transcript = transcribe(audio_file)

        podcastdata = PodcastData(
            transcript=transcript,
            **pr.df_podcast.iloc[idx].to_dict()
        )

        podcastdata_collection.list_podcast_data.append(podcastdata)

        pr.delete_audio(audio_path)
    
    print("Done!")


if __name__ == "__main__":
    main()
    print("Done!")