# Podcast Summary App

## Overview
This Streamlit application fetches metadata from a given podcast RSS link, transcribes the audio content, and provides a summary.

## Installation
- Install required packages using Poetry. A `pyproject.toml` file is provided for easy setup.
- Install ffmpeg if it is not installed to your environment.
```
sudo apt update
sudo apt install ffmpeg
```
- Create a `.env` file in the root directory and add your OpenAI API key and output directory.

```.env 
OPENAI_API_KEY = "your open ai api key"
OUTPUT_DIR = "your local output dir"
```

## Running the App
Run the application by executing `streamlit run app.py` from the root directory.

## Features
- Fetching metadata from RSS links.
- Transcribing podcasts.
- Summarizing content.
- Translate content if you needed.
