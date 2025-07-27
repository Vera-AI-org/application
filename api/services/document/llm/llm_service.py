import os
from pathlib import Path
import pandas as pd
from aisuite import Client
from jinja2 import Template

class LLMService:
    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("The variable OPENAI_API_KEY was not defined.")
        
        self.client = Client()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> Template:
        template_path = Path(__file__).parent / "templates" / "generate_regex_prompt.j2"
        try:
            with open(template_path, "r", encoding="utf-8") as file:
                return Template(file.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found in: {template_path}")

    def _generate_prompt(self, text:str, selected_texts: list) -> str:
        return self.prompt_template.render(text=text, selected_texts=selected_texts)

    def generate_regex(self, pattern: dict, model: str = "openai:gpt-4o-mini") -> str:
        name, text, selected_texts = pattern.values
        
        prompt = self._generate_prompt(text, selected_texts)
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature= 0.9
            )
            regex = response.choices[0].message.content.strip() if response.choices else ""
            return name, regex
        except Exception as e:
            print(f"Erro ao chamar a API do LLM: {e}")
            return "Ocorreu um erro ao tentar gerar a análise."