import difflib
from src.extraction import *
from src.llm.model import get_llm_response
import pandas as pd
import json

def fuzzy_merge_difflib(df_left, df_right, key='nome', threshold=0.85, suffix='_right'):
    """
    Fuzzy merge two DataFrames using difflib on the specified key column.
    """
    matched_names = []

    for name in df_left[key]:
        # Get closest match (returns a list)
        matches = difflib.get_close_matches(name, df_right[key], n=1, cutoff=threshold)
        matched_names.append(matches[0] if matches else name)

    df_left[key] = matched_names

    # Merge on fuzzy-matched name
    merged = pd.merge(df_left, df_right, on=key, how='left')

    return merged


def processamento(pdfs: dict, output_path: str = "resultado.csv") -> dict:

    cesta_basica_path = pdfs.get("cesta")
    folha_ponto_path = pdfs.get("cartao_pontos")
    funcionarios_path = pdfs.get("funcionarios")
    funcionarios_substitutos_path = pdfs.get("funcionarios_substitutos")
    contra_cheque_path = pdfs.get("vt")

    funcionarios_df = extract_funcionarios(
        funcionarios_path, 
        funcionarios_substitutos_path
    ) if funcionarios_path and funcionarios_substitutos_path else None

    cesta_basica_df = extract_cestabasica(
        cesta_basica_path,
        funcionarios_df["nome"].tolist()
    ) if cesta_basica_path else None
    
    folha_ponto_df = extract_ponto_funcionarios(folha_ponto_path, "folho_ponto_saida.csv") if folha_ponto_path else None

    contra_cheque_df = extract_contra_cheque(
        contra_cheque_path, 
        funcionarios_df["nome"].tolist() if funcionarios_df is not None else []
    ) if contra_cheque_path and funcionarios_df is not None else None

    df_list = [
        funcionarios_df,
        cesta_basica_df,
        folha_ponto_df,
        contra_cheque_df
    ]

    # Initialize with the first DataFrame
    merged_df = df_list[0]

    # Iterate and merge the rest
    for i in range(1, len(df_list)):
        merged_df = fuzzy_merge_difflib(
            merged_df, 
            df_list[i], 
            key='nome', 
            threshold=0.85, 
            suffix=f'_df{i}'
        )
        print(merged_df)
    
    merged_df.fillna("", inplace=True)

    merged_df.to_csv(output_path, index=False)

    analysis = ""

    retorno = {
        "data": merged_df.to_dict(orient='records'),
        "analise": analysis
    }

    json.dump(retorno, open("resultado.json", "w"), ensure_ascii=False, indent=4)

    return retorno