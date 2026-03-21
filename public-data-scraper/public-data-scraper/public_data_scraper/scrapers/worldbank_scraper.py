"""
worldbank_scraper.py
--------------------
Fetches development indicators from the World Bank Open Data API.

Source  : https://api.worldbank.org/v2/
Method  : REST API → JSON (no authentication required)
Docs    : https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

Indicators collected (configurable via INDICATORS dict)
--------------------------------------------------------
NY.GDP.MKTP.CD   GDP (current US$)
SP.POP.TOTL      Population, total
SI.POV.GINI      Gini index (inequality)
SH.XPD.CHEX.GD.ZS  Current health expenditure (% of GDP)
SE.ADT.LITR.ZS   Literacy rate, adult total (% of people 15+)

Schema columns populated
------------------------
SourceCode : "WBAPI01"
RecordID   : "{country_code}_{indicator_code}_{year}"
Title      : indicator name (e.g. "GDP (current US$)")
Category   : indicator group (e.g. "Economy", "Health")
Value      : numeric value as string
Unit       : unit description (e.g. "current US$", "% of GDP")
Country    : ISO 3-letter country code
Year       : year of measurement
URL        : API endpoint used
"""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from public_data_scraper.config import settings
from public_data_scraper.schema import enforce_schema

logger = logging.getLogger(__name__)

API_BASE = "https://api.worldbank.org/v2"

# Indicator code → (display name, category, unit)
INDICATORS: dict[str, tuple[str, str, str]] = {
    "NY.GDP.MKTP.CD":         ("GDP",                          "Economy",    "current US$"),
    "SP.POP.TOTL":            ("Total population",             "Demographics","persons"),
    "SI.POV.GINI":            ("Gini index",                   "Inequality", "index 0-100"),
    "SH.XPD.CHEX.GD.ZS":     ("Health expenditure",           "Health",     "% of GDP"),
    "SE.ADT.LITR.ZS":        ("Adult literacy rate",           "Education",  "% age 15+"),
}


def _create_session() -> requests.Session:
    """Create a requests session with retry strategy."""
    session = requests.Session()
    retry = Retry(
        total=settings.max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "public-data-scraper/1.0 (portfolio project; educational use)"
    })
    return session


def _fetch_indicator(
    session: requests.Session,
    indicator: str,
    country: str = "all",
    date_range: str = "2015:2023",
    per_page: int = 500,
) -> list[dict[str, Any]]:
    """
    Fetch all pages for one indicator from the World Bank API.

    Returns a flat list of raw data-point dicts.
    """
    url = f"{API_BASE}/country/{country}/indicator/{indicator}"
    params: dict[str, Any] = {
        "format":   "json",
        "per_page": per_page,
        "date":     date_range,
        "mrv":      1,          # most recent value
    }

    results: list[dict] = []
    page = 1

    while True:
        params["page"] = page
        resp = session.get(url, params=params, timeout=settings.request_timeout)
        resp.raise_for_status()

        data = resp.json()

        # World Bank returns [metadata, [records]] or [{"message": ...}]
        if not isinstance(data, list) or len(data) < 2:
            logger.warning("[WBAPI01] Unexpected response format for %s.", indicator)
            break

        meta    = data[0]
        records = data[1] or []

        for rec in records:
            if rec.get("value") is None:
                continue
            results.append({
                "country_code": rec.get("countryiso3code", ""),
                "country_name": rec.get("country", {}).get("value", ""),
                "year":         rec.get("date", ""),
                "value":        str(rec.get("value", "")),
            })

        total_pages = meta.get("pages", 1)
        if page >= total_pages:
            break

        page += 1
        time.sleep(settings.rate_limit_delay)  # Rate limiting

    return results


def WBAPI01(
    indicators: dict[str, tuple[str, str, str]] | None = None,
    date_range: str = "2018:2023",
) -> pd.DataFrame:
    """
    Fetch World Bank development indicators for all countries.

    Parameters
    ----------
    indicators : dict, optional
        Custom indicator map. Defaults to the module-level INDICATORS dict.
    date_range : str
        Date range in "YYYY:YYYY" format (default "2018:2023").

    Returns
    -------
    pd.DataFrame
        Schema-compliant DataFrame with indicator data.
    """
    if indicators is None:
        indicators = INDICATORS

    session = _create_session()

    all_records: list[dict] = []

    for ind_code, (ind_name, category, unit) in indicators.items():
        logger.info("[WBAPI01] Fetching indicator: %s (%s)", ind_code, ind_name)
        try:
            raw_points = _fetch_indicator(session, ind_code, date_range=date_range)
            for pt in raw_points:
                all_records.append({
                    "recordid": f"{pt['country_code']}_{ind_code}_{pt['year']}",
                    "title":    ind_name,
                    "category": category,
                    "value":    pt["value"],
                    "unit":     unit,
                    "country":  pt["country_code"],
                    "year":     pt["year"],
                    "url":      f"{API_BASE}/country/all/indicator/{ind_code}?format=json",
                })
            logger.info("[WBAPI01] %s → %d data points", ind_code, len(raw_points))
        except Exception as exc:
            logger.warning("[WBAPI01] Indicator '%s' failed: %s", ind_code, exc)
            continue

    if not all_records:
        return enforce_schema(pd.DataFrame(), "WBAPI01")

    raw = pd.DataFrame(all_records)
    logger.info("[WBAPI01] Total records fetched: %d", len(raw))
    return enforce_schema(raw, "WBAPI01")
