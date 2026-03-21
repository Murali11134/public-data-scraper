"""
public_data_scraper
===================
A portfolio scraping project demonstrating 4 real-world data collection
techniques against fully public data sources.

Techniques covered
------------------
- requests + BeautifulSoup  (Books to Scrape — HTML)
- REST API / JSON           (World Bank Open Data)
- pdfplumber                (UN Population Reports)
- Selenium                  (Wikipedia JS-rendered tables)

Quick start
-----------
    from public_data_scraper import run_many, save_results

    results = run_many(["BOOKS01", "WBAPI01"], skip_browser=True)
    save_results(results, output_dir="output")

CLI
---
    python -m public_data_scraper --codes BOOKS01 WBAPI01 --output output/
    python -m public_data_scraper --list
"""

from public_data_scraper.runner   import run_one, run_many, save_results, print_summary
from public_data_scraper.registry import REGISTRY, get_scraper, list_codes
from public_data_scraper.schema   import enforce_schema, REQUIRED_COLUMNS

__version__ = "1.0.0"

__all__ = [
    "run_one", "run_many", "save_results", "print_summary",
    "REGISTRY", "get_scraper", "list_codes",
    "enforce_schema", "REQUIRED_COLUMNS",
]
