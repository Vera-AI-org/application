import pdfplumber
import re
import json
import pandas as pd

def extract_ponto_funcionarios(pdf_path: str, output_path: str):
    regex_nome_funcionario = r'NOME DO FUNCIONÁRIO: (.+?)(?: ENT.|\b HORÁRIO\b|$)'
    regex_total = r'TOTAIS\s+([\d+:.]+)'
    regex_data_inicio = r'DE\s+(\d{2}\/\d{2}\/\d{4})'
    regex_data_fim = r'ATÉ\s+(\d{2}\/\d{2}\/\d{4})'

    funcionarios = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            nome_match = re.search(regex_nome_funcionario, text)
            total_match = re.search(regex_total, text)
            data_inicio_match = re.search(regex_data_inicio, text)
            data_fim_match = re.search(regex_data_fim, text)

            funcionario = {
                "nome": nome_match.group(1).strip() if nome_match else "",
                "total_horas": total_match.group(1).strip() if total_match else "",
                "data_inicio": data_inicio_match.group(1) if data_inicio_match else "",
                "data_fim": data_fim_match.group(1) if data_fim_match else "",
            }

            funcionarios.append(funcionario)
        pdf.close()
    
    df = pd.DataFrame(funcionarios)
    df.to_csv(output_path, index=False)
        
    return df