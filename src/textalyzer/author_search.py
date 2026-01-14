"""Search Project Gutenberg for books by author using Gutendex API."""

import argparse
import logging

import httpx

from textalyzer.config import (
    GUTENDEX_API_URL,
    setup_logging,
)

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


def search_books_by_author(author: str) -> list[dict]:
    """Search Gutendex API for books by the given author.

    Returns a list of book dicts with 'id', 'title', and 'authors' keys.
    """
    logger.info(f"Searching for books by '{author}'...")

    all_books = []
    url: str | None = GUTENDEX_API_URL
    params: dict[str, str] | None = {"search": author}
    normalized_search = normalize_author_name(author)

    max_pages = 100  # Safety limit
    page = 0
    while url:
        page += 1
        if page > max_pages:
            logger.warning(f"Reached maximum page limit ({max_pages}), stopping")
            break

        try:
            logger.debug(f"Fetching page {page}: {url} with params {params}")
            response = httpx.get(url, params=params, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch from Gutendex: {e}")
            break

        count = data.get("count", 0)
        results = data.get("results", [])
        next_url = data.get("next")
        logger.debug(f"Page {page}: count={count}, results={len(results)}, next={next_url}")

        # Filter results to only include books where author matches
        matches_on_page = 0
        for book in results:
            for book_author in book.get("authors", []):
                author_name = book_author.get("name", "")
                if normalized_search in normalize_author_name(author_name):
                    all_books.append(
                        {
                            "id": book["id"],
                            "title": book["title"],
                            "authors": [a["name"] for a in book.get("authors", [])],
                        }
                    )
                    matches_on_page += 1
                    break

        logger.debug(f"Page {page}: {matches_on_page} matches found")

        # Follow pagination - next URL already contains query params
        url = next_url
        params = None

    logger.info(f"Found {len(all_books)} book(s) by '{author}'")
    return all_books


def format_book_line(book: dict) -> str:
    """Format a book as a book-ids.dat line.

    Returns a string like '1342  # Pride and Prejudice'.
    """
    book_id = str(book["id"])
    title = book["title"][:50]  # Truncate long titles
    return f"{book_id}  # {title}"


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
