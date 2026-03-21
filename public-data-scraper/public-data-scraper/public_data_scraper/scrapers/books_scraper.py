"""
books_scraper.py
----------------
Scrapes books.toscrape.com — a sandbox site built specifically for
web-scraping practice.

Source  : http://books.toscrape.com
Method  : requests + BeautifulSoup (static HTML, paginated)
Output  : Title, Category, Price (Value), Rating (Unit), URL

Schema columns populated
------------------------
SourceCode : "BOOKS01"
RecordID   : sequential index
Title      : book title
Category   : genre (e.g. Mystery, Science Fiction)
Value      : price in GBP (numeric string, e.g. "12.99")
Unit       : star rating (e.g. "Three")
Country    : n/a (global catalogue)
Year       : n/a
URL        : direct product page URL
"""

from __future__ import annotations

import logging
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from public_data_scraper.schema import enforce_schema

logger = logging.getLogger(__name__)

BASE_URL   = "http://books.toscrape.com"
CATALOGUE  = f"{BASE_URL}/catalogue"


def _get_categories(session: requests.Session) -> dict[str, str]:
    """Return {category_name: category_url} from the sidebar."""
    resp = session.get(BASE_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    categories: dict[str, str] = {}
    for li in soup.select("ul.nav-list ul li"):
        a = li.find("a")
        if not a:
            continue
        name = a.get_text(strip=True)
        href = a["href"].replace("../", "")
        categories[name] = f"{BASE_URL}/{href}"

    logger.info("[BOOKS01] Found %d categories.", len(categories))
    return categories


def _scrape_category(
    session: requests.Session,
    category: str,
    start_url: str,
) -> list[dict]:
    """Paginate through a category page and return raw book records."""
    records: list[dict] = []
    url = start_url

    while url:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for article in soup.select("article.product_pod"):
            # Title
            h3_a = article.select_one("h3 a")
            title  = h3_a["title"] if h3_a else pd.NA
            detail = h3_a["href"].replace("../", "") if h3_a else ""

            # Price (strip £ symbol)
            price_tag = article.select_one("p.price_color")
            price = price_tag.get_text(strip=True).lstrip("£Â") if price_tag else pd.NA

            # Star rating (word form, e.g. "Three")
            rating_tag = article.select_one("p.star-rating")
            rating = rating_tag["class"][1] if rating_tag and len(rating_tag["class"]) > 1 else pd.NA

            # Product detail URL
            product_url = f"{CATALOGUE}/{detail}" if detail else pd.NA

            records.append({
                "title":    title,
                "category": category,
                "value":    price,
                "unit":     rating,
                "url":      product_url,
            })

        # Pagination
        next_btn = soup.select_one("li.next a")
        if next_btn:
            next_href = next_btn["href"]
            # Construct absolute URL for the next page
            if "catalogue/" in url:
                url = "/".join(url.split("/")[:-1]) + "/" + next_href
            else:
                url = f"{CATALOGUE}/{next_href}"
            time.sleep(0.5)          # polite crawl delay
        else:
            url = None

    return records


def BOOKS01(max_categories: int | None = None) -> pd.DataFrame:
    """
    Scrape books from books.toscrape.com.

    Parameters
    ----------
    max_categories : int, optional
        Limit the number of categories scraped (useful for quick tests).
        Default is None (scrape all ~50 categories).

    Returns
    -------
    pd.DataFrame
        Schema-compliant DataFrame with book data.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "public-data-scraper/1.0 (portfolio project; educational use)"
    })

    categories = _get_categories(session)
    if max_categories:
        categories = dict(list(categories.items())[:max_categories])

    all_records: list[dict] = []

    for cat_name, cat_url in categories.items():
        logger.info("[BOOKS01] Scraping category: %s", cat_name)
        try:
            records = _scrape_category(session, cat_name, cat_url)
            all_records.extend(records)
            logger.debug("[BOOKS01] %s → %d books", cat_name, len(records))
        except Exception as exc:
            logger.warning("[BOOKS01] Category '%s' failed: %s", cat_name, exc)
            continue

    if not all_records:
        return enforce_schema(pd.DataFrame(), "BOOKS01")

    raw = pd.DataFrame(all_records)
    raw["recordid"] = range(1, len(raw) + 1)
    raw["country"]  = pd.NA
    raw["year"]     = pd.NA

    logger.info("[BOOKS01] Total books scraped: %d", len(raw))
    return enforce_schema(raw, "BOOKS01")
