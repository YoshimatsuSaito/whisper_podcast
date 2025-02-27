# Podcast Summary App

## Overview

This Streamlit application fetches metadata from a given podcast RSS link, transcribes the audio content, and provides a summary.

## Installation

The following steps assume a Linux environment.

### Python packages

Install Python packages in the root directory.

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ffmpeg

Install ffmpeg if it is not already installed in your environment.

```shell
sudo apt update
sudo apt install ffmpeg
```

### OPENAI_API_KEY

Create a .env file in the root directory and add your OpenAI API key.

```env
OPENAI_API_KEY = "your open ai api key"
```

## Running the App

Run the application by executing `streamlit run app.py` from the root directory with [the virtual environment that you created](#python-packages).

## Features

### Fetching metadata from RSS links.

- Information about the podcast and its episodes is extracted from the provided RSS links.
- You can obtain RSS links of a podcast channel you are interested in from websites such as [this one](https://castos.com/tools/find-podcast-rss-feed/).
![meta info](/assets/fetching.png)

### Downloading, transcribing, and summarizing podcasts.

Processing begins when you press the 'Generate a summary!' button.
![processing](/assets/processing.png)

### Showing generated content

Once processing is complete, the generated content will be displayed as shown below.
![generated_contents](/assets/generated_contents.png)

### Translating content

You can translate the generated content into any language.
![translating](/assets/translating.png)
