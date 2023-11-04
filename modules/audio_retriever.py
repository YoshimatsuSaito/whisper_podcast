import os
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from pydub import AudioSegment

TEN_MINUTES = 10 * 60 * 1000

class PodcastRetriever:
    """Retrieves the podcast audio from the given url"""
    def __init__(self, url: str, list_tag: list[str] = ["title", "enclosure", "pubDate", "duration", "description", "creator"]) -> None:
        self.url = url
        self.list_tag = list_tag
        self.df_podcast = None

    def _safe_find(self, item: Tag, tag: str) -> None | str:
        """Returns the text of the tag if it exists, else None"""
        res = item.find(tag)
        if res is None:
            return None
        elif tag == "enclosure":
            return res['url']
        else:
            return res.text

    def _parse_data(self) -> None:
        """Returns a dataframe with the data from the podcast"""
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')
        dict_data = {tag: [] for tag in self.list_tag}
        for item in items:
            for tag in self.list_tag:
                dict_data[tag].append(self._safe_find(item, tag))
        self.df_podcast = pd.DataFrame(dict_data)

    def _format_data(self) -> None:
        """Formats the data from the dataframe"""
        if self.df_podcast is None:
            raise Exception("You must first parse the data using parse_data()")
        
        try:
            self.df_podcast['pubDate'] = self.df_podcast['pubDate'].apply(lambda x: parsedate_to_datetime(x))
        except:
            pass

        try:
            self.df_podcast['duration'] = pd.to_timedelta(self.df_podcast['duration'])
        except:
            pass
    
    def parse_and_format_data(self) -> None:
        """Parses and formats the data"""
        self._parse_data()
        self._format_data()
    
    def _download_audio(self, output_dir: Path, idx: int) -> Path:
        """Downloads the audio from the podcast"""
        if self.df_podcast is None:
            raise Exception("You must first parse the data using parse_data()")

        ser_target = self.df_podcast.iloc[idx]

        r = requests.get(ser_target['enclosure'])
        output_path = output_dir / f"{ser_target['title']}_{ser_target['pubDate'].strftime('%Y%m%d%H%M')}.mp3"
        with open(output_path, "wb") as f:
            f.write(r.content)
        
        return output_path

    def _chunk_audio(self, file_path_to_chunk: Path) -> Path:
        """Chunks the audio file into 10 minute chunks"""
        if file_path_to_chunk.exists() and file_path_to_chunk.suffix == '.mp3':
            title_audio = file_path_to_chunk.name.split('.')[0]
            output_dir = file_path_to_chunk.parent / title_audio
            os.makedirs(output_dir, exist_ok=True)

            audio_segment = AudioSegment.from_mp3(file_path_to_chunk)
            for i, chunk in enumerate(audio_segment[::TEN_MINUTES]):
                idx = i if i >= 10 else f"0{i}"
                chunk.export(f"{output_dir}/audio_{idx}.mp3", format="mp3")
            
            # delete the original file
            os.remove(file_path_to_chunk)

            return output_dir
    
    def download_and_chunk_audio(self, output_dir: Path, idx: int) -> None:
        """Downloads and chunks the audio file"""
        if self.df_podcast is None:
            raise Exception("You must first parse the data using parse_data()")
        file_path_to_chunk = self._download_audio(output_dir, idx)
        chunk_dir = self._chunk_audio(file_path_to_chunk)

        return chunk_dir
    
    def download_and_chunk_all_audio(self, output_dir: Path) -> None:
        """Downloads and chunks all the audio files"""
        if self.df_podcast is None:
            raise Exception("You must first parse the data using parse_data()")
        for idx in self.df_podcast.index:
            self.download_and_chunk_audio(output_dir, idx)
