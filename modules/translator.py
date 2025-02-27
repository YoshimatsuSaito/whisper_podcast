from openai import OpenAI


def translate(
    text: str, language: str, client: OpenAI, model_name: str, max_tokens: int
) -> str:
    """Translate the article to the specified language"""

    user_message = f"""
    You are a excellent translator to translate the text to {language}.

    - Output should be {language} text.
    - Output format should be markdown.

    Text to translate: {text}
    """

    res = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=max_tokens,
    )

    return res.choices[0].message.content
