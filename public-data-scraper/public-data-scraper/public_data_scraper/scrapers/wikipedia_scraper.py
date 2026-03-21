"""
wikipedia_scraper.py
--------------------
Scrapes large data tables from Wikipedia using Selenium, demonstrating
browser automation on JS-enhanced pages.

Source  : https://en.wikipedia.org
Method  : Selenium (Chrome) + BeautifulSoup
Pages   : Three tables with real-world data of different shapes

Tables scraped
--------------
WIKI01 – List of countries by GDP (nominal) per capita
WIKI02 – List of largest companies by revenue
WIKI03 – List of countries by Human Development Index (HDI)

Why Selenium here?
------------------
Wikipedia uses JS-rendered sortable table headers and lazy-loaded
content on some list pages. Selenium ensures the full DOM is available
before parsing, which is the real-world pattern you'll encounter on
modern data-rich sites (government portals, stock screeners, etc.).

Schema columns populated
------------------------
SourceCode : "WIKI01" / "WIKI02" / "WIKI03"
RecordID   : sequential row index
Title      : entity name (country or company)
Category   : table category (e.g. "GDP per capita", "Revenue")
Value      : numeric value (GDP, revenue, HDI score)
Unit       : unit of Value (e.g. "USD", "USD billions", "index 0-1")
Country    : country name or HQ country
Year       : reference year from table notes
URL        : Wikipedia page URL
"""

from __future__ import annotations

import logging
import time

import pandas as pd
from bs4 import BeautifulSoup

from public_data_scraper.schema import enforce_schema

logger = logging.getLogger(__name__)

PAGES: dict[str, dict] = {
    "WIKI01": {
        "url":      "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)_per_capita",
        "category": "GDP per capita",
        "unit":     "USD",
        "year":     "2023",
    },
    "WIKI02": {
        "url":      "https://en.wikipedia.org/wiki/List_of_largest_companies_by_revenue",
        "category": "Revenue",
        "unit":     "USD billions",
        "year":     "2023",
    },
    "WIKI03": {
        "url":      "https://en.wikipedia.org/wiki/List_of_countries_by_Human_Development_Index",
        "category": "Human Development Index",
        "unit":     "index 0-1",
        "year":     "2022",
    },
}


def _make_driver():
    """
    Initialise a headless Chrome WebDriver.
    webdriver-manager handles ChromeDriver binary automatically.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=public-data-scraper/1.0 (portfolio project; educational use)"
    )

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def _parse_table(html: str, source_code: str, meta: dict) -> list[dict]:
    """
    Parse the first sortable wikitable found in the given HTML fragment.
    Returns a list of raw record dicts.
    """
    soup = BeautifulSoup(html, "lxml")

    # Wikipedia sortable tables have class "wikitable sortable"
    table = soup.find("table", class_=lambda c: c and "wikitable" in c)
    if not table:
        logger.warning("[%s] No wikitable found on page.", source_code)
        return []

    # Extract headers
    headers = [
        th.get_text(separator=" ", strip=True)
        for th in table.select("tr:first-of-type th")
    ]
    if not headers:
        headers = [str(i) for i in range(20)]

    records: list[dict] = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all(["td", "th"])]
        if not cells or all(c == "" for c in cells):
            continue

        # Heuristic column mapping — works for most Wikipedia data tables
        title   = cells[0] if len(cells) > 0 else pd.NA
        value   = cells[1] if len(cells) > 1 else pd.NA
        country = cells[0] if source_code in ("WIKI01", "WIKI03") else (
            cells[2] if len(cells) > 2 else pd.NA
        )

        # Clean numeric values (remove commas, reference marks like [2], ♠)
        import re
        value = re.sub(r"[\[♠†‡§¶,].*", "", str(value)).strip() if pd.notna(value) else value

        records.append({
            "title":    title,
            "category": meta["category"],
            "value":    value,
            "unit":     meta["unit"],
            "country":  country,
            "year":     meta["year"],
            "url":      meta["url"],
        })

    return records


def _scrape_page(
    driver,
    source_code: str,
    meta: dict,
) -> list[dict]:
    """Open a Wikipedia page in Selenium and extract the main data table."""
    logger.info("[%s] Loading %s", source_code, meta["url"])
    driver.get(meta["url"])
    time.sleep(3)   # allow JS to settle

    # Extract only the content div to reduce HTML size
    try:
        from selenium.webdriver.common.by import By
        content = driver.find_element(By.ID, "mw-content-text")
        html = content.get_attribute("innerHTML")
    except Exception:
        html = driver.page_source

    records = _parse_table(html, source_code, meta)
    logger.info("[%s] Extracted %d rows.", source_code, len(records))
    return records


def WIKI01() -> pd.DataFrame:
    """
    Scrape Wikipedia: countries by GDP per capita (nominal).
    Uses Selenium in headless mode.
    """
    return _run_single("WIKI01")


def WIKI02() -> pd.DataFrame:
    """
    Scrape Wikipedia: largest companies by revenue.
    Uses Selenium in headless mode.
    """
    return _run_single("WIKI02")


def WIKI03() -> pd.DataFrame:
    """
    Scrape Wikipedia: countries by Human Development Index.
    Uses Selenium in headless mode.
    """
    return _run_single("WIKI03")


def WIKI_ALL() -> pd.DataFrame:
    """
    Scrape all three Wikipedia tables in a single browser session
    (more efficient — one Chrome instance).

    Returns
    -------
    pd.DataFrame
        Combined schema-compliant DataFrame from all three pages.
    """
    driver = _make_driver()
    all_records: list[dict] = []

    try:
        for source_code, meta in PAGES.items():
            try:
                records = _scrape_page(driver, source_code, meta)
                for i, r in enumerate(records, 1):
                    r["recordid"] = f"{source_code}_{i:04d}"
                all_records.extend(records)
            except Exception as exc:
                logger.warning("[%s] Failed: %s", source_code, exc, exc_info=True)
    finally:
        driver.quit()

    if not all_records:
        return enforce_schema(pd.DataFrame(), "WIKI_ALL")

    raw = pd.DataFrame(all_records)
    return enforce_schema(raw, "WIKI_ALL")


def _run_single(source_code: str) -> pd.DataFrame:
    """Internal helper: scrape one Wikipedia page."""
    meta = PAGES[source_code]
    driver = _make_driver()

    try:
        records = _scrape_page(driver, source_code, meta)
    except Exception as exc:
        logger.error("[%s] Scrape failed: %s", source_code, exc, exc_info=True)
        return enforce_schema(pd.DataFrame(), source_code)
    finally:
        driver.quit()

    if not records:
        return enforce_schema(pd.DataFrame(), source_code)

    for i, r in enumerate(records, 1):
        r["recordid"] = f"{source_code}_{i:04d}"

    raw = pd.DataFrame(records)
    return enforce_schema(raw, source_code)
