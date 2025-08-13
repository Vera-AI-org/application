import os
from pathlib import Path
import google.generativeai as genai
from jinja2 import Template

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

    def _generate_prompt(self, text: str, selected_texts: list) -> str:
        return self.prompt_template.render(text=text, selected_texts=selected_texts)

    def generate_regex(self, pattern_data: list, model: str = "gemini-2.5-pro") -> str:
        selected_texts = ""
        text = ""
        for pattern in pattern_data:
            selected_texts += pattern.get("values")
            text += pattern.get("context")

        prompt = self._generate_prompt(text, selected_texts)
        
        try:
            llm = genai.GenerativeModel(model)
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.9
            )
            
            response = llm.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            regex = response.text.strip()
            return regex
        except Exception as e:
            print(f"Erro ao chamar a API do Gemini: {e}")
            return "Ocorreu um erro ao tentar gerar a análise."