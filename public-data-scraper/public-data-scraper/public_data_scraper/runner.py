"""
runner.py
---------
Orchestrates scraper execution with error isolation, structured logging,
optional parallelism, and dual CSV + JSON output.
"""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from public_data_scraper.registry import REGISTRY, get_scraper

logger = logging.getLogger(__name__)


class ScraperResult:
    """Holds the outcome of a single scraper run."""

    def __init__(self, code: str):
        self.code       = code
        self.df: Optional[pd.DataFrame] = None
        self.error: Optional[Exception] = None
        self.duration_s: float          = 0.0

    @property
    def success(self) -> bool:
        return self.error is None and self.df is not None and not self.df.empty

    @property
    def record_count(self) -> int:
        return len(self.df) if self.df is not None else 0

    def __repr__(self) -> str:
        if self.success:
            return f"<ScraperResult {self.code} OK rows={self.record_count} t={self.duration_s:.1f}s>"
        return f"<ScraperResult {self.code} FAILED error={self.error}>"


def run_one(code: str) -> ScraperResult:
    """
    Run a single scraper. Captures all exceptions into ScraperResult —
    one failure never stops the pipeline.
    """
    result = ScraperResult(code)
    entry  = REGISTRY.get(code)
    desc   = entry.description if entry else "unknown"
    logger.info("▶  [%s] Starting — %s", code, desc)

    t0 = time.monotonic()
    try:
        fn       = get_scraper(code)
        result.df = fn()
        result.duration_s = time.monotonic() - t0
        logger.info(
            "✔  [%s] Done in %.1fs — %d record(s).",
            code, result.duration_s, result.record_count,
        )
    except Exception as exc:
        result.duration_s = time.monotonic() - t0
        result.error = exc
        logger.error(
            "✘  [%s] Failed after %.1fs — %s: %s",
            code, result.duration_s, type(exc).__name__, exc,
            exc_info=True,
        )

    return result


def run_many(
    codes: list[str],
    *,
    max_workers: int = 1,
    skip_browser: bool = False,
) -> list[ScraperResult]:
    """
    Run multiple scrapers, optionally in parallel.

    Parameters
    ----------
    codes : list[str]
        Source codes to run.
    max_workers : int
        Thread workers (default 1 = sequential). Browser scrapers should
        not be run in parallel unless you have enough RAM for N Chrome instances.
    skip_browser : bool
        Skip scrapers that require a browser (safe for headless/CI environments).
    """
    if skip_browser:
        skipped = [c for c in codes if REGISTRY.get(c) and REGISTRY[c].requires_browser]
        if skipped:
            logger.warning("Skipping browser-required scrapers: %s", skipped)
        codes = [c for c in codes if not (REGISTRY.get(c) and REGISTRY[c].requires_browser)]

    if max_workers == 1:
        return [run_one(c) for c in codes]

    results_map: dict[str, ScraperResult] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_one, c): c for c in codes}
        for future in as_completed(futures):
            code = futures[future]
            results_map[code] = future.result()

    return [results_map[c] for c in codes]


def save_results(
    results: list[ScraperResult],
    output_dir: str | Path = "output",
    *,
    combined_stem: str  = "all_sources",
    per_scraper: bool   = False,
    save_json: bool     = True,
    save_csv: bool      = True,
) -> dict[str, Path]:
    """
    Save scraper results to CSV and/or JSON.

    Parameters
    ----------
    results      : list of ScraperResult
    output_dir   : directory to write into (created if absent)
    combined_stem: filename stem for combined outputs (no extension)
    per_scraper  : also write individual files per successful scraper
    save_json    : write combined JSON (records orientation)
    save_csv     : write combined CSV

    Returns
    -------
    dict[str, Path]
        Keys: "csv", "json" (whichever were written).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    successful = [r for r in results if r.success]
    failed     = [r for r in results if not r.success]

    written: dict[str, Path] = {}

    if not successful:
        logger.warning("No successful results to save.")
        return written

    combined_df = pd.concat([r.df for r in successful], ignore_index=True)

    # ── Per-scraper files ────────────────────────────────────────────────
    if per_scraper:
        for r in successful:
            if save_csv:
                p = out / f"{r.code}.csv"
                r.df.to_csv(p, index=False, encoding="utf-8-sig")
                logger.debug("Saved %s → %s", r.code, p)
            if save_json:
                p = out / f"{r.code}.json"
                r.df.to_json(p, orient="records", indent=2, force_ascii=False)

    # ── Combined CSV ─────────────────────────────────────────────────────
    if save_csv:
        csv_path = out / f"{combined_stem}.csv"
        combined_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info(
            "CSV saved → %s (%d records, %d source(s))",
            csv_path, len(combined_df), len(successful),
        )
        written["csv"] = csv_path

    # ── Combined JSON ────────────────────────────────────────────────────
    if save_json:
        json_path = out / f"{combined_stem}.json"
        combined_df.to_json(json_path, orient="records", indent=2, force_ascii=False)
        logger.info("JSON saved → %s", json_path)
        written["json"] = json_path

    if failed:
        logger.warning(
            "%d scraper(s) failed: %s",
            len(failed), [r.code for r in failed],
        )

    return written


def print_summary(results: list[ScraperResult]) -> None:
    """Print a run summary table to stdout."""
    ok    = [r for r in results if r.success]
    err   = [r for r in results if not r.success]
    total = sum(r.record_count for r in ok)

    print("\n" + "=" * 62)
    print(f"  Run Summary — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 62)
    print(f"  {'Scrapers run':<20}: {len(results)}")
    print(f"  {'✔  Succeeded':<20}: {len(ok)}  ({total:,} records)")
    print(f"  {'✘  Failed':<20}: {len(err)}")
    if err:
        for r in err:
            print(f"       {r.code:10s}  {type(r.error).__name__}: {r.error}")
    if ok:
        print()
        print(f"  {'Code':<12} {'Records':>8}  {'Time':>8}  Method")
        print(f"  {'-'*44}")
        for r in ok:
            entry  = REGISTRY.get(r.code)
            method = entry.method if entry else "?"
            print(f"  {r.code:<12} {r.record_count:>8,}  {r.duration_s:>7.1f}s  {method}")
    print("=" * 62 + "\n")
