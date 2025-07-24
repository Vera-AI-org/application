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
        template_path = Path(__file__).parent / "templates" / "report_analysis_prompt.j2"
        try:
            with open(template_path, "r", encoding="utf-8") as file:
                return Template(file.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found in: {template_path}")

    def _generate_prompt(self, dataframe: pd.DataFrame) -> str:
        dados_markdown = dataframe.to_markdown(index=False)
        return self.prompt_template.render(input_data=dados_markdown)

    def generate_analysis(self, dataframe: pd.DataFrame, model: str = "openai:gpt-4o-mini") -> str:
    
        if dataframe.empty:
            return "Não foi possível gerar a análise pois não há dados para processar."

        prompt = self._generate_prompt(dataframe)
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5
            )
            return response.choices[0].message.content.strip() if response.choices else ""
        except Exception as e:
            print(f"Erro ao chamar a API do LLM: {e}")
            return "Ocorreu um erro ao tentar gerar a análise."