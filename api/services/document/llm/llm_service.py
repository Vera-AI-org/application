import os
from pathlib import Path
import google.generativeai as genai
from jinja2 import Template
from openai import OpenAI

client = OpenAI()

class LLMService:
    def __init__(self):
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> Template:
        template_path = Path(__file__).parent / "templates" / "generate_regex_prompt.j2"
        try:
            with open(template_path, "r", encoding="utf-8") as file:
                return Template(file.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de template não encontrado em: {template_path}")

    def _generate_prompt(self, case_text: str) -> str:
        return self.prompt_template.render(caso=case_text)

    def generate_regex(self, case: str, model: str = "gpt-5") -> str:
        
        prompt = self._generate_prompt(case)
        print(prompt)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            
            regex = response.choices[0].message.content.strip()
            print("regex", regex)
            return regex
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")
            return "Ocorreu um erro ao tentar gerar a análise."