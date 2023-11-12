from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag


@dataclass(frozen=False)
class PodcastMetaData:
    """Dataclass for the podcast metadata"""

    title: str
    enclosure: str
    pubDate: datetime | None
    duration: str | None
    description: str | None
    creator: str | None
    id: str | None = None

    def __post_init__(self):
        if self.title is None or self.enclosure is None:
            raise Exception("Title and enclosure cannot be None")


@dataclass(frozen=False)
class PodcastMetaDataCollection:
    """Collection of PodcastMetaData"""

    list_podcast_metadata: list[PodcastMetaData]

    def __post_init__(self):
        """Sort the metadata list by publication date and assign ids"""
        self.sort_by_pubdate()
        self.assign_ids()

    def sort_by_pubdate(self):
        """Sort the metadata list by publication date."""
        self.list_podcast_metadata.sort(
            key=lambda x: x.pubDate if x.pubDate else datetime.min
        )

    def assign_ids(self):
        """Assign a zero-padded ID based on the sorted position."""
        for i, podcast_metadata in enumerate(self.list_podcast_metadata, start=1):
            podcast_metadata.id = str(i).zfill(4)

    def to_dataframe(self) -> pd.DataFrame:
        """Create a dataframe from the list of PodcastMetaData"""
        df = pd.DataFrame(
            [
                [
                    podcast_metadata.id,
                    podcast_metadata.title,
                    podcast_metadata.enclosure,
                    podcast_metadata.pubDate,
                    podcast_metadata.duration,
                    podcast_metadata.description,
                    podcast_metadata.creator,
                ]
                for podcast_metadata in self.list_podcast_metadata
            ],
            columns=[
                "id",
                "title",
                "enclosure",
                "pubDate",
                "duration",
                "description",
                "creator",
            ],
        )
        return df


class PodcastMetaDataRetriever:
    """Retrieves the podcast audio from the given url
    Input: rss url
    Output: PodcastMetaDataCollection
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self.list_tag = [
            "title",
            "enclosure",
            "pubDate",
            "duration",
            "description",
            "creator",
        ]

    def _safe_find(self, item: Tag, tag: str) -> None | str:
        """Returns the text of the tag if it exists, else None"""
        res = item.find(tag)
        if res is None:
            return None
        elif tag == "enclosure":
            return res["url"]
        else:
            return res.text

    def _get_items(self) -> list[Tag]:
        """Returns a list of item from the podcast"""
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")
        return items

    def get_data(self) -> PodcastMetaDataCollection:
        """Returns a dataframe with the data from the podcast"""
        items = self._get_items()
        list_podcast_metadata = []

        for item in items:
            pubDate = self._safe_find(item, "pubDate")
            pubDate = parsedate_to_datetime(pubDate) if pubDate is not None else None

            podcastmetadata = PodcastMetaData(
                title=self._safe_find(item, "title"),
                enclosure=self._safe_find(item, "enclosure"),
                pubDate=pubDate,
                duration=self._safe_find(item, "duration"),
                description=self._safe_find(item, "description"),
                creator=self._safe_find(item, "creator"),
            )
            list_podcast_metadata.append(podcastmetadata)

        return PodcastMetaDataCollection(list_podcast_metadata=list_podcast_metadata)
