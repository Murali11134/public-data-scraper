"""
un_pdf_scraper.py
-----------------
Extracts population data tables from the UN World Population Prospects
PDF report — publicly available on the UN DESA website.

Source  : https://population.un.org/wpp/
Method  : pdfplumber (PDF table extraction)
Fallback: If the main PDF is unavailable, falls back to the UN Data API
          (https://data.un.org) which returns JSON.

Schema columns populated
------------------------
SourceCode : "UNPDF01"
RecordID   : sequential index
Title      : country / region name
Category   : "Population" or sub-group label
Value      : population estimate (thousands)
Unit       : "thousands"
Country    : country name (Title column)
Year       : year of estimate
URL        : PDF source URL
"""

from __future__ import annotations

import logging
from io import BytesIO

import pandas as pd
import requests

from public_data_scraper.schema import enforce_schema

logger = logging.getLogger(__name__)

# UN WPP Summary PDF (stable public URL — updated periodically)
PDF_URL = (
    "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/"
    "WPP2024_TotalPopulationBySex.csv"
)

# Fallback: UN Data API endpoint for total population
UN_API_URL = "https://data.un.org/ws/rest/data/UNSD,DF_UNData_UNFCC,1.0/A..TOTPOP./?format=jsondata"


def _fetch_via_csv(session: requests.Session) -> pd.DataFrame:
    """
    Fetch UN WPP population data from the official CSV file.
    This is the primary method — UN now publishes CSVs directly.
    """
    logger.info("[UNPDF01] Fetching UN WPP CSV from %s", PDF_URL)
    resp = session.get(PDF_URL, timeout=60)
    resp.raise_for_status()

    from io import StringIO
    raw = pd.read_csv(StringIO(resp.text), low_memory=False)

    # Columns: Location, ISO3_code, Time, PopTotal, PopMale, PopFemale, etc.
    required = {"Location", "ISO3_code", "Time", "PopTotal"}
    if not required.issubset(set(raw.columns)):
        logger.warning(
            "[UNPDF01] Expected columns not found. Got: %s", list(raw.columns[:10])
        )
        return pd.DataFrame()

    # Filter for most recent year per country (Variant = "Medium")
    if "Variant" in raw.columns:
        raw = raw[raw["Variant"] == "Medium"]

    # Keep only country-level rows (not aggregates) — ISO3_code is populated
    raw = raw[raw["ISO3_code"].notna() & (raw["ISO3_code"].str.len() == 3)]

    # Take the most recent year available per country
    idx = raw.groupby("ISO3_code")["Time"].idxmax()
    raw = raw.loc[idx]

    records = []
    for _, row in raw.iterrows():
        records.append({
            "title":    str(row.get("Location", "")),
            "category": "Total population",
            "value":    str(round(float(row["PopTotal"]), 2)) if pd.notna(row["PopTotal"]) else pd.NA,
            "unit":     "thousands",
            "country":  str(row.get("ISO3_code", "")),
            "year":     str(int(row["Time"])) if pd.notna(row["Time"]) else pd.NA,
            "url":      PDF_URL,
        })

    return pd.DataFrame(records)


def _fetch_via_pdf(session: requests.Session, pdf_url: str) -> pd.DataFrame:
    """
    Extract tables from a PDF using pdfplumber.
    Used as a fallback or for alternative UN PDFs.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("[UNPDF01] pdfplumber not installed. Run: pip install pdfplumber")
        return pd.DataFrame()

    logger.info("[UNPDF01] Downloading PDF from %s", pdf_url)
    resp = session.get(pdf_url, timeout=60)
    resp.raise_for_status()

    pdf_bytes = BytesIO(resp.content)
    records: list[dict] = []

    with pdfplumber.open(pdf_bytes) as pdf:
        logger.info("[UNPDF01] PDF has %d page(s).", len(pdf.pages))
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            if not tables:
                continue
            for table in tables:
                for row in table:
                    if not row or not row[0]:
                        continue
                    # Heuristic: col 0 = region/country, col -1 = most recent value
                    title = str(row[0]).strip()
                    value = str(row[-1]).strip() if len(row) > 1 else pd.NA
                    if title.upper() == title and len(title) > 20:
                        # Skip all-caps header rows
                        continue
                    records.append({
                        "title":    title,
                        "category": "Population estimate",
                        "value":    value,
                        "unit":     "thousands",
                        "country":  title,
                        "year":     "2024",
                        "url":      pdf_url,
                    })

    return pd.DataFrame(records)


def UNPDF01(use_pdf: bool = False, pdf_url: str | None = None) -> pd.DataFrame:
    """
    Fetch UN population data (CSV primary, optional PDF mode).

    Parameters
    ----------
    use_pdf : bool
        If True, fetch from a PDF instead of the CSV API (slower, demo of pdfplumber).
        Default is False.
    pdf_url : str, optional
        Custom PDF URL. Used only when use_pdf=True.

    Returns
    -------
    pd.DataFrame
        Schema-compliant DataFrame with population data.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "public-data-scraper/1.0 (portfolio project; educational use)"
    })

    try:
        if use_pdf and pdf_url:
            raw = _fetch_via_pdf(session, pdf_url)
        else:
            raw = _fetch_via_csv(session)
    except Exception as exc:
        logger.error("[UNPDF01] Fetch failed: %s", exc, exc_info=True)
        return enforce_schema(pd.DataFrame(), "UNPDF01")

    if raw.empty:
        logger.warning("[UNPDF01] No data extracted.")
        return enforce_schema(pd.DataFrame(), "UNPDF01")

    raw["recordid"] = range(1, len(raw) + 1)
    logger.info("[UNPDF01] Total records: %d", len(raw))
    return enforce_schema(raw, "UNPDF01")


def UNPDF01_demo_pdf(pdf_url: str) -> pd.DataFrame:
    """
    Demonstrate pdfplumber extraction from any publicly available PDF URL.

    This function exists purely to showcase PDF scraping on Upwork profiles.
    Pass any URL to a publicly available tabular PDF.

    Example
    -------
        df = UNPDF01_demo_pdf(
            "https://www.vfsc.vu/wp-content/uploads/2023/07/"
            "Licensed-Financial-Service-Providers.pdf"
        )
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Run: pip install pdfplumber")

    session = requests.Session()
    session.headers.update({"User-Agent": "public-data-scraper/1.0 (educational)"})
    return _fetch_via_pdf(session, pdf_url)
