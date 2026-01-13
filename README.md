# Textalyzer

Download and analyze books from Project Gutenberg.

## Features

- **Download books**: Fetch plain text books and metadata from Project Gutenberg
- **Full-text search**: Index books into SQLite FTS5 for fast full-text search

## Installation

Requires Python 3.11+.

```bash
uv sync
```

## Usage

### 1. Download Books

Create a `book-ids.dat` file with Project Gutenberg book IDs (one per line):

```
# Pride and Prejudice
1342
# Moby Dick
2701
# Frankenstein
84
```

Then run the downloader:

```bash
uv run textalyzer-download
```

This downloads each book's text file and metadata to the `text-store/` directory.

### 2. Index Books

Index downloaded books into a searchable SQLite database:

```bash
uv run textalyzer-search
```

This creates `db/text-search.db` with an FTS5 virtual table containing the book content.

## Project Structure

```
src/textalyzer/
├── __init__.py      # Package metadata
├── config.py        # Shared configuration (paths, URLs, patterns)
├── downloader.py    # Download books and metadata from Gutenberg
└── indexer.py       # Index books into SQLite FTS5
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
