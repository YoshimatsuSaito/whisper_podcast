import dotenv
import os

import openai
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm

dotenv.load_dotenv()


class ArticleGenerator:
    """Generate article from the podcast transcript"""
    def __init__(self, title: str, text: str, model_name: str = "gpt-3.5-turbo", chunk_size: int=1024, chunk_overlap: int = 0) -> None:
        self.model_name = model_name
        self.llm = ChatOpenAI(temperature=0, openai_api_key=os.environ["OPENAI_API_KEY"], model_name=self.model_name)
        self.title = title
        self.text = text
        self.list_split_text = self._split_text(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def _split_text(self, chunk_size: int, chunk_overlap: int) -> list[str]:
        """Split the text into multiple documents"""
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name=self.model_name, 
            chunk_size = chunk_size,
            chunk_overlap  = chunk_overlap,
        )
        texts = text_splitter.split_text(self.text)
        return texts

    def _generate_article(self, title: str, text: str, max_tokens: int) -> str:
        """Generate article from the transcript"""
        user_message = f"""
        You are a writer who is writing an article about the podcast episode.
        The title of the episode is {title}.

        - Read the podcast transcript and create a article based on its content, maintaining the distinctive atmosphere of the episode.
        - Choose an article style that matches the characteristics of the episode (ex. if it is cheerful, the article should also cheeful).
        - To convey the atmosphere of the episode, you should select and directly quote important statements from the transcription.
        - Organize the content into clearly divided sections based on its content. 
        - The article should be interesting for the reader, so you should avoid just summarizing the content of the episode.
        - Write the article in the same language as the transcript.
        
        The transcript of the episode is as follows:

        {text}
        """

        res = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
        )

        return res["choices"][0]["message"]["content"]
    
    def generate_articles(self, max_tokens: int) -> list[str]:
        """Generate articles from the transcript"""
        list_article = []
        for text in tqdm(self.list_split_text):
            article = self._generate_article(text=text, title=self.title, max_tokens=max_tokens)

            list_article.append(f"{article} \n\n")
        return list_article

    def concat_articles(self, texts: list[str], max_tokens: int) -> str:
        """Concatenate the articles into one article"""
        articles = "".join(texts)

        user_message = f"""
        Please connect the articles from various sections of the podcast. 
        The title of the podcast episode is '{self.title}'.

        You should follow these guidelines:
        - Read the text and, where adjacent sections contain duplicated content, consolidate them. 
        - If there are different writing styles throughout the text, unify them into a single style. 
        - DO NOT summarize or make any other alterations beyond these.
        - Output should be in the same language as the articles.
        - Output should be in the markdown format.

        Here are the individual sections you need to connect:

        {articles}
        """

        res = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
        )

        return res["choices"][0]["message"]["content"]
