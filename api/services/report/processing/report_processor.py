import pandas as pd
from pathlib import Path
import difflib
from typing import List, Dict, Any, Tuple

from core.logging import get_logger

from ..extraction.extract_funcionarios import extract_funcionarios
from ..extraction.extract_cestabasica import extract_cestabasica
from ..extraction.extract_ponto_funcionarios import extract_ponto_funcionarios
from ..extraction.extract_contra_cheque import extract_contra_cheque
from ..llm.llm_service import LLMService

logger = get_logger(__name__)

class ReportDataProcessor:
    def __init__(self, file_paths: Dict[str, str], output_dir: Path, llm_service: LLMService):
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.llm_service = llm_service

    def _fuzzy_merge(self, df_left: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
        if df_right is None or df_right.empty: return df_left
        matched_names = []
        for name in df_left['nome']:
            matches = difflib.get_close_matches(name, df_right['nome'], n=1, cutoff=0.85)
            matched_names.append(matches[0] if matches else name)
        df_left_copy = df_left.copy()
        df_left_copy['nome'] = matched_names
        return pd.merge(df_left_copy, df_right, on='nome', how='left')

    def _extract_base_data(self) -> Tuple[pd.DataFrame | None, List[str]]:
        logger.info("Extracting base employee data...")
        funcionarios_path = self.file_paths.get("funcionarios")
        substitutos_path = self.file_paths.get("funcionarios_substitutos")
        
        if not (funcionarios_path and substitutos_path):
            logger.warning("Employee or substitute files not provided. Cannot extract base data.")
            return None, []

        df_funcionarios = extract_funcionarios(
            fixos_pdf_path=funcionarios_path,
            substitutos_pdf_path=substitutos_path,
            output_path=str(self.output_dir / "funcionarios.csv")
        )
        nomes_funcionarios = df_funcionarios["nome"].tolist() if df_funcionarios is not None else []
        logger.info(f"Found {len(nomes_funcionarios)} employees.")
        return df_funcionarios, nomes_funcionarios

    def _extract_dependent_data(self, nomes_funcionarios: List[str]) -> List[pd.DataFrame]:
        dataframes = []
        
        if cesta_path := self.file_paths.get("cesta"):
            logger.info("Extracting 'cesta basica' data...")
            dataframes.append(extract_cestabasica(
                input_path=cesta_path, todos_funcionarios=nomes_funcionarios,
                output_path=str(self.output_dir / "cesta.csv")
            ))

        if ponto_path := self.file_paths.get("cartao_pontos"):
            logger.info("Extracting 'ponto' data...")
            dataframes.append(extract_ponto_funcionarios(
                pdf_path=ponto_path, output_path=str(self.output_dir / "cartao_pontos.csv")
            ))

        if vt_path := self.file_paths.get("vt"):
            logger.info("Extracting 'contra-cheque' data...")
            dataframes.append(extract_contra_cheque(
                caminho_pdf=vt_path, lista_funcionarios=nomes_funcionarios,
                output_path=str(self.output_dir / "vt.csv")
            ))
            
        return dataframes

    def _merge_all(self, dataframes: list[pd.DataFrame]) -> pd.DataFrame:
        valid_dfs = [df for df in dataframes if df is not None and not df.empty]
        if not valid_dfs: return pd.DataFrame()
        merged_df = valid_dfs[0]
        for df in valid_dfs[1:]:
            merged_df = self._fuzzy_merge(merged_df, df)
        merged_df.fillna("", inplace=True)
        return merged_df

    def run(self) -> Tuple[pd.DataFrame, str]:
        logger.info("Report data processing pipeline started.")
        
        df_funcionarios, nomes_funcionarios = self._extract_base_data()
        
        all_dataframes = [df_funcionarios]
        all_dataframes.extend(self._extract_dependent_data(nomes_funcionarios))
        
        logger.info("Merging all dataframes...")
        final_df = self._merge_all(all_dataframes)
        
        logger.info("Generating analysis with LLM...")
        analysis_text = self.llm_service.generate_analysis(final_df)
        
        logger.info("Report data processing pipeline finished successfully.")
        return final_df, analysis_text