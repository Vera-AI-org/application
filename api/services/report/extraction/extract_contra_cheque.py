import pdfplumber
import re
import pandas as pd
from difflib import SequenceMatcher

def extract_contra_cheque(caminho_pdf, lista_funcionarios, output_path):
    resultados = list()
    with pdfplumber.open(caminho_pdf) as pdf:
        texto_completo = ""
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"
    
    regex_split_por_funcionario = "Empr.:"
    partes_por_funcionarios = re.split(regex_split_por_funcionario, texto_completo)

    regex_nome = r"([A-Z\s]+)(?=\s+Situação)"
    regex_fgts = r"Valor FGTS:\s*([\d,.]+)"
    regex_inss = r"\bI\.N\.S\.S\.\s*[\d,]+\s*([\d,.]+)D"
    regex_vt = r"VALE TRANSPORTE\s*[\d,]+\s*([\d,.]+)D"

    for nome_funcionario in lista_funcionarios:
        encontrou = False
        for parte in partes_por_funcionarios:
            match_nome = re.search(regex_nome, parte)
            if not match_nome:
                continue
            
            nome_encontrado = match_nome.group(1).strip()

            similaridade = SequenceMatcher(None, nome_encontrado, nome_funcionario).ratio()
            if similaridade > 0.85:
                fgts = re.search(regex_fgts, parte)
                inss = re.search(regex_inss, parte)
                vt = re.search(regex_vt, parte)

                valor_fgts = float(fgts.group(1).replace('.', '').replace(',', '.')) if fgts else 0.0
                valor_inss = float(inss.group(1).replace('.', '').replace(',', '.')) if inss else 0.0
                valor_vt = float(vt.group(1).replace('.', '').replace(',', '.')) if vt else 0.0

                resultado = {
                    "nome": nome_encontrado,
                    "FGTS": valor_fgts > 0,
                    "INSS": valor_inss > 0,
                    "VT": valor_vt > 0
                }
                resultados.append(resultado)
                encontrou = True
                break 

        if not encontrou:
            resultados.append({
                "nome": nome_funcionario,
                "FGTS": False,
                "INSS": False,
                "VT": False
            })

    df = pd.DataFrame(resultados)
    df.to_csv(output_path, index=False)

    return df
