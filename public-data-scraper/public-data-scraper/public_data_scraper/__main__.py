"""
CLI entrypoint — python -m public_data_scraper

Examples
--------
    python -m public_data_scraper --list
    python -m public_data_scraper --codes BOOKS01 WBAPI01
    python -m public_data_scraper --all --skip-browser
    python -m public_data_scraper --method api --output data/
    python -m public_data_scraper --codes WIKI_ALL --per-scraper
"""

from __future__ import annotations

import argparse
import sys

from public_data_scraper.config import settings


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="public_data_scraper",
        description="Scrape public datasets using 4 different techniques.",
    )

    sel = p.add_mutually_exclusive_group()
    sel.add_argument("--codes",  nargs="+", metavar="CODE",
                     help="One or more source codes (e.g. BOOKS01 WBAPI01)")
    sel.add_argument("--all",    action="store_true", help="Run all sources")
    sel.add_argument("--method", choices=["requests","selenium","pdf","api"],
                     help="Run all sources using a given method")
    sel.add_argument("--list",   action="store_true", dest="list_codes",
                     help="Print all available source codes and exit")

    p.add_argument("--workers",      type=int, default=1, metavar="N")
    p.add_argument("--skip-browser", action="store_true")
    p.add_argument("--output",       default=settings.output_dir, metavar="DIR")
    p.add_argument("--per-scraper",  action="store_true")
    p.add_argument("--no-json",      action="store_true", help="Skip JSON output")
    p.add_argument("--no-csv",       action="store_true", help="Skip CSV output")
    p.add_argument("--log-level",    default=settings.log_level,
                   choices=["DEBUG","INFO","WARNING","ERROR"])
    p.add_argument("--log-file",     default=settings.log_file, metavar="PATH")
    return p


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    setup_logging(level=args.log_level, log_file=args.log_file)

    if args.list_codes:
        print(f"\n{'Code':<12} {'Domain':<14} {'Method':<10} {'Browser':<8} Description")
        print("-" * 78)
        for code, e in sorted(REGISTRY.items()):
            browser = "✓" if e.requires_browser else ""
            print(f"{code:<12} {e.domain:<14} {e.method:<10} {browser:<8} {e.description}")
        print(f"\nTotal: {len(REGISTRY)} sources\n")
        return 0

    if args.codes:
        codes = args.codes
    elif getattr(args, "all", False):
        codes = list_codes()
    elif args.method:
        codes = list_codes(method=args.method)
    else:
        _parser().print_help()
        return 1

    unknown = [c for c in codes if c not in REGISTRY]
    if unknown:
        print(f"Unknown code(s): {unknown}. Run --list to see valid codes.")
        return 1

    results = run_many(codes, max_workers=args.workers, skip_browser=args.skip_browser)

    save_results(
        results,
        output_dir    = args.output,
        per_scraper   = args.per_scraper,
        save_csv      = not args.no_csv,
        save_json     = not args.no_json,
    )

    print_summary(results)
    return 1 if any(not r.success for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
