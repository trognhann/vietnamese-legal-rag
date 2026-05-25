"""
Ingestion module - Thu thập và xử lý văn bản pháp luật Việt Nam.
"""

from .scraper import (
    VietnamLegalScraper,
    LegalSource,
    LEGAL_SOURCES,
    normalize_filename,
    classify_document,
    SessionStats,
)

__all__ = [
    "VietnamLegalScraper",
    "LegalSource",
    "LEGAL_SOURCES",
    "normalize_filename",
    "classify_document",
    "SessionStats",
]
