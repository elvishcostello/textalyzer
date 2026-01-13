"""Index books into SQLite FTS5 for full-text search."""

import json
import logging
import re
import sqlite3
from pathlib import Path

from textalyzer.config import (
    DEFAULT_DB_PATH,
    DEFAULT_STORE_PATH,
    END_MARKER_RE,
    MIN_PARAGRAPH_LENGTH,
    SKIP_PARAGRAPH_PATTERNS,
    START_MARKER_RE,
    setup_logging,
)

setup_logging()
logger = logging.getLogger(__name__)


def extract_book_content(text: str) -> str | None:
    """Extract content between START and END markers."""
    start_match = START_MARKER_RE.search(text)
    end_match = END_MARKER_RE.search(text)

    if not start_match or not end_match:
        return None

    start_pos = start_match.end()
    end_pos = end_match.start()

    if start_pos >= end_pos:
        return None

    return text[start_pos:end_pos].strip()


def _should_skip_paragraph(text: str) -> bool:
    """Check if paragraph should be skipped based on patterns."""
    return any(pattern in text for pattern in SKIP_PARAGRAPH_PATTERNS)


def split_into_paragraphs(content: str) -> list[str]:
    """Split content into paragraphs on double newlines.

    Filters out paragraphs shorter than MIN_PARAGRAPH_LENGTH and
    paragraphs containing patterns in SKIP_PARAGRAPH_PATTERNS.
    """
    paragraphs = content.split("\n\n")
    return [
        p.strip()
        for p in paragraphs
        if len(p.strip()) >= MIN_PARAGRAPH_LENGTH and not _should_skip_paragraph(p)
    ]


def parse_author_title(full_title: str) -> tuple[str, str]:
    """Parse author and title from combined string like 'Title by Author'."""
    if " by " in full_title:
        parts = full_title.rsplit(" by ", 1)
        return parts[1].strip(), parts[0].strip()
    return "", full_title


def load_metadata(meta_path: Path) -> dict[str, str]:
    """Load metadata JSON and extract title field."""
    with open(meta_path) as f:
        meta_list = json.load(f)

    # Find the title meta tag (name="title")
    for item in meta_list:
        if item.get("name") == "title":
            full_title = item.get("content", "")
            author, title = parse_author_title(full_title)
            return {"author": author, "title": title}

    return {"author": "", "title": ""}


def get_book_id_from_filename(filename: str) -> str:
    """Extract book ID from filename like 'pg12345.txt' -> '12345'."""
    match = re.match(r"pg(\d+)\.txt", filename)
    return match.group(1) if match else ""


def create_database(db_path: Path) -> sqlite3.Connection:
    """Create database and FTS5 virtual table."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)

    # TODO: Make idempotent by checking if book already indexed (e.g., via a
    # separate 'indexed_books' table with book_id and file hash). For now,
    # we drop and recreate the table on each run for a clean slate.
    conn.execute("DROP TABLE IF EXISTS books")

    conn.execute("""
        CREATE VIRTUAL TABLE books USING fts5(
            book_id,
            paragraph_num,
            author,
            title,
            content,
            tokenize='porter unicode61'
        )
    """)

    return conn


def index_books(store_path: Path, conn: sqlite3.Connection) -> int:
    """Index all books from store into database. Returns count of paragraphs indexed."""
    indexed = 0

    for txt_file in sorted(store_path.glob("pg*.txt")):
        book_id = get_book_id_from_filename(txt_file.name)
        if not book_id:
            logger.warning(f"Could not extract ID from {txt_file.name}, skipping")
            continue

        meta_file = store_path / f"{book_id}-meta.json"
        if not meta_file.exists():
            logger.warning(f"[{book_id}] Metadata file not found, skipping")
            continue

        # Load metadata
        metadata = load_metadata(meta_file)

        # Load and extract content
        text = txt_file.read_text(encoding="utf-8", errors="replace")
        content = extract_book_content(text)

        if not content:
            logger.warning(f"[{book_id}] Could not extract content, skipping")
            continue

        # Split into paragraphs and insert each one
        paragraphs = split_into_paragraphs(content)

        for paragraph_num, paragraph in enumerate(paragraphs, start=1):
            conn.execute(
                "INSERT INTO books (book_id, paragraph_num, author, title, content) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    book_id,
                    paragraph_num,
                    metadata["author"],
                    metadata["title"],
                    paragraph,
                ),
            )
            indexed += 1

        logger.info(
            f"[{book_id}] Indexed: {metadata['title'][:50]}... "
            f"({len(paragraphs)} paragraphs)"
        )

    conn.commit()
    return indexed


def main() -> None:
    """Main entry point for the indexer."""
    if not DEFAULT_STORE_PATH.exists():
        logger.error(f"Store path not found: {DEFAULT_STORE_PATH}")
        logger.error("Run textalyzer-download first to download books.")
        return

    logger.info(f"Creating database at {DEFAULT_DB_PATH}")
    conn = create_database(DEFAULT_DB_PATH)

    try:
        indexed = index_books(DEFAULT_STORE_PATH, conn)
        logger.info(f"Done. Indexed {indexed} book(s).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
