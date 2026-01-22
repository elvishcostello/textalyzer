# Textalyzer

Download and analyze books from Project Gutenberg.

## Features

- **Author search**: Search Project Gutenberg for books by author name
- **Download books**: Fetch plain text books and metadata from Project Gutenberg
- **Full-text search**: Index book paragraphs into SQLite FTS5 for fast full-text search

## Installation

Requires Python 3.11+.

```bash
uv sync
```

## Usage

### 1. Find Books by Author

Search Project Gutenberg for books by a specific author:

```bash
uv run author-search "Jane Austen"
```

This queries the Gutendex API and outputs matching books as tab-separated fields:

```
ID    TITLE    SUBJECT    SUMMARY
```

Example:

```
1342    Pride and Prejudice    Courtship -- Fiction    "Pride and Prejudice" by Jane Austen...
158     Emma                   Bildungsromans          "Emma" by Jane Austen...
```

### 2. Download Books

Create a `books.csv` file with Project Gutenberg book IDs (tab-separated, first column is ID):

```
1342	Pride and Prejudice	...
2701	Moby Dick	...
84	Frankenstein	...
```

Then run the downloader:

```bash
uv run download
```

This downloads each book's text file and metadata to the `text-store/` directory.

### 3. Index Books

Index downloaded books into a searchable SQLite database:

```bash
uv run index
```

This creates `db/text-search.db` with an FTS5 virtual table containing book paragraphs.

## Gutendex Setup

Textalyzer uses a local [Gutendex](https://gutendex.com) instance for searching Project Gutenberg. You'll need to set this up before using the author search feature.

See [docker/gutendex/README.md](docker/gutendex/README.md) for setup instructions.

To use the public Gutendex API instead, edit `src/textalyzer/config.py`:

```python
GUTENDEX_API_URL = "https://gutendex.com/books/"
```

## Project Structure

```
src/textalyzer/
├── __init__.py       # Package metadata
├── author_search.py  # Search Gutendex API for books by author
├── config.py         # Shared configuration (paths, URLs, patterns)
├── downloader.py     # Download books and metadata from Gutenberg
└── indexer.py        # Index book paragraphs into SQLite FTS5
```

## Development

### Run Tests

```bash
uv run pytest
```

Tests include coverage reporting by default.

### Code Quality

```bash
uv run ruff format .   # Format code
uv run ruff check .    # Lint
uv run pyright         # Type check
```

## License

MIT
