from aisuite import Client
from jinja2 import Template
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()  

client = Client()

def get_prompt(dataframe: pd.DataFrame) -> str:

    prompt_template = ""
    with open("src/llm/prompt.txt", "r") as file:
        prompt_template = file.read()

    dados = {
        'dados_de_entrada': dataframe.to_markdown(index=False),
    }

    prompt_template: Template = Template(prompt_template)
    prompt_template = prompt_template.render(**dados)

    return prompt_template

def get_llm_response(dataframe: pd.DataFrame, model: str = "openai:gpt-4o-mini") -> str:
    client = Client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": get_prompt(dataframe)},
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip() if response.choices else ""