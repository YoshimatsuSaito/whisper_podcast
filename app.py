import os
from pathlib import Path

import dotenv
import pandas as pd
import streamlit as st
from openai import OpenAI

from modules.article_generator import ArticleGenerator
from modules.audio_downloader import download_and_chunk_audio
from modules.audio_metadata_retriever import PodcastMetaDataRetriever
from modules.transcriber import transcribe
from modules.translator import translate

dotenv.load_dotenv()

# constants
OUTPUT_DIR = Path("./output")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
CLIENT = OpenAI(api_key=OPENAI_API_KEY)
TRANSCRIBE_MODEL_NAME = "whisper-1"
MODEL_NAME = "gpt-4o-mini"
CHUNK_SIZE = 4096


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
if "transcript" not in st.session_state:
    st.session_state["transcript"] = None
if "summary" not in st.session_state:
    st.session_state["summary"] = None
if "list_summary_detail" not in st.session_state:
    st.session_state["list_summary_detail"] = None
if "summary_translated" not in st.session_state:
    st.session_state["summary_translated"] = None
if "list_summary_detail_translated" not in st.session_state:
    st.session_state["list_summary_detail_translated"] = None

# Title and rss feed url
st.title("Podcast summary generator")
st.markdown(
    """
    This app generates a summary of an episode of any podcasts you selected
    """
)
st.link_button(
    "Search a podcast feed",
    "https://castos.com/tools/find-podcast-rss-feed/",
    icon=":material/search:",
)
url = st.text_input(
    "Enter a podcast RSS feed URL",
    value="https://podcasts.files.bbci.co.uk/p02nrsjn.rss",
)

# Get metadata of podcast episodes
df = get_metadata(url)
list_episode_label = [
    f"No. {episode['id']}: {episode['title']} - {episode['pubDate_str']}"
    for episode in df.to_dict("records")
]

# Select episode
episode = st.selectbox("Select an episode from the podcast channel", list_episode_label)
st.markdown("<br>", unsafe_allow_html=True)
idx = list_episode_label.index(episode)
df_episode = df.iloc[idx]

# Initialize session state if episode is changed
if st.session_state["current_episode_id"] != df_episode["id"]:
    st.session_state["current_episode_id"] = df_episode["id"]
    st.session_state["generated"] = False
    st.session_state["transcript"] = None
    st.session_state["summary"] = None
    st.session_state["list_summary_detail"] = None
    st.session_state["summary_translated"] = None
    st.session_state["list_summary_detail_translated"] = None

