import os
import json
from pathlib import Path
import google.generativeai as genai
from jinja2 import Template
from openai import OpenAI
import time 


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
        max_retries = 3
        all_extractions = {"extractions": []}

        for html in texts_html:
            retries = 0
            success = False
            prompt = self._create_prompt_process_document(html, patterns)
        
            while retries < max_retries and not success:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0,
                    )
                    
                    extraction = response.choices[0].message.content.strip()

                    try:
                        extraction_dict = json.loads(extraction)
                    except json.JSONDecodeError:
                        extraction_dict = {"extractions": []}

                    print("extraction", extraction_dict)

                    if "extractions" in extraction_dict:
                        all_extractions["extractions"].extend(extraction_dict["extractions"])

                    success = True

                except Exception as e:
                    retries += 1
                    print(f"Erro ao chamar a API da OpenAI (tentativa {retries}): {e}")
                    if retries < max_retries:
                        print("Aguardando 30 segundos antes de tentar novamente...")
                        time.sleep(30)
                    else:
                        print("Máximo de tentativas atingido, passando para o próximo HTML.")

        return all_extractions
        

    def _create_prompt_process_document(self, text_html, patterns):
        section = patterns[0]
        patterns_filtered = patterns[1:]

        patterns_str = "\n".join(
            f"- {key}: {value}"
            for pattern in patterns_filtered
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