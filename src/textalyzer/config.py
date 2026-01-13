"""Shared configuration for textalyzer."""

import logging
import re
from pathlib import Path

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)


# Path configuration
DEFAULT_BOOK_IDS_PATH = Path("book-ids.dat")
DEFAULT_STORE_PATH = Path("text-store")
DEFAULT_DB_PATH = Path("db/text-search.db")

# Project Gutenberg URL templates
TEXT_URL_TEMPLATE = "https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
EBOOK_URL_TEMPLATE = "https://www.gutenberg.org/ebooks/{book_id}"

# Regex patterns for extracting book content
START_MARKER_RE = re.compile(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK .+? \*\*\*")
END_MARKER_RE = re.compile(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK .+? \*\*\*")

# Indexing configuration
MIN_PARAGRAPH_LENGTH = 4
SKIP_PARAGRAPH_PATTERNS = ["[_Copyright", "[Illustration]"]
