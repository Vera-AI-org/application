import pymupdf4llm
import tempfile
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from models import document_model
from api.schemas import document_schema

async def create_document(db: Session, user_id: int, file: UploadFile) -> document_schema.DocumentSchema:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de arquivo inválido. Apenas PDFs são aceitos."
        )

    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.seek(0)
            
            md_text = pymupdf4llm.to_markdown(temp_file.name)

        if not md_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível extrair conteúdo do PDF. O arquivo pode estar vazio ou corrompido."
            )

        new_document = document_model.Document(
            user_id=user_id,
            file_name=file.filename,
            markdown_content=md_text
        )
        
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        return new_document

    except Exception as e:
        db.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao processar o arquivo: {e}"
        )