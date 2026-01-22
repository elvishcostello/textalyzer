"""Search Project Gutenberg for books by author using Gutendex API."""

import argparse
import logging
import sys

import httpx

from textalyzer.config import (
    GUTENDEX_API_URL,
    setup_logging,
)

GUTENDEX_CONNECTION_ERROR = """
Error: Cannot connect to Gutendex API at {url}

If using the local Docker instance:
  1. Ensure Docker is running (colima start / Docker Desktop)
  2. Start the Gutendex container: docker-compose up -d
  3. Wait for the catalog import to complete (check: docker-compose logs -f gutendex)

For the public API, edit src/textalyzer/config.py:
  GUTENDEX_API_URL = "https://gutendex.com/books/"

See docker/gutendex/README.md for setup instructions.
""".strip()

setup_logging()
logger = logging.getLogger(__name__)


def normalize_author_name(name: str) -> str:
    """Normalize author name for comparison.

    Handles "Last, First" format from Gutendex and converts to lowercase.
    """
    # Gutendex returns names as "Austen, Jane" - normalize both formats
    if "," in name:
        parts = name.split(",", 1)
        name = f"{parts[1].strip()} {parts[0].strip()}"
    return name.lower()


def author_matches(search_name: str, api_name: str) -> bool:
    """Check if all words from search_name appear in api_name.

    Uses soft matching so extra words in api_name (like full names in
    parentheses) don't prevent a match.
    """
    search_normalized = normalize_author_name(search_name)
    api_normalized = normalize_author_name(api_name)
    search_words = set(search_normalized.split())
    api_words = set(api_normalized.split())
    return search_words <= api_words


def search_books_by_author(author: str) -> list[dict]:
    """Search Gutendex API for books by the given author.

    Returns a list of book dicts with 'id', 'title', 'authors', 'subjects',
    and 'summaries' keys.
    """
    logger.info(f"Searching for books by '{author}'...")

    all_books = []
    url: str | None = GUTENDEX_API_URL
    params: dict[str, str] | None = {"search": author, "languages": "en"}

    max_pages = 100  # Safety limit
    page = 0
    while url:
        page += 1
        if page > max_pages:
            logger.warning(f"Reached maximum page limit ({max_pages}), stopping")
            break

        try:
            logger.debug(f"Fetching page {page}: {url} with params {params}")
            response = httpx.get(
                url, params=params, timeout=30.0, follow_redirects=True
            )
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError:
            error_msg = GUTENDEX_CONNECTION_ERROR.format(url=GUTENDEX_API_URL)
            print(error_msg, file=sys.stderr)
            sys.exit(1)
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch from Gutendex: {e}")
            break

        count = data.get("count", 0)
        results = data.get("results", [])
        next_url = data.get("next")
        logger.debug(
            f"Page {page}: count={count}, results={len(results)}, next={next_url}"
        )

        # Filter results to only include books where author matches
        matches_on_page = 0
        for book in results:
            for book_author in book.get("authors", []):
                author_name = book_author.get("name", "")
                if author_matches(author, author_name):
                    all_books.append(
                        {
                            "id": book["id"],
                            "title": book["title"],
                            "authors": [a["name"] for a in book.get("authors", [])],
                            "subjects": book.get("subjects", []),
                            "summaries": book.get("summaries", []),
                        }
                    )
                    matches_on_page += 1
                    break

        logger.debug(f"Page {page}: {matches_on_page} matches found")

        # Follow pagination - next URL already contains query params
        url = next_url
        params = None

    # Deduplicate by title, keeping the book with the highest ID
    seen_titles: dict[str, dict] = {}
    for book in all_books:
        title = book["title"]
        if title not in seen_titles or book["id"] > seen_titles[title]["id"]:
            seen_titles[title] = book
    all_books = list(seen_titles.values())

    logger.info(f"Found {len(all_books)} book(s) by '{author}'")
    return all_books


def format_book_line(book: dict) -> str:
    """Format a book as a tab-separated line.

    Returns a tab-separated string with: ID, TITLE, SUBJECT, SUMMARY.
    """
    book_id = str(book["id"])
    title = book["title"]
    subjects = book.get("subjects", [])
    subject = subjects[0] if subjects else ""
    summaries = book.get("summaries", [])
    summary = summaries[0] if summaries else ""
    return f"{book_id}\t{title}\t{subject}\t{summary}"


def main() -> None:
    """Main entry point for author search command."""
    parser = argparse.ArgumentParser(
        description="Search Project Gutenberg for books by author"
    )
    parser.add_argument("author", help="Author name to search for")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    books = search_books_by_author(args.author)

    for book in books:
        print(format_book_line(book))


if __name__ == "__main__":
    main()
