import os
import json
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

    def generate_regex(self, case: str, model: str = "gpt-4.1") -> str:
        
        prompt = self._generate_prompt(case)
        print(prompt)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )
            
            regex = response.choices[0].message.content.strip()
            print("regex", regex)
            return regex
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")
            return "Ocorreu um erro ao tentar gerar a análise."
    
    def process_document(self, texts_html, patterns):
        prompt = self._create_prompt_process_document(texts_html[0], patterns)
        print(prompt)
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )
            
            extraction = response.choices[0].message.content.strip()
            extraction = response.choices[0].message.content.strip()

            try:
                extraction_dict = json.loads(extraction)  
            except json.JSONDecodeError:
                extraction_dict = {"extractions": []}  

            print("extraction", extraction_dict)
            return extraction_dict

        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")
            return "Ocorreu um erro ao tentar processar o documento."
        

    def _create_prompt_process_document(self, text_html, patterns):
        section = patterns[0]
        patterns.remove(section)

        patterns_str = "\n".join(
            f"- {key}: {value}"
            for pattern in patterns
            for key, value in pattern.items()
        )

        template_str = """
        Você é um assistente que extrai informações de um documento HTML com base em padrões fornecidos.

        As informações vão estar agrupadas pela seguinte regra:
        {{ section }}
        Esse bloco é responsável apenas por te guiar. Você não deve incluir essa regra na resposta.

        Documento HTML:
        {{ text_html }}

        Padrões a serem extraídos:
        {{ patterns_str }}

        Extraia as informações relevantes do documento HTML com base nos padrões fornecidos e retorne os resultados no seguinte formato JSON:

        {
            "extractions": [
                {
                    "pattern_name1": "Valor Extraído1",
                    "pattern_name2": "Valor Extraído2",
                    "pattern_name3": "Valor Extraído3"
                },
                ...
            ]
        }

        Se nenhum valor for encontrado para um padrão específico, retorne "Não encontrado" como valor extraído.
        """
        template = Template(template_str)
        return template.render(section=section, text_html=text_html, patterns_str=patterns_str)