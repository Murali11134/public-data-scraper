"""
config.py
---------
Configuration management for the scraper.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""

    # Scraping settings
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    rate_limit_delay: float = Field(default=0.5, description="Delay between requests in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries for failed requests")

    # Output settings
    output_dir: str = Field(default="output", description="Default output directory")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str | None = Field(default=None, description="Log file path")

    # Browser settings
    headless: bool = Field(default=True, description="Run browser in headless mode")
    chrome_driver_path: str | None = Field(default=None, description="Path to ChromeDriver")

    class Config:
        env_prefix = "SCRAPER_"
        case_sensitive = False


# Global settings instance
settings = Settings()