# Show information of the episode
st.markdown(
    f"""
#### Selected episode: {df_episode["title"]}
"""
)
with st.expander("Show information of the episode"):
    st.markdown(
        f"""
    - Creator: {df_episode["creator"]}
    - Publication date: {df_episode["pubDate_str"]}
    - Duration: {df_episode["duration"]}
    - URL: [Link]({df_episode["enclosure"]})
    - Description: 
    """
    )
    st.markdown(df_episode["description"], unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Generate summary
cols = st.columns(3)
is_generate = cols[1].button("Generate a summary!")
st.markdown("<br>", unsafe_allow_html=True)
if is_generate and not st.session_state["generated"]:
    title = f"{df_episode['id']}_{df_episode['title']}"
    chunk_dir = OUTPUT_DIR / f"{title}"
    # Download and chunk audio
    with st.spinner("Downloading and chunking audio..."):
        if chunk_dir.exists():
            chunk_dir = chunk_dir
        else:
            chunk_dir = download_and_chunk_audio(
                url=df_episode["enclosure"],
                title=f"{df_episode['id']}_{df_episode['title']}",
                output_dir=OUTPUT_DIR,
            )
    st.info("Successfully downloaded audio")

    # Transcribe audio
    progress_text = "Transcribing audio... Please wait."
    transcript_file_path = chunk_dir / "transcript.txt"
    if transcript_file_path.exists():
        with open(transcript_file_path, "r") as f:
            st.session_state["transcript"] = f.read()
    else:
        progress_bar = st.progress(0, text=progress_text)
        list_audio_path = sorted(
            chunk_dir.iterdir(),
            key=lambda path: str(path).lower(),
        )
        list_transcript = []
        for idx, audio_path in enumerate(list_audio_path):
            transcript = transcribe(
                client=CLIENT,
                audio_file_path=audio_path,
                model_name=TRANSCRIBE_MODEL_NAME,
            )
            list_transcript.append(transcript)
            progress_bar.progress((idx + 1) / len(list_audio_path), text=progress_text)
        progress_bar.empty()
        st.session_state["transcript"] = "".join(list_transcript)
        with open(chunk_dir / "transcript.txt", "w") as f:
            f.write(st.session_state["transcript"])
    st.info("Successfully transcribed audio")
    with st.expander("Show the transcription"):
        st.write(st.session_state["transcript"])

    # Summarize transcript
    progress_text = "Writing summary of segment of the episode... Please wait."
    progress_bar = st.progress(0, text=progress_text)
    article_generator = ArticleGenerator(
        title=df_episode["title"],
        text=st.session_state["transcript"],
        client=CLIENT,
        model_name=MODEL_NAME,
        chunk_size=CHUNK_SIZE,
    )
    list_summary_detail = []
    for idx, text in enumerate(article_generator.list_split_text):
        summary_detail = article_generator.summarize_transcript(
            text=text, title=article_generator.title, max_tokens=CHUNK_SIZE * 2
        )
        list_summary_detail.append(f"{summary_detail} \n\n")
        progress_bar.progress(
            (idx + 1) / len(article_generator.list_split_text), text=progress_text
        )
    progress_bar.empty()
    st.session_state["list_summary_detail"] = list_summary_detail
    st.info("Successfully summarized each segment of the episode")
    with st.expander("Show summaries of each segment of the episode."):
        for idx, summary_detail in enumerate(st.session_state["list_summary_detail"]):
            st.subheader(f"Segment {idx + 1}")
            st.markdown(summary_detail)

    # Summarize summaries
    with st.spinner("Summarizing summaries... Please wait."):
        summary = article_generator.summarize_summaries(
            texts=list_summary_detail, max_tokens=CHUNK_SIZE * 2
        )
        st.session_state["summary"] = summary

    st.info("Successfully summarized summaries")
    st.session_state["generated"] = True
    st.rerun()

# Show summary
if st.session_state["generated"]:
    st.subheader("Generated contents")
    with st.expander("Summary"):
        st.markdown(st.session_state["summary"])
    with st.expander("Detailed summary"):
        for idx, summary_detail in enumerate(st.session_state["list_summary_detail"]):
            st.subheader(f"Segment {idx + 1}")
            st.markdown(summary_detail)
    with st.expander("Transcript"):
        st.markdown(st.session_state["transcript"])
    st.markdown("<br>", unsafe_allow_html=True)
    if (
        st.session_state["summary_translated"] is not None
        and st.session_state["list_summary_detail_translated"] is not None
    ):
        st.subheader("Translated contents")
        with st.expander("Show summary translated"):
            st.markdown(st.session_state["summary_translated"])
        with st.expander("Show detailed summary translated"):
            for idx, summary_detail_translated in enumerate(
                st.session_state["list_summary_detail_translated"]
            ):
                st.subheader(f"Segment {idx + 1}")
                st.markdown(summary_detail_translated)
        st.markdown("<br>", unsafe_allow_html=True)

# Translate summary
if st.session_state["generated"]:
    st.subheader("Translation")
    language_to_translate = st.text_input(
        "Enter language to translate. If translation is not needed, skip this.",
        value=None,
    )
    cols_translate = st.columns(3)
    is_translate = cols_translate[1].button("Translate this summary!")
    if language_to_translate is None and is_translate:
        st.warning("Please enter language to translate.")
    elif is_translate:
        progress_text = "Translating summary... Please wait."
        progress_bar = st.progress(0, text=progress_text)
        translated_summary = translate(
            text=st.session_state["summary"],
            language=language_to_translate,
            client=CLIENT,
            model_name=MODEL_NAME,
            max_tokens=CHUNK_SIZE * 2,
        )
        progress_bar.progress(
            1 / (len(st.session_state["list_summary_detail"]) + 1), text=progress_text
        )
        st.session_state["summary_translated"] = translated_summary
        list_summary_detail_translated = []
        for idx, summary_detail in enumerate(st.session_state["list_summary_detail"]):
            translated_summary_detail = translate(
                text=summary_detail,
                language=language_to_translate,
                client=CLIENT,
                model_name=MODEL_NAME,
                max_tokens=CHUNK_SIZE * 2,
            )
            list_summary_detail_translated.append(f"{translated_summary_detail} \n\n")
            progress_bar.progress(
                (idx + 2) / (len(st.session_state["list_summary_detail"]) + 1),
                text=progress_text,
            )
        progress_bar.empty()
        st.session_state["list_summary_detail_translated"] = (
            list_summary_detail_translated
        )

        st.rerun()
