# Podcast Summary App

## Overview
This Streamlit application fetches metadata from a given podcast RSS link, transcribes the audio content, and provides a summary.

## Installation
- Install required packages using Poetry. A `pyproject.toml` file is provided for easy setup.
- Install ffmpeg if it is not already installed in your environment.
```
sudo apt update
sudo apt install ffmpeg
```
- Create a .env file in the root directory and add your OpenAI API key as well as the output directory.

```.env 
OPENAI_API_KEY = "your open ai api key"
OUTPUT_DIR = "your local output dir"
```

## Running the App
Run the application by executing `streamlit run app.py` from the root directory.

## Features
### Fetching metadata from RSS links.
- Information about the podcast and its episodes is extracted from the provided RSS links.
- You can obtain RSS links of a podcast channel you are interested in from websites such as [this one](https://castos.com/tools/find-podcast-rss-feed/).
![meta info](/assets/fetching.png)

### Downloading, transcribing, and summarizing podcasts.
Processing begins when you press the 'Generate a summary!' button.
![processing](/assets/processing.png)

### Showing generated contents
Once processing is complete, the generated content will be displayed as shown below.
![generated_contents](/assets/generated_contents.png)

### Translating content
You can translate the generated content into any language.
![translating](/assets/translating.png)