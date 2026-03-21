"""
schema.py
---------
Canonical output schema and enforce_schema() shared across all scrapers.

Every scraper in this project returns a DataFrame with exactly these columns.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: list[str] = [
    "SourceCode",
    "RecordID",
    "Title",
    "Category",
    "Value",
    "Unit",
    "Country",
    "Year",
    "URL",
]

_ALIASES: dict[str, str] = {c.lower(): c for c in REQUIRED_COLUMNS}
_ALIASES.update({
    "sourcecode": "SourceCode",
    "recordid":   "RecordID",
    "title":      "Title",
    "category":   "Category",
    "value":      "Value",
    "unit":       "Unit",
    "country":    "Country",
    "year":       "Year",
    "url":        "URL",
})

_NULLISH = {"", "nan", "None", "NaN", "none", "N/A", "n/a", "null", "NULL"}


def enforce_schema(df: pd.DataFrame, source_code: str) -> pd.DataFrame:
    """
    Normalise any raw DataFrame into the canonical 9-column schema.

    Parameters
    ----------
    df : pd.DataFrame
        Raw scraped data (any column naming convention).
    source_code : str
        Unique source identifier, e.g. ``"BOOKS01"``.

    Returns
    -------
    pd.DataFrame
        Clean, schema-compliant DataFrame with REQUIRED_COLUMNS.
    """
    if df is None or df.empty:
        logger.debug("[%s] enforce_schema received empty input.", source_code)
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = df.copy()

    # Rename via alias map (case-insensitive)
    rename_map = {
        col: _ALIASES[col.lower()]
        for col in df.columns
        if col.lower() in _ALIASES
    }
    df.rename(columns=rename_map, inplace=True)

    # Add any missing required columns
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    # Clean values
    for col in REQUIRED_COLUMNS:
        df[col] = df[col].astype(str).str.strip().replace(_NULLISH, pd.NA)

    # Stamp source code
    df["SourceCode"] = source_code

    # Drop rows with no title
    before = len(df)
    df = df[df["Title"].notna()]
    dropped = before - len(df)
    if dropped:
        logger.debug("[%s] Dropped %d row(s) with missing Title.", source_code, dropped)

    logger.info("[%s] enforce_schema → %d record(s).", source_code, len(df))
    return df[REQUIRED_COLUMNS].reset_index(drop=True)
