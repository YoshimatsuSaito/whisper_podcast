import os
import sys
from pathlib import Path

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(currentdir, "../"))

from pipeline.pipeline import PodcastDataProcessingPipeline

if __name__ == "__main__":
    """Sample usage of the pipeline"""
    url = "https://your_podcast.rss"
    output_dir = Path("./data")

    pipeline = PodcastDataProcessingPipeline(url=url, output_dir=output_dir)
    pipeline.get_metadata()
    pipeline.download_audio()
    pipeline.transcribe()
    pipeline.generate_article()
    pipeline.translate_article()

    print("Done!")
