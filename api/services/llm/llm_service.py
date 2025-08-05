import json
import google.generativeai as genai
from pathlib import Path
from fastapi import HTTPException
from core.config import settings

class TemplateLLMService:
    def __init__(self):
        google_api_key = settings.GOOGLE_API_KEY
        if not google_api_key:
            raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
        
        genai.configure(api_key=google_api_key)
        
        self.prompt_template_path = Path(__file__).parent / "prompts" / "generate_template_prompt.j2"
        if not self.prompt_template_path.is_file():
            raise RuntimeError(f"Arquivo de prompt não encontrado em: {self.prompt_template_path}")

    def _generate_prompt(self, doc_markdown: str, selections: list, template_name: str) -> str:
        selections_str = "\n".join([
            f"- Label: `{item.label}` -> Exemplo de Texto: `{item.context}`"
            for item in selections
        ])

        with open(self.prompt_template_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        prompt_text = prompt_text.replace("{{ doc_markdown }}", doc_markdown)
        prompt_text = prompt_text.replace(
            "{% for item in selections %}\n- Label: `{{ item.label }}` -> Exemplo de Texto: `{{ item.context }}`\n{% endfor %}",
            selections_str
        )
        prompt_text = prompt_text.replace("{{ template_name }}", template_name)
        prompt_text = prompt_text.replace("{{ template_name | replace('_', ' ') }}", template_name.replace('_', ' '))

        return prompt_text

    def generate_template_from_document(self, doc_markdown: str, selections: list, template_name: str) -> dict:
        prompt = self._generate_prompt(doc_markdown, selections, template_name)
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            response_text = response.text.strip()
            
            return json.loads(response_text)

        except Exception as e:
            print(f"Erro ao chamar a API do Gemini ou ao processar a resposta: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Não foi possível gerar o template via LLM. Verifique o log para mais detalhes."
            )