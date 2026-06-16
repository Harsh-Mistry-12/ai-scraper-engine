"""File handling utilities for reading and writing data files."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import pandas as pd
SUPPORTED_INPUT = {"csv", "xlsx", "json", "xml"}
SUPPORTED_OUTPUT = {"csv", "xlsx", "json", "xml"}
def detect_file_type(filename: str) -> str:
    """Return the file extension in lowercase without the dot."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext in SUPPORTED_INPUT:
        return ext
    raise ValueError(f"Unsupported file type: .{ext}. Supported: {', '.join(SUPPORTED_INPUT)}")
def read_file_to_df(filepath: str | Path, file_type: str | None = None) -> pd.DataFrame:
    """Read a data file into a pandas DataFrame."""
    filepath = Path(filepath)
    if file_type is None:
        file_type = detect_file_type(filepath.name)
    readers = {
        "csv": lambda p: pd.read_csv(p),
        "xlsx": lambda p: pd.read_excel(p, engine="openpyxl"),
        "json": lambda p: pd.read_json(p),
        "xml": lambda p: pd.read_xml(p),
    }
    reader = readers.get(file_type)
    if reader is None:
        raise ValueError(f"No reader for type: {file_type}")
    return reader(filepath)
def write_df_to_file(df: pd.DataFrame, filepath: str | Path, file_type: str | None = None) -> Path:
    """Write a DataFrame to a file in the given format. Returns the path."""
    filepath = Path(filepath)
    if file_type is None:
        file_type = detect_file_type(filepath.name)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    writers = {
        "csv": lambda d, p: d.to_csv(p, index=False),
        "xlsx": lambda d, p: d.to_excel(p, index=False, engine="openpyxl"),
        "json": lambda d, p: d.to_json(p, orient="records", indent=2),
        "xml": lambda d, p: d.to_xml(p, index=False),
    }
    writer = writers.get(file_type)
    if writer is None:
        raise ValueError(f"No writer for type: {file_type}")
    writer(df, filepath)
    return filepath
def df_to_preview(df: pd.DataFrame, max_rows: int = 20) -> dict[str, Any]:
    """Convert a DataFrame into a preview dict for the frontend."""
    preview_df = df.head(max_rows)
    return {
        "columns": list(df.columns),
        "rows": preview_df.to_dict(orient="records"),
        "total_rows": len(df),
        "preview_rows": len(preview_df),
    }
def get_file_schema(df: pd.DataFrame) -> dict[str, Any]:
    """Extract schema information from a DataFrame for AI context."""
    return {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "shape": list(df.shape),
        "sample_rows": df.head(3).to_dict(orient="records"),
        "null_counts": df.isnull().sum().to_dict(),
    }
