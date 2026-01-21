"""Search indexed books using FTS5 queries from a query file."""

import argparse
import sqlite3
import sys
from pathlib import Path

from textalyzer.config import DEFAULT_DB_PATH

COLUMNS = ["book_id", "paragraph_num", "author", "title", "content"]
MAX_RESULTS = 100


def parse_query_line(line: str) -> tuple[list[str], str, str]:
    """Parse a query line into (terms, operator, comment).

    Returns (terms, 'AND'|'OR', comment).
    Raises ValueError on syntax error (mixed operators, empty terms).
    """
    # Extract comment if present
    comment = ""
    if "#" in line:
        line, comment = line.split("#", 1)
        comment = comment.strip()

    line = line.strip()
    if not line:
        raise ValueError("Empty query")

    # Check for operator
    has_and = "&" in line
    has_or = "|" in line

    if has_and and has_or:
        raise ValueError("Cannot mix '&' and '|' operators in the same query")

    if has_and:
        operator = "AND"
        terms = [t.strip() for t in line.split("&")]
    elif has_or:
        operator = "OR"
        terms = [t.strip() for t in line.split("|")]
    else:
        # Single term, treat as AND (doesn't matter for single term)
        operator = "AND"
        terms = [line.strip()]

    # Validate terms
    terms = [t for t in terms if t]
    if not terms:
        raise ValueError("No search terms found")

    return terms, operator, comment


def execute_query(
    conn: sqlite3.Connection, terms: list[str], operator: str
) -> list[tuple[str, int, str, str, str]]:
    """Execute FTS5 query, return up to MAX_RESULTS rows ordered by paragraph_num."""
    # Build WHERE clause with parameterized queries
    match_clauses = ["content MATCH ?" for _ in terms]
    where_clause = f" {operator} ".join(match_clauses)

    sql = f"""
        SELECT book_id, paragraph_num, author, title, content
        FROM books
        WHERE {where_clause}
        ORDER BY paragraph_num
        LIMIT {MAX_RESULTS}
    """

    cursor = conn.execute(sql, terms)
    return cursor.fetchall()


def format_result_block(
    rows: list[tuple[str, int, str, str, str]], query: str, comment: str
) -> str:
    """Format results as TSV with comment header."""
    lines = []

    # Query comment
    lines.append(f"# Query: {query}")
    if comment:
        lines.append(f"# Original comment: {comment}")

    if not rows:
        lines.append("# No results found")
    else:
        # Header row
        lines.append("\t".join(COLUMNS))
        # Data rows
        for row in rows:
            # Escape tabs and newlines in content
            formatted = []
            for val in row:
                str_val = str(val)
                str_val = str_val.replace("\t", " ").replace("\n", " ")
                formatted.append(str_val)
            lines.append("\t".join(formatted))

    return "\n".join(lines)


def load_query_file(path: Path) -> list[str]:
    """Load and return non-empty, non-comment-only lines from query file."""
    with path.open() as f:
        lines = f.readlines()

    result = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines and comment-only lines
        if stripped and not stripped.startswith("#"):
            result.append(stripped)

    return result


def main() -> None:
    """Main entry point for search command."""
    parser = argparse.ArgumentParser(
        description="Search indexed books using queries from a file"
    )
    parser.add_argument("query_file", type=Path, help="Path to query file")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to database (default: {DEFAULT_DB_PATH})",
    )
    args = parser.parse_args()

    # Validate query file exists
    if not args.query_file.exists():
        print(f"Error: Query file not found: {args.query_file}", file=sys.stderr)
        sys.exit(1)

    # Validate database exists
    if not args.db.exists():
        print(f"Error: Database not found: {args.db}", file=sys.stderr)
        print("Run textalyzer-index first to create the database.", file=sys.stderr)
        sys.exit(1)

    # Load queries
    query_lines = load_query_file(args.query_file)
    if not query_lines:
        return  # Empty file, nothing to do

    # Parse all queries first to catch syntax errors early
    parsed_queries: list[tuple[str, list[str], str, str]] = []
    for i, line in enumerate(query_lines, start=1):
        try:
            terms, operator, comment = parse_query_line(line)
            parsed_queries.append((line, terms, operator, comment))
        except ValueError as e:
            print(f"Error on line {i}: {e}", file=sys.stderr)
            print(f"  Line: {line}", file=sys.stderr)
            sys.exit(1)

    # Execute queries and output results
    conn = sqlite3.connect(args.db)
    try:
        results = []
        for original_line, terms, operator, comment in parsed_queries:
            rows = execute_query(conn, terms, operator)
            # Reconstruct query string for display (without comment)
            query_display = original_line.split("#")[0].strip()
            result_block = format_result_block(rows, query_display, comment)
            results.append(result_block)

        print("\n\n".join(results))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
