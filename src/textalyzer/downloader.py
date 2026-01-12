"""Download books and metadata from Project Gutenberg."""

import json
import logging
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

TEXT_URL_TEMPLATE = "https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
EBOOK_URL_TEMPLATE = "https://www.gutenberg.org/ebooks/{book_id}"

DEFAULT_BOOK_IDS_PATH = Path("book-ids.dat")
DEFAULT_STORE_PATH = Path("text-store")


def load_book_ids(path: Path) -> list[str]:
    """Load book IDs from a file, one ID per line."""
    if not path.exists():
        logger.error(f"Book IDs file not found: {path}")
        return []

    ids = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                ids.append(line)
    return ids


def download_text(book_id: str, store_path: Path) -> bool:
    """Download book text file. Returns True if downloaded, False if skipped/error."""
    filename = f"pg{book_id}.txt"
    filepath = store_path / filename

    if filepath.exists():
        logger.info(f"[{book_id}] Text already exists, skipping: {filename}")
        return False

    url = TEXT_URL_TEMPLATE.format(book_id=book_id)
    logger.info(f"[{book_id}] Downloading text from {url}")

    try:
        response = httpx.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        filepath.write_bytes(response.content)
        logger.info(f"[{book_id}] Saved text to {filepath}")
        return True
    except httpx.HTTPError as e:
        logger.error(f"[{book_id}] Failed to download text: {e}")
        return False


def extract_meta_tags(html: str) -> list[dict[str, str]]:
    """Extract all meta tags from HTML and return as list of dicts."""
    soup = BeautifulSoup(html, "html.parser")
    meta_tags = soup.find_all("meta")

    result = []
    for tag in meta_tags:
        attrs = dict(tag.attrs)
        if attrs:
            result.append(attrs)
    return result


def download_metadata(book_id: str, store_path: Path) -> bool:
    """Download ebook page and extract metadata. Returns True if downloaded."""
    filename = f"{book_id}-meta.json"
    filepath = store_path / filename

    if filepath.exists():
        logger.info(f"[{book_id}] Metadata already exists, skipping: {filename}")
        return False

    url = EBOOK_URL_TEMPLATE.format(book_id=book_id)
    logger.info(f"[{book_id}] Downloading metadata from {url}")

    try:
        response = httpx.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        meta_tags = extract_meta_tags(response.text)
        filepath.write_text(json.dumps(meta_tags, indent=2))
        logger.info(f"[{book_id}] Saved metadata to {filepath}")
        return True
    except httpx.HTTPError as e:
        logger.error(f"[{book_id}] Failed to download metadata: {e}")
        return False


def main() -> None:
    """Main entry point for the downloader."""
    book_ids = load_book_ids(DEFAULT_BOOK_IDS_PATH)
    if not book_ids:
        logger.error("No book IDs found. Create book-ids.dat with one ID per line.")
        return

    logger.info(f"Found {len(book_ids)} book ID(s) to process")

    DEFAULT_STORE_PATH.mkdir(exist_ok=True)

    for book_id in book_ids:
        download_text(book_id, DEFAULT_STORE_PATH)
        download_metadata(book_id, DEFAULT_STORE_PATH)

    logger.info("Done")


if __name__ == "__main__":
    main()
