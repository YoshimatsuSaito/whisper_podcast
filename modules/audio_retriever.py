import os
from email.utils import parsedate_to_datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

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

    def parse_data(self) -> None:
        """Returns a dataframe with the data from the podcast"""
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')
        dict_data = {tag: [] for tag in self.list_tag}
        for item in items:
            for tag in self.list_tag:
                dict_data[tag].append(self._safe_find(item, tag))
        self.df_podcast = pd.DataFrame(dict_data)

    def format_data(self) -> None:
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
    
    def download_audio(self, output_dir: str, idx: int) -> str:
        """Downloads the audio from the podcast"""
        if self.df_podcast is None:
            raise Exception("You must first parse the data using parse_data()")

        ser_target = self.df_podcast.iloc[idx]

        r = requests.get(ser_target['enclosure'])
        output_path = f"{output_dir}/{ser_target['title']}.mp3"
        with open(output_path, "wb") as f:
            f.write(r.content)
        
        return output_path

    def delete_audio(self, file_path_todelete: str) -> None:
        """Deletes the audio file if it is mp3 file"""
        if os.path.exists(file_path_todelete) and file_path_todelete.endswith(".mp3"):
            os.remove(file_path_todelete)
