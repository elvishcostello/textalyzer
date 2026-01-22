"""Search Project Gutenberg for books by author using Gutendex API."""

import argparse
import logging
import sys
from urllib.parse import quote

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


def extract_last_name(name: str) -> str:
    """Extract the last name from an author name for API search.

    Returns the last word after splitting on spaces. This helps with authors
    who have initials (e.g., "P. G. Wodehouse" -> "Wodehouse") since the
    Gutendex API doesn't handle initials well in search queries.
    """
    parts = name.split()
    return parts[-1] if parts else name


def normalize_author_name(name: str) -> str:
    """Normalize author name for comparison.

    Handles "Last, First" format from Gutendex and converts to lowercase.
    Also normalizes initials by replacing periods with spaces and collapsing
    so "E. M. Forster" and "E.M. Forster" both become "e m forster".
    Strips parenthetical suffixes like "(Dorothy Leigh)" from names.
    """
    # Strip parenthetical suffixes (e.g., "Dorothy L. (Dorothy Leigh)")
    if "(" in name:
        name = name[: name.index("(")]
    # Gutendex returns names as "Austen, Jane" - normalize both formats
    if "," in name:
        parts = name.split(",", 1)
        name = f"{parts[1].strip()} {parts[0].strip()}"
    # Replace periods with spaces (for initials) and collapse multiple spaces
    name = name.replace(".", " ")
    name = " ".join(name.split())
    return name.lower()


def search_books_by_author(author: str) -> list[dict]:
    """Search Gutendex API for books by the given author.

    Returns a list of book dicts with 'id', 'title', and 'authors' keys.
    """
    logger.info(f"Searching for books by '{author}'...")

    all_books = []
    # Use only the last name for API search to handle authors with initials
    # (e.g., "P. G. Wodehouse" -> search for "Wodehouse")
    last_name = extract_last_name(author)
    encoded_last_name = quote(last_name)
    url: str | None = f"{GUTENDEX_API_URL}?search={encoded_last_name}&languages=en"
    normalized_search = normalize_author_name(author)

    max_pages = 100  # Safety limit
    page = 0
    while url:
        page += 1
        if page > max_pages:
            logger.warning(f"Reached maximum page limit ({max_pages}), stopping")
            break

        try:
            logger.debug(f"Fetching page {page}: {url}")
            response = httpx.get(url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError:  # pragma: no cover
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

    # Deduplicate by title, keeping highest ID (most recent)
    seen_titles: dict[str, dict] = {}
    for book in all_books:
        title = book["title"]
        if title not in seen_titles or book["id"] > seen_titles[title]["id"]:
            seen_titles[title] = book
    all_books = list(seen_titles.values())

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

    print(f"# Search: {args.author}")
    for book in books:
        print(format_book_line(book))


if __name__ == "__main__":
    main()
