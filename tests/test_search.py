"""Tests for search module."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from textalyzer.search import (
    execute_query,
    format_result_block,
    load_query_file,
    main,
    parse_query_line,
)


class TestParseQueryLine:
    """Tests for parse_query_line function."""

    def test_parse_and_query(self) -> None:
        """parse_query_line should parse AND queries."""
        terms, operator, comment = parse_query_line("term1 & term2 & term3")

        assert terms == ["term1", "term2", "term3"]
        assert operator == "AND"
        assert comment == ""

    def test_parse_or_query(self) -> None:
        """parse_query_line should parse OR queries."""
        terms, operator, comment = parse_query_line("term1 | term2 | term3")

        assert terms == ["term1", "term2", "term3"]
        assert operator == "OR"
        assert comment == ""

    def test_parse_with_comment(self) -> None:
        """parse_query_line should extract comments."""
        terms, operator, comment = parse_query_line("term1 & term2 # this is a comment")

        assert terms == ["term1", "term2"]
        assert operator == "AND"
        assert comment == "this is a comment"

    def test_parse_single_term(self) -> None:
        """parse_query_line should handle single terms."""
        terms, operator, comment = parse_query_line("singleterm")

        assert terms == ["singleterm"]
        assert operator == "AND"
        assert comment == ""

    def test_parse_strips_whitespace(self) -> None:
        """parse_query_line should strip whitespace from terms."""
        terms, operator, comment = parse_query_line("  term1  &  term2  ")

        assert terms == ["term1", "term2"]

    def test_parse_mixed_operators_raises(self) -> None:
        """parse_query_line should raise on mixed operators."""
        with pytest.raises(ValueError, match="Cannot mix"):
            parse_query_line("term1 & term2 | term3")

    def test_parse_empty_query_raises(self) -> None:
        """parse_query_line should raise on empty query."""
        with pytest.raises(ValueError, match="Empty query"):
            parse_query_line("")

    def test_parse_only_comment_raises(self) -> None:
        """parse_query_line should raise on comment-only line."""
        with pytest.raises(ValueError, match="Empty query"):
            parse_query_line("# just a comment")

    def test_parse_whitespace_only_raises(self) -> None:
        """parse_query_line should raise on whitespace-only query."""
        with pytest.raises(ValueError, match="Empty query"):
            parse_query_line("   ")

    def test_parse_empty_terms_after_split_raises(self) -> None:
        """parse_query_line should raise if all terms are empty."""
        with pytest.raises(ValueError, match="No search terms"):
            parse_query_line("& &")

    def test_parse_comment_with_hash_in_term(self) -> None:
        """parse_query_line should split on first hash only."""
        terms, operator, comment = parse_query_line("term1 # comment with # hash")

        assert terms == ["term1"]
        assert comment == "comment with # hash"


class TestExecuteQuery:
    """Tests for execute_query function."""

    def test_execute_and_query(self, tmp_path: Path) -> None:
        """execute_query should build correct AND query."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 1, "Author", "Title", "hello world foo"),
        )
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 2, "Author", "Title", "hello bar"),
        )
        conn.commit()

        results = execute_query(conn, ["hello", "world"], "AND")
        conn.close()

        assert len(results) == 1
        assert results[0][4] == "hello world foo"

    def test_execute_or_query(self, tmp_path: Path) -> None:
        """execute_query should build correct OR query."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 1, "Author", "Title", "hello world"),
        )
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 2, "Author", "Title", "goodbye world"),
        )
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 3, "Author", "Title", "nothing here"),
        )
        conn.commit()

        results = execute_query(conn, ["hello", "goodbye"], "OR")
        conn.close()

        assert len(results) == 2

    def test_execute_query_orders_by_paragraph_num(self, tmp_path: Path) -> None:
        """execute_query should order results by paragraph_num."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 100, "Author", "Title", "hello world"),
        )
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 5, "Author", "Title", "hello there"),
        )
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 50, "Author", "Title", "hello again"),
        )
        conn.commit()

        results = execute_query(conn, ["hello"], "AND")
        conn.close()

        assert results[0][1] == 5
        assert results[1][1] == 50
        assert results[2][1] == 100

    def test_execute_query_limits_to_100(self, tmp_path: Path) -> None:
        """execute_query should limit results to 100."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        for i in range(150):
            conn.execute(
                "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
                ("1", i, "Author", "Title", "hello world"),
            )
        conn.commit()

        results = execute_query(conn, ["hello"], "AND")
        conn.close()

        assert len(results) == 100


class TestFormatResultBlock:
    """Tests for format_result_block function."""

    def test_format_with_results(self) -> None:
        """format_result_block should format results as TSV."""
        rows = [
            ("1", 10, "Jane Austen", "Pride", "Content here"),
            ("2", 20, "Mark Twain", "Tom Sawyer", "More content"),
        ]

        result = format_result_block(rows, "term1 & term2", "test comment")

        lines = result.split("\n")
        assert lines[0] == "# Query: term1 & term2"
        assert lines[1] == "# Original comment: test comment"
        assert lines[2] == "book_id\tparagraph_num\tauthor\ttitle\tcontent"
        assert lines[3] == "1\t10\tJane Austen\tPride\tContent here"
        assert lines[4] == "2\t20\tMark Twain\tTom Sawyer\tMore content"

    def test_format_without_comment(self) -> None:
        """format_result_block should omit comment line if empty."""
        rows = [("1", 10, "Author", "Title", "Content")]

        result = format_result_block(rows, "term1", "")

        lines = result.split("\n")
        assert lines[0] == "# Query: term1"
        assert lines[1] == "book_id\tparagraph_num\tauthor\ttitle\tcontent"

    def test_format_empty_results(self) -> None:
        """format_result_block should show no results message for empty."""
        result = format_result_block([], "term1 & term2", "a comment")

        lines = result.split("\n")
        assert lines[0] == "# Query: term1 & term2"
        assert lines[1] == "# Original comment: a comment"
        assert lines[2] == "# No results found"
        assert len(lines) == 3

    def test_format_escapes_tabs_in_content(self) -> None:
        """format_result_block should escape tabs in content."""
        rows = [("1", 10, "Author", "Title", "Content\twith\ttabs")]

        result = format_result_block(rows, "term1", "")

        lines = result.split("\n")
        assert "Content with tabs" in lines[2]
        assert lines[2].count("\t") == 4  # Only column separators

    def test_format_escapes_newlines_in_content(self) -> None:
        """format_result_block should escape newlines in content."""
        rows = [("1", 10, "Author", "Title", "Content\nwith\nnewlines")]

        result = format_result_block(rows, "term1", "")

        lines = result.split("\n")
        assert "Content with newlines" in lines[2]


class TestLoadQueryFile:
    """Tests for load_query_file function."""

    def test_load_basic_file(self, tmp_path: Path) -> None:
        """load_query_file should load non-empty lines."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("term1 & term2\nterm3 | term4\n")

        result = load_query_file(query_file)

        assert result == ["term1 & term2", "term3 | term4"]

    def test_load_skips_empty_lines(self, tmp_path: Path) -> None:
        """load_query_file should skip empty lines."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("term1\n\nterm2\n\n\nterm3\n")

        result = load_query_file(query_file)

        assert result == ["term1", "term2", "term3"]

    def test_load_skips_comment_only_lines(self, tmp_path: Path) -> None:
        """load_query_file should skip comment-only lines."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("term1\n# this is a comment\nterm2\n")

        result = load_query_file(query_file)

        assert result == ["term1", "term2"]

    def test_load_preserves_inline_comments(self, tmp_path: Path) -> None:
        """load_query_file should preserve inline comments."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("term1 & term2 # inline comment\n")

        result = load_query_file(query_file)

        assert result == ["term1 & term2 # inline comment"]

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """load_query_file should return empty list for empty file."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("")

        result = load_query_file(query_file)

        assert result == []


