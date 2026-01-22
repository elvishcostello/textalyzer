"""Shared configuration for textalyzer."""

import logging
import re
from pathlib import Path

# Logging configuration
LOG_LEVEL = logging.WARNING
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)


# Path configuration
DEFAULT_BOOK_IDS_PATH = Path("books.csv")
DEFAULT_STORE_PATH = Path("text-store")
DEFAULT_DB_PATH = Path("db/text-search.db")

# Project Gutenberg URL templates
TEXT_URL_TEMPLATE = "https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
EBOOK_URL_TEMPLATE = "https://www.gutenberg.org/ebooks/{book_id}"

# Gutendex API for searching Project Gutenberg catalog
# Uses local Docker instance by default. See docker/gutendex/README.md for setup.
# For the public API, use: https://gutendex.com/books/
GUTENDEX_API_URL = "http://localhost:8000/books/"

# Regex patterns for extracting book content
# Flexible pattern to handle historical variations in Gutenberg markers
START_MARKER_RE = re.compile(
    r"\*+\s*"  # one or more asterisks
    r"START\s+(?:OF\s+)?"  # START OF (OF optional)
    r"(?:THIS\s+|THE\s+)?"  # optional THIS or THE
    r"PROJECT\s+GUTENBERG"  # PROJECT GUTENBERG
    r".*?"  # anything in between
    r"\*+",  # ending asterisks
    re.IGNORECASE,
)
END_MARKER_RE = re.compile(
    r"\*+\s*"  # one or more asterisks
    r"END\s+(?:OF\s+)?"  # END OF (OF optional)
    r"(?:THIS\s+|THE\s+)?"  # optional THIS or THE
    r"PROJECT\s+GUTENBERG"  # PROJECT GUTENBERG
    r".*?"  # anything in between
    r"\*+",  # ending asterisks
    re.IGNORECASE,
)

# Indexing configuration
MIN_PARAGRAPH_LENGTH = 4

# Patterns to skip when indexing paragraphs
SKIP_PARAGRAPH_PATTERNS = [
    "[Illustration",  # image markers: [Illustration] or [Illustration: caption]
    "[Blank Page]",  # blank page indicators
    "[**",  # proofreader/transcriber comments
    "[Transcriber's Note",  # transcriber explanations
    "[Editor's Note",  # editorial notes
    "[Technical Note",  # technical annotations
    "[_Copyright",  # copyright notices
]
