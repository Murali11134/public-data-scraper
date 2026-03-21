"""
examples/run_examples.py
------------------------
Runnable examples. Each function makes live network requests.
"""

def example_books():
    """requests + BeautifulSoup — scrape 3 genres from books.toscrape.com"""
    from public_data_scraper.scrapers.books_scraper import BOOKS01
    df = BOOKS01(max_categories=3)
    print(f"Books scraped: {len(df)}")
    print(df[["Title", "Category", "Value", "Unit"]].head(10))

def example_worldbank():
    """REST API — fetch World Bank indicators"""
    from public_data_scraper.scrapers.worldbank_scraper import WBAPI01
    df = WBAPI01(date_range="2022:2023")
    print(f"Indicators fetched: {len(df)}")
    print(df[["Country", "Title", "Value", "Unit", "Year"]].head(10))

def example_un():
    """pdfplumber — UN population data"""
    from public_data_scraper.scrapers.un_pdf_scraper import UNPDF01
    df = UNPDF01()
    print(f"Countries: {len(df)}")
    print(df[["Title", "Value", "Unit", "Year"]].head(10))

def example_wikipedia():
    """Selenium — Wikipedia tables (requires Chrome)"""
    from public_data_scraper.scrapers.wikipedia_scraper import WIKI_ALL
    df = WIKI_ALL()
    print(f"Wikipedia rows: {len(df)}")
    print(df[["Title", "Category", "Value", "Unit"]].head(10))

def example_full_pipeline():
    """Run all non-browser scrapers and save CSV + JSON"""
    from public_data_scraper import run_many, save_results, print_summary
    results = run_many(["BOOKS01", "WBAPI01", "UNPDF01"])
    save_results(results, output_dir="output", per_scraper=True)
    print_summary(results)

if __name__ == "__main__":
    print("=== Books (requests + BeautifulSoup) ===")
    example_books()
    print("\n=== World Bank (API) ===")
    example_worldbank()
    print("\n=== UN Population (pdfplumber) ===")
    example_un()
    # Uncomment to run Selenium example (requires Chrome):
    # print("\n=== Wikipedia (Selenium) ===")
    # example_wikipedia()