class TestMain:
    """Tests for main function."""

    def test_main_exits_if_query_file_missing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main should exit if query file doesn't exist."""
        with patch("sys.argv", ["search", str(tmp_path / "missing.txt")]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Query file not found" in captured.err

    def test_main_exits_if_database_missing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main should exit if database doesn't exist."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("term1\n")

        with patch("sys.argv", ["search", str(query_file)]):
            with patch("textalyzer.search.DEFAULT_DB_PATH", tmp_path / "missing.db"):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Database not found" in captured.err

    def test_main_exits_on_syntax_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main should exit on query syntax error."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("term1 & term2 | term3\n")

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        conn.close()

        with patch("sys.argv", ["search", str(query_file), "--db", str(db_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error on line 1" in captured.err
        assert "Cannot mix" in captured.err

    def test_main_empty_file_no_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main should produce no output for empty query file."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("")

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        conn.close()

        with patch("sys.argv", ["search", str(query_file), "--db", str(db_path)]):
            main()

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_main_outputs_results(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main should output query results as TSV."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("hello # test query\n")

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("123", 45, "Jane Austen", "Pride", "hello world"),
        )
        conn.commit()
        conn.close()

        with patch("sys.argv", ["search", str(query_file), "--db", str(db_path)]):
            main()

        captured = capsys.readouterr()
        assert "# Query: hello" in captured.out
        assert "# Original comment: test query" in captured.out
        assert "book_id\tparagraph_num" in captured.out
        assert "123\t45\tJane Austen\tPride\thello world" in captured.out

    def test_main_multiple_queries(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main should handle multiple queries."""
        query_file = tmp_path / "queries.txt"
        query_file.write_text("hello\ngoodbye\n")

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE VIRTUAL TABLE books USING fts5(
                book_id, paragraph_num, author, title, content
            )
        """)
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("1", 1, "Author", "Title", "hello there"),
        )
        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?)",
            ("2", 2, "Author", "Title", "goodbye friend"),
        )
        conn.commit()
        conn.close()

        with patch("sys.argv", ["search", str(query_file), "--db", str(db_path)]):
            main()

        captured = capsys.readouterr()
        assert "# Query: hello" in captured.out
        assert "# Query: goodbye" in captured.out
        assert "hello there" in captured.out
        assert "goodbye friend" in captured.out
