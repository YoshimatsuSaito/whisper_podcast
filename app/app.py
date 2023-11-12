import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(currentdir, "../"))

from modules.article_generator import ArticleGenerator
from modules.audio_downloader import download_and_chunk_audio
from modules.audio_metadata_retriever import PodcastMetaDataRetriever
from modules.transcriber import Transcriber
from modules.translator import translate


@st.cache_data
def get_metadata(url: str) -> pd.DataFrame:
    """Get metadata of podcast episodes"""
    podcast_metadata_retriever = PodcastMetaDataRetriever(url)
    podcast_metadata_collection = podcast_metadata_retriever.get_data()
    df = podcast_metadata_collection.to_dataframe()
    df = df.sort_values(by="pubDate", ascending=False).reset_index(drop=True)
    df["pubDate_str"] = df["pubDate"].apply(
        lambda ts: ts.strftime("%Y/%m/%d") if pd.notnull(ts) else ts
    )
    return df


# Initialize session state
if "current_episode_id" not in st.session_state:
    st.session_state["current_episode_id"] = None
if "generated" not in st.session_state:
    st.session_state["generated"] = False
if "article" not in st.session_state:
    st.session_state["article"] = None
if "list_article_detail" not in st.session_state:
    st.session_state["list_article_detail"] = None

# Title and rss feed url
st.title("Podcast article generator")
url = st.text_input(
    "Enter podcast RSS feed URL", value="https://podcasts.files.bbci.co.uk/p02nrsjn.rss"
)

# Get metadata of podcast episodes
df = get_metadata(url)
list_episode_label = [
    f"No. {episode['id']}: {episode['title']} - {episode['pubDate_str']}"
    for episode in df.to_dict("records")
]

# Select episode
episode = st.selectbox("Select episode", list_episode_label)
idx = list_episode_label.index(episode)
df_episode = df.iloc[idx]

# Initialize session state if episode is changed
if st.session_state["current_episode_id"] != df_episode["id"]:
    st.session_state["current_episode_id"] = df_episode["id"]
    st.session_state["generated"] = False
    st.session_state["article"] = None
    st.session_state["list_article_detail"] = None

# Show information of the episode
st.markdown(f"""
#### {df_episode['title']}
""")
with st.expander("Show information of the episode"):
    st.markdown(f"""
    - Creator: {df_episode['creator']}
    - Publication date: {df_episode['pubDate_str']}
    - Duration: {df_episode['duration']}
    - URL: [Link]({df_episode['enclosure']})
    - Description: 
    """)
    st.markdown(df_episode["description"], unsafe_allow_html=True)

# Generate article
cols = st.columns(3)
is_generate = cols[1].button("Generate the summary article")
if is_generate and not st.session_state["generated"]:

    with st.status("Generating... Please wait."):
        
        st.write("Downloading and chunking audio...")
        chunk_dir = download_and_chunk_audio(
            url=df_episode["enclosure"],
            title=f"{df_episode['id']}_{df_episode['title']}",
            output_dir=Path("/workspaces/whisper_podcast/data"),
        )

        st.write("Transcribing audio...")
        list_audio_path = sorted(
            chunk_dir.iterdir(),
            key=lambda path: str(path).lower(),
        )
        transcriber = Transcriber(list_audio_path=list_audio_path)
        transcript = transcriber.get_full_transcript()

        st.write("Writing article...")
        article_generator = ArticleGenerator(
            title=df_episode["title"],
            text=transcript,
            model_name="gpt-3.5-turbo-1106",
        )
        list_article_detail = article_generator.generate_articles(max_tokens=2048)
        article = article_generator.concat_articles(
            texts=list_article_detail, max_tokens=4096
        )

    st.session_state["article"] = article
    st.session_state["list_article_detail"] = list_article_detail
    st.info("Article generated")
    st.session_state["generated"] = True

# Show article
if st.session_state["list_article_detail"] is not None:
    for article_detail in st.session_state["list_article_detail"]:
        st.markdown("---")
        st.markdown(article_detail)

# Translate article
if st.session_state["generated"]:
    language_to_translate = st.text_input("Enter language to translate. If translation is not needed, skip this.", value=None)
    if language_to_translate is not None:
        with st.spinner("Translating... Please wait."):
            translated_article = translate(text=st.session_state["article"], language=language_to_translate, model_name="gpt-3.5-turbo-1106", max_tokens=4096)
            list_translated_article_detail = []
            for article_detail in st.session_state["list_article_detail"]:
                translated_article_detail = translate(text=article_detail, language=language_to_translate, model_name="gpt-3.5-turbo-1106", max_tokens=2048)
                list_translated_article_detail.append(translated_article_detail)
            st.info("Translation completed")
        st.session_state["article"] = translated_article
        st.session_state["list_article_detail"] = list_translated_article_detail