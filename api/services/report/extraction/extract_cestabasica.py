import pandas as pd
import pdfplumber
import json
import logging 
import argparse
import pymupdf
import difflib
import re
import unicodedata

logging.getLogger("pdfminer").setLevel(logging.ERROR)

def extrair_texto_pdf(caminho_pdf):
    paginas = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            paginas.append(pagina.extract_text())
    return paginas

def separate_pdf_content_from_list(contents):
    recibos = []
    assinaturas = []

    for content in contents:
        documents = re.split(r'(?=RECIBO DE ENTREGA DE CESTA BÁSICA)', content)

        for doc in documents:
            if not doc.strip():
                continue

            split_index = doc.find("Assinaturas")
            if split_index != -1:
                recibo_part = doc[:split_index].strip()
                if recibo_part:
                    recibos.append(recibo_part)

                assinatura_part = doc[split_index:].strip()
                if assinatura_part:
                    assinaturas.append(assinatura_part)
            else:
                if doc.strip():
                    recibos.append(doc.strip())

    return recibos, assinaturas

def save_lists_to_files(recibos, assinaturas, recibo_file, assinatura_file):
    with open(recibo_file, 'w', encoding='utf-8') as f:
        for i, recibo in enumerate(recibos, 1):
            f.write(f"Recibo {i}:\n{recibo}\n\n{'-'*50}\n\n")

    with open(assinatura_file, 'w', encoding='utf-8') as f:
        for i, assinatura in enumerate(assinaturas, 1):
            f.write(f"Assinatura {i}:\n{assinatura}\n\n{'-'*50}\n\n")

def normalize_name(name):
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn').lower()
    # Remove espaços extras e hífens
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'[-]', '', name)
    return name

def extract_name_from_receipt(receipt_text):
    # Expressão adaptada para letras maiúsculas com ou sem acento e espaços
    match = re.search(r'Funcionário: ([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s\.]+) \d+', receipt_text)
    name = match.group(1).strip() if match else None
    print(f"extract_name_from_receipt - Recibo - Nome extraído: {name}")
    return name

def extract_name_from_signature_log(signature_text):
    # Extrai nome de "NOME Assinou" no log, incluindo acentos e cedilha
    match = re.search(r'([A-Za-zÀ-ÖØ-öø-ÿ\s\.]+) Assinou(?: \([a-f0-9-]+\))? - Email:', signature_text)
    name = match.group(1).strip() if match else None
    print(f"extract_name_from_signature_log - Log de assinatura - Nome extraído: {name}")
    return name


def extract_document_code(text):
    # Extrai código do documento (UUID)
    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text, re.IGNORECASE)
    code = match.group(0).lower() if match else None
    print(f"extract_document_code -Código do documento: {code}")
    return code

def extract_missing(unique_list, full_list):
    nomes = [pessoa['nome'] for pessoa in unique_list]
    missing = []
    for others in full_list:
        close_matches = difflib.get_close_matches(others, nomes, n=1, cutoff=0.8)
        if len(close_matches) == 0:

            missing.append({
            'nome': others,
            'tem_recibo': False,
            'tem_assinatura': False,
            'observacao': "Não consta na lista de recibos da cesta básica"
        })
    return missing


def check_receipts_and_signatures(recibos, assinaturas, todos_funcionarios, output_file):
    status_list = []  # Lista de status: nome, tem recibo, tem assinatura

    # Dicionário de logs de assinaturas por código de documento
    signature_logs = {}
    for sig in assinaturas:
        doc_code = extract_document_code(sig)
        if doc_code:
            signature_logs[doc_code] = sig
            print(f"Log de assinatura registrado para UUID: {doc_code}")

    # Processa lista de recibos (recibo e metadados alternados)
    i = 0
    while i < len(recibos):
        receipt = recibos[i]
        receipt_name = extract_name_from_receipt(receipt)
        receipt_doc_code = extract_document_code(receipt)

        if not receipt_name or not receipt_doc_code:
            print(f"Recibo inválido, pulando (nome: {receipt_name}, UUID: {receipt_doc_code})")
            i += 1
            continue

        # Verifica metadados de assinatura (próxima entrada, se houver)
        signature_name = None
        has_signature = False
        observation = "Sem observação"

        signature_name = extract_name_from_signature_log(signature_logs[receipt_doc_code])

        # Compara nomes normalizados
        if signature_name:
            norm_receipt_name = normalize_name(receipt_name)
            norm_signature_name = normalize_name(signature_name)
            print(f"Comparando nomes normalizados: {norm_receipt_name} vs {norm_signature_name}")
            if norm_receipt_name == norm_signature_name:
                has_signature = True
            else:
                close_matches = difflib.get_close_matches(norm_receipt_name, [norm_signature_name], n=1, cutoff=0.8)
                if len(close_matches) > 0:
                  has_signature = True

                print(f"Nomes não correspondem: {receipt_name} (recibo) vs {signature_name} (assinatura)")
                observation = f"Nomes não correspondem: {receipt_name} (recibo) vs {signature_name} (assinatura)"
        else:
            print(f"Sem assinatura encontrada para {receipt_name}, UUID: {receipt_doc_code}")

        # Adiciona à lista de status
        i += 1

        # Adiciona à lista de status
        status_list.append({
            'nome': receipt_name,
            'tem_recibo': True,
            'tem_assinatura': True if has_signature else False,
            'observacao': observation
        })

    # Remove duplicatas na lista de status
    seen_names = set()
    unique_status_list = []
    for status in status_list:
        if status['nome'] not in seen_names:
            unique_status_list.append(status)
            seen_names.add(status['nome'])


    for miss in extract_missing(unique_status_list, todos_funcionarios):
        unique_status_list.append(miss)
    df = pd.DataFrame(unique_status_list)

    with open(output_file, "w", encoding="utf-8") as f:
        df.to_csv(output_file, index=False)
    
    return df
    
def extract_cestabasica(input_path: str, todos_funcionarios: list, output_path: str):    
    paginas = extrair_texto_pdf(input_path)
    recibos, assinaturas = separate_pdf_content_from_list(paginas)
    return check_receipts_and_signatures(recibos, assinaturas, todos_funcionarios, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("all_employers")
    parser.add_argument("output_path")
    args = parser.parse_args()
    extract_cestabasica(args.input_path, args.all_employers, args.output_path)
