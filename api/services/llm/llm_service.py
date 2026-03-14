import json
from openai import OpenAI
from core.config import settings


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def extract_fields(self, document_text: str, fields: list) -> dict:
        """
        Extract all fields from document text.
        fields: list of Field objects with .name and .description
        Returns: dict {field_name: extracted_value}
        """
        field_descriptions = "\n".join([
            f"- {f.name}: {f.description}" for f in fields
        ])

        prompt = f"""Você é um assistente especializado em extração de dados de documentos trabalhistas brasileiros.

Extraia as seguintes informações do documento abaixo:
{field_descriptions}

Retorne APENAS um objeto JSON válido com os nomes dos campos como chaves e os valores extraídos como valores.
Se um campo não for encontrado no documento, use null.

Documento:
{document_text[:8000]}"""

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )

        return json.loads(response.choices[0].message.content)
