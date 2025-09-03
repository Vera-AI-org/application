import pymupdf4llm
import re
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import pdfplumber
from models.pattern_model import Pattern
from .llm.llm_service import LLMService
from core.logging import get_logger
from models.document_model import Document
from models.template_model import Template
import tempfile
import regex as re
import unicodedata
import fitz
from fuzzysearch import find_near_matches
import markdown2
from bs4 import BeautifulSoup
from core.email.email_service import send_extraction_email
from pydantic import EmailStr

logger = get_logger(__name__)

class DocumentService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def upload_file(self, file: UploadFile):
        md_text = await self._extractor_text_from_pdf_to_markdown(file)

        new_document = Document(
                user_id=self.user_id,
                document_md=md_text, 
            )
        
        self.db.add(new_document)
        self.db.commit()
        self.db.refresh(new_document)

        return new_document


    async def _extractor_text_from_pdf_to_markdown(self, file: UploadFile) -> str:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            md_text = pymupdf4llm.to_markdown(temp_file.name)
            html = markdown2.markdown(md_text)

        return html
    
    async def _extractor_text_from_pdf_to_markdown_pairs(self, file: UploadFile) -> list[str]:
        html_list = []

        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            doc = fitz.open(temp_file.name)
            num_pages = doc.page_count

            for i in range(0, num_pages, 2):
                start = i
                end = min(i + 2, num_pages)

                md_text = pymupdf4llm.to_markdown(temp_file.name, pages=range(start, end))
                html = markdown2.markdown(md_text)
                html_list.append(html)

        return html_list

    async def save_pattern(self, template_id: int, name: str, description: str, is_section: bool):       
        new_pattern = Pattern(
                user_id= self.user_id,
                template_id=template_id,
                name=name,
                pattern=description,
                is_section=is_section
            )
        
        self.db.add(new_pattern)
        self.db.commit()
        self.db.refresh(new_pattern)
        return new_pattern

    async def process_document(self, template_id: int, file: UploadFile):
        file_html_list = await self._extractor_text_from_pdf_to_markdown_pairs(file)
        section = self.db.query(Pattern).filter(Pattern.template_id == template_id).first()
        
        patterns_text = [{section.name : section.pattern}] 
        patterns_all = self.db.query(Pattern).all()
        for p in patterns_all:
            print(p.id, p.template_id, p.name, p.pattern, p.is_section)

        patterns = self.db.query(Pattern).filter(
            Pattern.template_id == template_id,
            Pattern.is_section == False
        ).all()
        print(patterns)
        for pattern in patterns:
            patterns_text.append({pattern.name: pattern.pattern})

        file_result = LLMService().process_document(file_html_list, patterns_text)
        return file_result

    async def generate_regex(self, selected_datas: list, document_id: int, is_section: bool):
        document = self.db.query(Document).filter(Document.id == document_id).first()
        case = await self._format_case_section(document.document_md, selected_datas)

        regex = await self._generate_regex_from_selected_text(case)
        
        new_pattern = Pattern(
                user_id= self.user_id,
                document_id= document_id,
                name="name",
                pattern=regex,
                is_section=is_section
            )
        
        self.db.add(new_pattern)
        self.db.commit()
        self.db.refresh(new_pattern)
        return new_pattern
    
    async def delete_pattern_by_id(self, pattern_id: int):
        pattern_to_delete = self._get_pattern_by_id(pattern_id)
        
        self.db.delete(pattern_to_delete)
        self.db.commit()

        return {"message": f"Pattern with ID {pattern_id} successfully deleted."}

    async def get_pattern_by_id(self, pattern_id: int):
        pattern = self.db.query(Pattern).filter(
            Pattern.id == pattern_id,
            Pattern.user_id == self.user_id 
        ).first()

        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Pattern not found or permission denied"
            )
        
        return pattern

    async def _format_case_pattern(self, document, selected_datas):
        case = ''
        section_regex = self.db.query(Pattern).filter(Pattern.document_id == document.id and Pattern.is_section == True).first().pattern

        sections = re.split(section_regex, document.document_md, flags=re.DOTALL | re.MULTILINE)[1:]

        for selected_data in selected_datas:
            for section in sections:
                if selected_data in section:
                    case += f"Texto: {section}\n Resultados esperados: {selected_data}\n"
                    sections.remove(section)
        return case
            
    def fuzzy_find(self, text, pattern, max_l_dist=50):
        matches = find_near_matches(pattern, text, max_l_dist=max_l_dist)
        return matches[0].start if matches else -1

    def _extract_text_from_html(self, html_string: str) -> str:
        if not html_string:
            return ""
        soup = BeautifulSoup(html_string, 'html.parser')
        text = soup.get_text()
        
        return re.sub(r'\s+', ' ', text).strip()

    async def _format_case_section(self, document_md, selected_datas):
        document_text = self._extract_text_from_html(document_md)
        print(document_text[0:500])
        extracted_data = [str(data) for data in selected_datas]

        case = ""
        for i, selected_data in enumerate(extracted_data):
            selected_data = self._extract_text_from_html(selected_data)
            start = self.fuzzy_find(document_text, selected_data)
            print(selected_data)
            print(start)

            if start != -1:
                end = start + len(selected_data)

                left_start = max(0, start - 20)
                right_end = min(len(document_text), end + 20)

                left_context = document_text[left_start:start]
                right_context = document_text[end:right_end]

                context = left_context + selected_data + right_context
                case += f"Texto {i}:\n {context}\nResultados esperados {i}: \n{selected_data}\n"

        return case


    async def _generate_regex_from_selected_text(self, case: str) -> str:
        llm_service = LLMService()

        regex = llm_service.generate_regex(case)
        return regex
    
    async def _extract_text_from_pdf(self, file: UploadFile) -> str:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file.seek(0)
                
                text = ""
                with pdfplumber.open(temp_file.name) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Falha ao extrair texto do PDF: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível processar o arquivo PDF."
            )
        
    async def apply_regex_to_pdf(self, template_id: int, file: UploadFile) -> dict:
        logger.info(f"Iniciando extração para o document_id: {template_id}")

        template = self.db.query(Template).filter(
            Template.id == template_id,
            Template.user_id == self.user_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template com ID {template_id} não encontrado ou você não tem permissão."
            )
        
        section_pattern = None
        value_patterns = []
        for p in template.patterns:
            if p.is_section:
                section_pattern = p
            else:
                value_patterns.append(p)

        if not section_pattern:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O template com ID {template_id} não possui um padrão de seção (is_section=True)."
            )
        if not value_patterns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O template com ID {template_id} não possui padrões de extração (is_section=False)."
            )


        pdf_text = await self._extract_text_from_pdf(file)

        try:
            text_blocks = re.split(f'({section_pattern.pattern})', pdf_text, flags=re.DOTALL | re.MULTILINE)[1:]
            blocks = [text_blocks[i] + text_blocks[i+1] for i in range(0, len(text_blocks), 2)]

        except re.error as e:
            logger.error(f"Regex de seção inválido para o padrão '{section_pattern.name}' (ID: {section_pattern.id}): {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro no regex do padrão de seção."
            )

        final_results = []
        for block_text in blocks:
            if not block_text.strip():
                continue

            extracted_item = {}
            for vp in value_patterns:
                try:
                    match = re.search(vp.pattern, block_text, flags=re.DOTALL | re.MULTILINE)
                    extracted_item[vp.name] = match.group(1).strip() if match and match.groups() else match.group(0).strip() if match else None
                except re.error:
                    logger.warning(f"Regex de valor inválido para o padrão '{vp.name}' (ID: {vp.id}). Pulando.")
                    extracted_item[vp.name] = "Erro de extração"
            
            final_results.append(extracted_item)
        
        logger.info(f"Extração para o template_id: {template_id} concluída. {len(final_results)} itens encontrados.")
        return final_results


async def handle_file_upload(db: Session, user_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.upload_file(file) 

async def handle_generate_regex(db: Session, user_id: int, pattern_data: list, document_id: int, is_section: bool):
    service = DocumentService(db=db, user_id=user_id)
    return await service.generate_regex(pattern_data, document_id, is_section) 

async def handle_apply_regex(db: Session, user_id: int, template_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.apply_regex_to_pdf(template_id, file)

async def handle_delete_regex(db: Session, user_id: int, pattern_id: int):
    service = DocumentService(db=db, user_id=user_id)
    return await service.delete_regex_by_id(pattern_id)

async def handle_save_pattern(db: Session, user_id: int, template_id:int, name: str, description: str, is_section: bool):
    service = DocumentService(db=db, user_id=user_id)
    return await service.save_pattern(template_id, name, description, is_section)

async def handle_process_document(db: Session, user_id: int, template_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.process_document(template_id, file)

async def handle_process_document_background(db: Session, user_id: int, user_email: EmailStr, template_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    extracted_data = await service.process_document(template_id, file)
    await send_extraction_email(email_to=user_email, results=extracted_data)