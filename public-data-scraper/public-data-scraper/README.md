# public-data-scraper

A production-grade Python scraping portfolio project demonstrating **4 real-world data collection techniques** against fully public data sources.

Built as a clean, original portfolio project for Upwork and GitHub — 100% open data, zero IP concerns.

---

## What this project demonstrates

| Technique | Library | Source | Data |
|---|---|---|---|
| **HTML scraping** | `requests` + `BeautifulSoup` | books.toscrape.com | ~1,000 books: title, price, rating, genre |
| **REST API / JSON** | `requests` | World Bank Open Data | GDP, population, HDI for ~200 countries |
| **PDF extraction** | `pdfplumber` | UN World Population Prospects | Country population estimates |
| **Browser automation** | `Selenium` (headless Chrome) | Wikipedia | GDP per capita, largest companies, HDI tables |

All sources are **publicly available**, **scraping-friendly**, and raise zero legal or IP concerns.

---

## Project Structure

```
public-data-scraper/
│
├── public_data_scraper/          # Main package
│   ├── __init__.py               # Public API exports
│   ├── __main__.py               # CLI entrypoint
│   ├── schema.py                 # Canonical schema + enforce_schema()
│   ├── registry.py               # Source registry + metadata
│   ├── runner.py                 # Orchestration, error isolation, CSV/JSON output
│   ├── logging_config.py         # Structured logging setup
│   └── scrapers/
│       ├── books_scraper.py      # BOOKS01 — requests + BeautifulSoup
│       ├── worldbank_scraper.py  # WBAPI01 — REST API / JSON
│       ├── un_pdf_scraper.py     # UNPDF01 — pdfplumber
│       └── wikipedia_scraper.py  # WIKI01/02/03 — Selenium
│
├── tests/
│   └── test_core.py              # 20+ unit tests (schema, registry, runner)
│
├── examples/
│   └── run_examples.py           # Runnable usage examples
│
├── output/                       # CSV + JSON output (git-ignored)
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Output Schema

Every scraper returns a `pandas.DataFrame` with exactly these 9 columns:

| Column | Description | Example |
|---|---|---|
| `SourceCode` | Unique source identifier | `BOOKS01` |
| `RecordID` | Unique record identifier | `GB_NY.GDP.MKTP.CD_2022` |
| `Title` | Main entity name | `A Light in the Attic` |
| `Category` | Data category / genre | `Mystery` |
| `Value` | Primary numeric value | `51.77` |
| `Unit` | Unit of Value | `GBP` |
| `Country` | Country code (ISO3 or name) | `GBR` |
| `Year` | Reference year | `2022` |
| `URL` | Source URL | `http://books.toscrape.com/...` |

Missing values are `pd.NA`. Every scraper calls `enforce_schema()` before returning — guaranteeing this schema regardless of the source format.

---

## Installation

```bash
git clone https://github.com/Murali11134/T-Mart.git
cd T-Mart
pip install -e ".[dev]"
```

Chrome must be installed for Selenium scrapers. `webdriver-manager` handles ChromeDriver automatically.

---

## Usage

### CLI

```bash
# List all available sources
python -m public_data_scraper --list

# Run specific scrapers
python -m public_data_scraper --codes BOOKS01 WBAPI01

# Run all non-browser scrapers (fast, no Chrome needed)
python -m public_data_scraper --all --skip-browser

# Run all API-based scrapers
python -m public_data_scraper --method api

# Run Wikipedia scrapers (Selenium)
python -m public_data_scraper --codes WIKI_ALL

# Save per-source files in addition to combined output
python -m public_data_scraper --codes BOOKS01 WBAPI01 --per-scraper --output data/

# Enable debug logging
python -m public_data_scraper --codes WBAPI01 --log-level DEBUG --log-file logs/run.log
```

### Python API

```python
from public_data_scraper import run_many, save_results, print_summary

# Run multiple scrapers — errors are isolated, never crash the pipeline
results = run_many(["BOOKS01", "WBAPI01", "UNPDF01"])

# Save combined CSV + JSON to ./output/
save_results(results, output_dir="output")

# Print a formatted summary table
print_summary(results)
```

```python
# Run a single scraper directly
from public_data_scraper import get_scraper

fn = get_scraper("BOOKS01")
df = fn()
print(df.head())
print(df.dtypes)
```

```python
# Filter sources by technique
from public_data_scraper import list_codes

# All sources that don't need a browser
safe = list_codes(requires_browser=False)   # ['BOOKS01', 'UNPDF01', 'WBAPI01']

# Only API-based sources
api_codes = list_codes(method="api")        # ['WBAPI01']
```

---

## Techniques in Detail

### 1. requests + BeautifulSoup — `BOOKS01`

Scrapes [books.toscrape.com](http://books.toscrape.com), a sandbox site built specifically for scraping practice.

- Paginates through all ~50 genre categories
- Extracts book title, price (£), star rating, and genre per page
- Uses polite crawl delays between page requests
- Handles relative → absolute URL resolution for pagination

```python
from public_data_scraper.scrapers.books_scraper import BOOKS01
df = BOOKS01(max_categories=3)   # Quick test: first 3 genres only
```

### 2. REST API / JSON — `WBAPI01`

Fetches from the [World Bank Open Data API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) — no authentication required.

Indicators collected: GDP (current US$), Total Population, Gini Index, Health Expenditure (% GDP), Adult Literacy Rate.

- Handles multi-page API pagination automatically
- Configurable indicator set and date range
- ~200 countries × 5 indicators = ~1,000 data points

```python
from public_data_scraper.scrapers.worldbank_scraper import WBAPI01
df = WBAPI01(date_range="2020:2023")
```

### 3. pdfplumber — `UNPDF01`

Extracts population data from [UN World Population Prospects](https://population.un.org/wpp/).

- Primary mode: downloads the official UN CSV (fast, recommended)
- PDF demo mode: demonstrates `pdfplumber` table extraction on any public PDF
- Country-level filtering (ISO3 codes), most recent year per country

```python
from public_data_scraper.scrapers.un_pdf_scraper import UNPDF01, UNPDF01_demo_pdf
df = UNPDF01()

# Demonstrate PDF extraction on any public tabular PDF
df_pdf = UNPDF01_demo_pdf("https://example.com/some_report.pdf")
```

### 4. Selenium — `WIKI01`, `WIKI02`, `WIKI03`, `WIKI_ALL`

Scrapes Wikipedia data tables using headless Chrome, demonstrating the standard pattern for JS-rendered content.

- WIKI01: Countries by GDP per capita
- WIKI02: Largest companies by revenue
- WIKI03: Countries by Human Development Index
- WIKI_ALL: All three in one browser session (more efficient)

```python
from public_data_scraper.scrapers.wikipedia_scraper import WIKI_ALL
df = WIKI_ALL()   # Single Chrome session, 3 tables
```

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
pytest --cov=public_data_scraper --cov-report=term-missing
```

Tests cover schema enforcement, registry integrity, runner error isolation, and CSV/JSON output. No network calls during testing.

---

## License

MIT — free to use, modify, and build on.
