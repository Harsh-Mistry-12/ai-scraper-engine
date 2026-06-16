"""Data transformer — converts raw scraped data to user's desired output format."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any
import pandas as pd
from utils.file_handler import write_df_to_file, df_to_preview
import config
logger = logging.getLogger(__name__)
class DataTransformer:
    """Transforms raw scraped data into structured output."""
    def transform(
        self,
        raw_data: list[dict[str, Any]],
        desired_fields: list[str] | None = None,
        column_mapping: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """
        Transform raw scraped data into a clean DataFrame.
        Args:
            raw_data: List of dicts from the scraping engine.
            desired_fields: If provided, only keep these fields (in order).
            column_mapping: If provided, rename columns {old: new}.
        """
        if not raw_data:
            return pd.DataFrame()
        df = pd.DataFrame(raw_data)
        # Rename columns if mapping provided
        if column_mapping:
            df = df.rename(columns=column_mapping)
        # Filter to desired fields if specified
        if desired_fields:
            existing = [f for f in desired_fields if f in df.columns]
            if existing:
                df = df[existing]
        # Clean data
        df = self._clean_data(df)
        return df
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply basic data cleaning."""
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace empty strings and 'None' with actual NaN
            df[col] = df[col].replace({"": pd.NA, "None": pd.NA, "nan": pd.NA})
        # Drop completely empty rows
        df = df.dropna(how="all")
        # Drop duplicate rows
        df = df.drop_duplicates()
        # Reset index
        df = df.reset_index(drop=True)
        return df
    def get_preview(self, df: pd.DataFrame, max_rows: int = 20) -> dict[str, Any]:
        """Get a preview of the transformed data."""
        return df_to_preview(df, max_rows)
    def export(
        self,
        df: pd.DataFrame,
        session_id: str,
        output_format: str = "csv",
        filename: str | None = None,
    ) -> Path:
        """Export the DataFrame to a file in the output directory."""
        if filename is None:
            filename = f"scraped_data_{session_id[:8]}.{output_format}"
        filepath = config.OUTPUT_DIR / filename
        return write_df_to_file(df, filepath, output_format)
