"""
tests/test_core.py
------------------
Unit tests for schema, registry, and runner.
No network calls are made in this test suite.
"""

import pandas as pd
import pytest

from public_data_scraper.schema   import REQUIRED_COLUMNS, enforce_schema
from public_data_scraper.registry import REGISTRY, list_codes, get_scraper
from public_data_scraper.runner   import ScraperResult, run_one, save_results


# ── enforce_schema ────────────────────────────────────────────────────────────

def test_returns_required_columns():
    df = pd.DataFrame({"title": ["Test Item"]})
    result = enforce_schema(df, "TEST01")
    assert list(result.columns) == REQUIRED_COLUMNS


def test_stamps_source_code():
    df = pd.DataFrame({"title": ["Item"]})
    result = enforce_schema(df, "ZZ99")
    assert result["SourceCode"].iloc[0] == "ZZ99"


def test_strips_whitespace():
    df = pd.DataFrame({"title": ["  Padded Title  "]})
    result = enforce_schema(df, "TEST01")
    assert result["Title"].iloc[0] == "Padded Title"


def test_replaces_empty_string_with_na():
    df = pd.DataFrame({"title": ["Item"], "value": [""]})
    result = enforce_schema(df, "TEST01")
    assert pd.isna(result["Value"].iloc[0])


def test_replaces_nan_string_with_na():
    df = pd.DataFrame({"title": ["Item"], "unit": ["nan"]})
    result = enforce_schema(df, "TEST01")
    assert pd.isna(result["Unit"].iloc[0])


def test_drops_missing_title():
    df = pd.DataFrame({"title": ["Valid", None, ""]})
    result = enforce_schema(df, "TEST01")
    assert len(result) == 1
    assert result["Title"].iloc[0] == "Valid"


def test_adds_missing_columns():
    df = pd.DataFrame({"title": ["Only Title"]})
    result = enforce_schema(df, "TEST01")
    for col in REQUIRED_COLUMNS:
        assert col in result.columns


def test_case_insensitive_rename():
    df = pd.DataFrame({"title": ["item"], "sourcecode": ["OLD"], "country": ["GB"]})
    result = enforce_schema(df, "NEW01")
    assert "Title"   in result.columns
    assert "Country" in result.columns
    assert result["SourceCode"].iloc[0] == "NEW01"  # overwritten by enforce_schema


def test_none_input_returns_empty_schema():
    result = enforce_schema(None, "TEST01")
    assert list(result.columns) == REQUIRED_COLUMNS
    assert len(result) == 0


def test_empty_df_returns_empty_schema():
    result = enforce_schema(pd.DataFrame(), "TEST01")
    assert list(result.columns) == REQUIRED_COLUMNS
    assert len(result) == 0


# ── Registry ──────────────────────────────────────────────────────────────────

def test_registry_not_empty():
    assert len(REGISTRY) >= 7


def test_all_entries_have_required_fields():
    for code, entry in REGISTRY.items():
        assert entry.code == code
        assert entry.method in ("requests", "selenium", "pdf", "api")
        assert entry.module.startswith("public_data_scraper")


def test_list_codes_returns_all():
    codes = list_codes()
    assert len(codes) == len(REGISTRY)


def test_list_codes_filter_method():
    api_codes = list_codes(method="api")
    assert "WBAPI01" in api_codes
    assert all(REGISTRY[c].method == "api" for c in api_codes)


def test_list_codes_filter_browser():
    no_browser = list_codes(requires_browser=False)
    assert all(not REGISTRY[c].requires_browser for c in no_browser)


def test_get_scraper_returns_callable():
    fn = get_scraper("BOOKS01")
    assert callable(fn)


def test_get_scraper_unknown_raises():
    with pytest.raises(KeyError, match="Unknown source code"):
        get_scraper("NONEXISTENT")


# ── Runner ────────────────────────────────────────────────────────────────────

def test_run_one_bad_code_does_not_raise():
    result = run_one("NONEXISTENT_CODE")
    assert result.success is False
    assert result.error is not None


def test_scraper_result_record_count_zero_on_fail():
    r = ScraperResult("XX01")
    assert r.record_count == 0
    assert r.success is False


def test_save_results_creates_csv(tmp_path):
    r = ScraperResult("TEST01")
    r.df = pd.DataFrame([{c: "x" if c != "Title" else "My Item" for c in REQUIRED_COLUMNS}])

    written = save_results([r], output_dir=tmp_path, save_csv=True, save_json=False)
    assert "csv" in written
    assert written["csv"].exists()

    loaded = pd.read_csv(written["csv"])
    assert list(loaded.columns) == REQUIRED_COLUMNS


def test_save_results_creates_json(tmp_path):
    r = ScraperResult("TEST01")
    r.df = pd.DataFrame([{c: "x" if c != "Title" else "My Item" for c in REQUIRED_COLUMNS}])

    written = save_results([r], output_dir=tmp_path, save_csv=False, save_json=True)
    assert "json" in written
    assert written["json"].exists()

    import json
    data = json.loads(written["json"].read_text())
    assert isinstance(data, list)
    assert data[0]["Title"] == "My Item"


def test_save_results_empty_returns_nothing(tmp_path):
    r = ScraperResult("FAIL01")
    r.error = ValueError("test error")
    written = save_results([r], output_dir=tmp_path)
    assert written == {}
