import json

import pymupdf

import pandas as pd


def extract_funcionarios(
    fixos_pdf_path: str,
    substitutos_pdf_path: str,
    output_path: str = "funcionarios.csv",
):
    page_fixos = pymupdf.open(fixos_pdf_path).load_page(0)
    tabs_fixos = page_fixos.find_tables()
    raw_fixos = tabs_fixos[0].extract()

    page_substitutos = pymupdf.open(substitutos_pdf_path).load_page(0)
    tabs_substitutos = page_substitutos.find_tables()
    raw_substitutos = tabs_substitutos[0].extract()

    funcionarios = [
        {"nome": func[1], "situacao": func[3], "substituto": False}
        for func in raw_fixos[3:]
    ]

    substitutos = set([func[4] for func in raw_substitutos[3:]])

    funcionarios.extend(
        [
            {"nome": func, "situacao": "TRABALHANDO", "substituto": True}
            for func in substitutos
        ]
    )

    funcionarios.sort(key=lambda x: x["nome"])
    df = pd.DataFrame(funcionarios)
    df.to_csv(output_path, index=False)

    return df
