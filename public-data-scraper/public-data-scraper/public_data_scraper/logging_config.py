"""
logging_config.py — centralised logging setup.
"""
from __future__ import annotations
import logging, sys
from pathlib import Path
from typing import Optional

from public_data_scraper.config import settings

_FMT  = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
_DATE = "%Y-%m-%d %H:%M:%S"

def setup_logging(level: Optional[str] = None, log_file: Optional[str | Path] = None) -> None:
    if level is None:
        level = settings.log_level
    if log_file is None:
        log_file = settings.log_file
    handlers: list[logging.Handler] = [_console(level)]
    if log_file:
        handlers.append(_file(log_file, level))
    logging.basicConfig(level=level.upper(), handlers=handlers, force=True)
    for noisy in ("selenium", "urllib3", "requests", "charset_normalizer", "WDM"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

def _console(level: str) -> logging.StreamHandler:
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(level.upper())
    h.setFormatter(logging.Formatter(_FMT, datefmt=_DATE))
    return h

def _file(path: str | Path, level: str) -> logging.Handler:
    from logging.handlers import RotatingFileHandler
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    h = RotatingFileHandler(path, maxBytes=10*1024*1024, backupCount=3, encoding="utf-8")
    h.setLevel(level.upper())
    h.setFormatter(logging.Formatter(_FMT, datefmt=_DATE))
    return h
