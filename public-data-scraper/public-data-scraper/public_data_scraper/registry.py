"""
registry.py
-----------
Central registry mapping every source code to its scraper function
and metadata. Add new scrapers here as you build them.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd


@dataclass(frozen=True)
class ScraperEntry:
    code: str
    description: str
    domain: str          # e.g. "E-commerce", "Economics", "Demographics"
    method: str          # "requests" | "selenium" | "pdf" | "api"
    module: str          # dotted import path
    requires_browser: bool = False
    notes: str = ""


REGISTRY: dict[str, ScraperEntry] = {
    "BOOKS01": ScraperEntry(
        code             = "BOOKS01",
        description      = "Books to Scrape – book catalogue (price, rating, genre)",
        domain           = "E-commerce",
        method           = "requests",
        module           = "public_data_scraper.scrapers.books_scraper",
        requires_browser = False,
        notes            = "Sandbox site built for scraping practice. ~1,000 books across 50 genres.",
    ),
    "WBAPI01": ScraperEntry(
        code             = "WBAPI01",
        description      = "World Bank Open Data – development indicators (GDP, population, etc.)",
        domain           = "Economics",
        method           = "api",
        module           = "public_data_scraper.scrapers.worldbank_scraper",
        requires_browser = False,
        notes            = "Free JSON API. No auth required. ~200 countries × 5 indicators.",
    ),
    "UNPDF01": ScraperEntry(
        code             = "UNPDF01",
        description      = "UN World Population Prospects – country population estimates",
        domain           = "Demographics",
        method           = "pdf",
        module           = "public_data_scraper.scrapers.un_pdf_scraper",
        requires_browser = False,
        notes            = "Primary: official UN CSV. Demo PDF mode available via UNPDF01_demo_pdf().",
    ),
    "WIKI01": ScraperEntry(
        code             = "WIKI01",
        description      = "Wikipedia – countries by GDP per capita (nominal)",
        domain           = "Economics",
        method           = "selenium",
        module           = "public_data_scraper.scrapers.wikipedia_scraper",
        requires_browser = True,
    ),
    "WIKI02": ScraperEntry(
        code             = "WIKI02",
        description      = "Wikipedia – largest companies by revenue",
        domain           = "Business",
        method           = "selenium",
        module           = "public_data_scraper.scrapers.wikipedia_scraper",
        requires_browser = True,
    ),
    "WIKI03": ScraperEntry(
        code             = "WIKI03",
        description      = "Wikipedia – countries by Human Development Index",
        domain           = "Demographics",
        method           = "selenium",
        module           = "public_data_scraper.scrapers.wikipedia_scraper",
        requires_browser = True,
    ),
    "WIKI_ALL": ScraperEntry(
        code             = "WIKI_ALL",
        description      = "Wikipedia – all three tables in one browser session",
        domain           = "Mixed",
        method           = "selenium",
        module           = "public_data_scraper.scrapers.wikipedia_scraper",
        requires_browser = True,
        notes            = "More efficient than running WIKI01/02/03 separately.",
    ),
}


def get_scraper(code: str) -> Callable[[], pd.DataFrame]:
    """
    Return the callable scraper function for a given source code.

    Raises KeyError if the code is not registered.
    """
    if code not in REGISTRY:
        raise KeyError(
            f"Unknown source code '{code}'. "
            f"Available: {sorted(REGISTRY)}"
        )
    entry  = REGISTRY[code]
    module = importlib.import_module(entry.module)
    return getattr(module, code)


def list_codes(
    method: Optional[str] = None,
    domain: Optional[str] = None,
    requires_browser: Optional[bool] = None,
) -> list[str]:
    """Return a filtered list of registered source codes."""
    results = []
    for code, entry in REGISTRY.items():
        if method           and entry.method           != method:           continue
        if domain           and entry.domain.lower()   != domain.lower():   continue
        if requires_browser is not None and entry.requires_browser != requires_browser: continue
        results.append(code)
    return sorted(results)
