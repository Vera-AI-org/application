import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Any

from models import document_model, template_model, field_model, extraction_model


def _segment_by_pattern(content: str, strategy_details: Dict[str, Any]) -> List[str]:
    pattern = strategy_details.get("pattern")
    if not pattern:
        raise ValueError("A estratégia 'pattern' requer uma chave 'pattern' com uma regex válida.")
    
    parts = re.split(f'({pattern})', content)
    
    blocks = [parts[0]] if parts and parts[0].strip() else []
    
    it = iter(parts[1:])
    for delimiter, text_block in zip(it, it):
        blocks.append(delimiter + text_block)
        
    return [block for block in blocks if block.strip()]

def _segment_by_page(content: str) -> List[str]:
    blocks = re.split(r'--- PAGE \d+ ---', content)
    return [block.strip() for block in blocks if block.strip()]

def _segment_by_table_row(content: str) -> List[Dict[str, str]]:
    table_match = re.search(r'(\|.*\|(?:\n|\r\n?))(\| *[:-]+ *\|.*(?:\n|\r\n?))((?:\|.*\|(?:\n|\r\n?))+)', content)
    if not table_match:
        return []

    table_str = table_match.group(0)
    lines = [line.strip() for line in table_str.strip().split('\n')]
    
    headers = [h.strip() for h in lines[0].strip('|').split('|')]
    
    rows = []
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
            
    return rows

def _apply_extraction(block: Any, fields: List[field_model.Field], strategy: str) -> Dict[str, Any]:
    extracted_data = {}
    
    if strategy in ["pattern", "page"]:
        if not isinstance(block, str): return {}
        for field in fields:
            match = re.search(field.extraction_pattern, block, re.DOTALL | re.IGNORECASE)
            if match:
                value = match.group(1).strip() if match.groups() else match.group(0).strip()
                extracted_data[field.label] = value
            elif field.is_required:
                extracted_data[field.label] = None
                
    elif strategy == "table_row":
        if not isinstance(block, dict): return {} # Guarda de segurança
        for field in fields:
            column_name = field.extraction_pattern
            value = block.get(column_name)
            
            if value is not None:
                extracted_data[field.label] = value.strip()
            elif field.is_required:
                extracted_data[field.label] = None

    return extracted_data

async def extract_from_document(db: Session, user_id: int, document_id: int, template_id: int) -> Dict[str, Any]:
    document = db.query(document_model.Document).filter(
        document_model.Document.id == document_id,
        document_model.Document.user_id == user_id
    ).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    template = db.query(template_model.Template).filter(
        template_model.Template.id == template_id,
        template_model.Template.user_id == user_id
    ).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template não encontrado.")

    content = document.markdown_content
    strategy_info = template.segmentation_strategy
    strategy_name = strategy_info.get("strategy")
    
    blocks = []
    errors = []

    try:
        if strategy_name == "pattern":
            blocks = _segment_by_pattern(content, strategy_info)
        elif strategy_name == "page":
            blocks = _segment_by_page(content)
        elif strategy_name == "table_row":
            blocks = _segment_by_table_row(content)
        else:
            errors.append(f"Estratégia de segmentação '{strategy_name}' não é suportada.")
    except Exception as e:
        errors.append(f"Falha ao executar a segmentação '{strategy_name}': {e}")

    if not blocks and not errors:
        errors.append("Nenhum bloco de dados foi encontrado no documento usando a estratégia do template.")
    
    results = []
    for block in blocks:
        extracted_data = _apply_extraction(block, template.fields, strategy_name)
        if any(v is not None for v in extracted_data.values()):
            results.append(extracted_data)

    new_extraction = extraction_model.Extraction(
        user_id=user_id,
        document_id=document_id,
        template_id=template_id,
        data=results,
        errors=errors
    )
    db.add(new_extraction)
    db.commit()
    db.refresh(new_extraction)
    
    return new_extraction