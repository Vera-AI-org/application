import pandas as pd
import difflib
from pathlib import Path

from ..extraction import (
    extract_funcionarios,
    extract_cestabasica,
    extract_ponto_funcionarios,
    extract_contra_cheque
)
from ..llm.llm_service import LLMService

class ReportDataProcessor:
    def __init__(self, file_paths: dict[str, str], output_dir: Path):
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.funcionarios_list = []

    def _fuzzy_merge(self, df_left: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
        if df_right is None or df_right.empty: return df_left
        matched_names = []
        for name in df_left['nome']:
            matches = difflib.get_close_matches(name, df_right['nome'], n=1, cutoff=0.85)
            matched_names.append(matches[0] if matches else name)
        df_left_copy = df_left.copy()
        df_left_copy['nome'] = matched_names
        return pd.merge(df_left_copy, df_right, on='nome', how='left')

    def _extract_all(self) -> list[pd.DataFrame]:
        dataframes = []

        funcionarios_path = self.file_paths.get("funcionarios")
        substitutos_path = self.file_paths.get("funcionarios_substitutos")
        if funcionarios_path and substitutos_path:
            df_funcionarios = extract_funcionarios(
                fixos_pdf_path=funcionarios_path,
                substitutos_pdf_path=substitutos_path,
                output_path=str(self.output_dir / "funcionarios.csv")
            )
            self.funcionarios_list = df_funcionarios["nome"].tolist()
            dataframes.append(df_funcionarios)
        
        extraction_steps = [
            {"key": "cesta", "func": extract_cestabasica, "args": {"todos_funcionarios": self.funcionarios_list}},
            {"key": "cartao_pontos", "func": extract_ponto_funcionarios, "args": {}},
            {"key": "vt", "func": extract_contra_cheque, "args": {"lista_funcionarios": self.funcionarios_list}},
        ]

        for step in extraction_steps:
            file_path = self.file_paths.get(step["key"])
            if file_path:
                df = step["func"](
                    input_path=file_path,
                    output_path=str(self.output_dir / f"{step['key']}.csv"),
                    **step["args"]
                )
                dataframes.append(df)
        
        return dataframes

    def _merge_all(self, dataframes: list[pd.DataFrame]) -> pd.DataFrame:
        valid_dfs = [df for df in dataframes if df is not None and not df.empty]
        if not valid_dfs:
            return pd.DataFrame()

        merged_df = valid_dfs[0]
        for df in valid_dfs[1:]:
            merged_df = self._fuzzy_merge(merged_df, df)
        
        merged_df.fillna("", inplace=True)
        return merged_df

    def run(self) -> tuple[pd.DataFrame, str]:
        extracted_dfs = self._extract_all()
        final_df = self._merge_all(extracted_dfs)
        
        llm_service = LLMService()
        analysis_text = llm_service.generate_analysis(final_df)
        
        return final_df, analysis_text