"""Tests for indexer module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from textalyzer.indexer import (
    create_database,
    extract_book_content,
    get_book_id_from_filename,
    index_books,
    load_metadata,
    main,
    parse_author_title,
    split_into_paragraphs,
)


class TestExtractBookContent:
    """Tests for extract_book_content function."""

    def test_extract_book_content_success(self, sample_gutenberg_text: str) -> None:
        """extract_book_content should extract content between markers."""
        result = extract_book_content(sample_gutenberg_text)

        assert result is not None
        assert "first paragraph" in result
        assert "second paragraph" in result
        assert "START OF THE PROJECT" not in result
        assert "END OF THE PROJECT" not in result

    def test_extract_book_content_no_start_marker(self) -> None:
        """extract_book_content should return None without start marker."""
        text = """Some text here
*** END OF THE PROJECT GUTENBERG EBOOK TEST ***
More text"""

        result = extract_book_content(text)

        assert result is None

    def test_extract_book_content_no_end_marker(self) -> None:
        """extract_book_content should return None without end marker."""
        text = """Some text here
*** START OF THE PROJECT GUTENBERG EBOOK TEST ***
Content without end marker"""

        result = extract_book_content(text)

        assert result is None

    def test_extract_book_content_markers_wrong_order(self) -> None:
        """extract_book_content should return None if markers in wrong order."""
        text = """
*** END OF THE PROJECT GUTENBERG EBOOK TEST ***
Content here
*** START OF THE PROJECT GUTENBERG EBOOK TEST ***
"""

        result = extract_book_content(text)

        assert result is None

    def test_extract_book_content_strips_whitespace(
        self, sample_gutenberg_text: str
    ) -> None:
        """extract_book_content should strip leading/trailing whitespace."""
        result = extract_book_content(sample_gutenberg_text)

        assert result is not None
        assert not result.startswith("\n")
        assert not result.endswith("\n")


class TestSplitIntoParagraphs:
    """Tests for split_into_paragraphs function."""

    def test_split_into_paragraphs_basic(self) -> None:
        """split_into_paragraphs should split on double newlines."""
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

        result = split_into_paragraphs(content)

        assert len(result) == 3
        assert result[0] == "First paragraph."
        assert result[1] == "Second paragraph."
        assert result[2] == "Third paragraph."

    def test_split_into_paragraphs_filters_short(self) -> None:
        """split_into_paragraphs should filter short paragraphs."""
        content = "OK.\n\nAB\n\nThis is long enough."

        result = split_into_paragraphs(content)

        # "AB" is only 2 chars, should be filtered (MIN_PARAGRAPH_LENGTH is 4)
        # "OK." is 3 chars, should be filtered
        assert len(result) == 1
        assert result[0] == "This is long enough."

    def test_split_into_paragraphs_strips_whitespace(self) -> None:
        """split_into_paragraphs should strip whitespace from each paragraph."""
        content = "  First paragraph.  \n\n  Second paragraph.  "

        result = split_into_paragraphs(content)

        assert result[0] == "First paragraph."
        assert result[1] == "Second paragraph."

    def test_split_into_paragraphs_empty_content(self) -> None:
        """split_into_paragraphs should return empty list for empty content."""
        result = split_into_paragraphs("")

        assert result == []

    def test_split_into_paragraphs_single_paragraph(self) -> None:
        """split_into_paragraphs should handle single paragraph."""
        content = "Just one paragraph here."

        result = split_into_paragraphs(content)

        assert len(result) == 1
        assert result[0] == "Just one paragraph here."

    def test_split_into_paragraphs_multiple_blank_lines(self) -> None:
        """split_into_paragraphs should handle multiple consecutive blank lines."""
        content = "First.\n\n\n\nSecond."

        result = split_into_paragraphs(content)

        # Multiple blank lines create empty strings that get filtered
        assert len(result) == 2

    def test_split_into_paragraphs_filters_copyright(self) -> None:
        """split_into_paragraphs should filter paragraphs with [_Copyright."""
        content = "Normal paragraph.\n\n[_Copyright 1923]\n\nAnother paragraph."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[_Copyright" not in p for p in result)

    def test_split_into_paragraphs_filters_illustration(self) -> None:
        """split_into_paragraphs should filter paragraphs with [Illustration]."""
        content = "Normal paragraph.\n\n[Illustration]\n\nAnother paragraph."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[Illustration" not in p for p in result)

    def test_split_into_paragraphs_filters_illustration_with_caption(self) -> None:
        """split_into_paragraphs should filter [Illustration: caption]."""
        content = "Normal paragraph.\n\n[Illustration: A lovely scene]\n\nAnother."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[Illustration" not in p for p in result)

    def test_split_into_paragraphs_filters_blank_page(self) -> None:
        """split_into_paragraphs should filter [Blank Page] markers."""
        content = "Normal paragraph.\n\n[Blank Page]\n\nAnother paragraph."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[Blank Page]" not in p for p in result)

    def test_split_into_paragraphs_filters_proofreader_comments(self) -> None:
        """split_into_paragraphs should filter [** proofreader comments."""
        content = "Normal paragraph.\n\n[** unclear text]\n\nAnother paragraph."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[**" not in p for p in result)

    def test_split_into_paragraphs_filters_transcriber_note(self) -> None:
        """split_into_paragraphs should filter [Transcriber's Note."""
        content = "Normal paragraph.\n\n[Transcriber's Note: Fixed typo]\n\nAnother."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[Transcriber's Note" not in p for p in result)

    def test_split_into_paragraphs_filters_editor_note(self) -> None:
        """split_into_paragraphs should filter [Editor's Note."""
        content = "Normal paragraph.\n\n[Editor's Note: See appendix]\n\nAnother."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[Editor's Note" not in p for p in result)

    def test_split_into_paragraphs_filters_technical_note(self) -> None:
        """split_into_paragraphs should filter [Technical Note."""
        content = "Normal paragraph.\n\n[Technical Note: Formula error]\n\nAnother."

        result = split_into_paragraphs(content)

        assert len(result) == 2
        assert all("[Technical Note" not in p for p in result)


class TestParseAuthorTitle:
    """Tests for parse_author_title function."""

    def test_parse_author_title_with_by(self) -> None:
        """parse_author_title should split on ' by '."""
        result = parse_author_title("Pride and Prejudice by Jane Austen")

        assert result == ("Jane Austen", "Pride and Prejudice")

    def test_parse_author_title_without_by(self) -> None:
        """parse_author_title should return empty author without ' by '."""
        result = parse_author_title("Untitled Work")

        assert result == ("", "Untitled Work")

    def test_parse_author_title_multiple_by(self) -> None:
        """parse_author_title should split on last ' by '."""
        result = parse_author_title("Stand by Me by Stephen King")

        assert result == ("Stephen King", "Stand by Me")

    def test_parse_author_title_strips_whitespace(self) -> None:
        """parse_author_title should strip whitespace from results."""
        result = parse_author_title("  Title  by  Author  ")

        assert result == ("Author", "Title")


class TestLoadMetadata:
    """Tests for load_metadata function."""

    def test_load_metadata_finds_title(
        self, tmp_path: Path, sample_metadata_json: str
    ) -> None:
        """load_metadata should find and parse title."""
        meta_file = tmp_path / "meta.json"
        meta_file.write_text(sample_metadata_json)

        result = load_metadata(meta_file)

        assert result["title"] == "Pride and Prejudice"
        assert result["author"] == "Jane Austen"

    def test_load_metadata_no_title_tag(self, tmp_path: Path) -> None:
        """load_metadata should return empty strings without title tag."""
        meta_file = tmp_path / "meta.json"
        meta_file.write_text('[{"name": "other", "content": "value"}]')

        result = load_metadata(meta_file)

        assert result == {"author": "", "title": ""}

    def test_load_metadata_empty_json_array(self, tmp_path: Path) -> None:
        """load_metadata should return empty strings for empty array."""
        meta_file = tmp_path / "meta.json"
        meta_file.write_text("[]")

        result = load_metadata(meta_file)

        assert result == {"author": "", "title": ""}


class TestGetBookIdFromFilename:
    """Tests for get_book_id_from_filename function."""

    def test_get_book_id_standard_format(self) -> None:
        """get_book_id_from_filename should extract ID from pg*.txt."""
        result = get_book_id_from_filename("pg12345.txt")

        assert result == "12345"

    def test_get_book_id_large_number(self) -> None:
        """get_book_id_from_filename should handle large IDs."""
        result = get_book_id_from_filename("pg9999999.txt")

        assert result == "9999999"

    def test_get_book_id_invalid_format(self) -> None:
        """get_book_id_from_filename should return empty for invalid format."""
        result = get_book_id_from_filename("book12345.txt")

        assert result == ""

    def test_get_book_id_wrong_extension(self) -> None:
        """get_book_id_from_filename should return empty for wrong extension."""
        result = get_book_id_from_filename("pg12345.pdf")

        assert result == ""


class TestCreateDatabase:
    """Tests for create_database function."""

    def test_create_database_creates_parent_dirs(self, tmp_path: Path) -> None:
        """create_database should create parent directories."""
        db_path = tmp_path / "nested" / "dir" / "test.db"

        conn = create_database(db_path)

        try:
            assert db_path.parent.exists()
        finally:
            conn.close()

    def test_create_database_creates_file(self, tmp_path: Path) -> None:
        """create_database should create the database file."""
        db_path = tmp_path / "test.db"

        conn = create_database(db_path)

        try:
            assert db_path.exists()
        finally:
            conn.close()

    def test_create_database_creates_books_table(self, tmp_path: Path) -> None:
        """create_database should create books FTS5 table."""
        db_path = tmp_path / "test.db"

        conn = create_database(db_path)

        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='books'"
            )
            result = cursor.fetchone()
            assert result is not None
        finally:
            conn.close()

    @patch("textalyzer.indexer.sqlite3.connect")
    def test_create_database_drops_existing_table(
        self, mock_connect: MagicMock, tmp_path: Path
    ) -> None:
        """create_database should drop existing books table."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        db_path = tmp_path / "test.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        create_database(db_path)

        calls = [str(call) for call in mock_conn.execute.call_args_list]
        assert any("DROP TABLE IF EXISTS books" in call for call in calls)


class TestIndexBooks:
    """Tests for index_books function."""

    def test_index_books_empty_store(self, tmp_path: Path) -> None:
        """index_books should return 0 for empty store."""
        mock_conn = MagicMock()

        result = index_books(tmp_path, mock_conn)

        assert result == 0

    def test_index_books_skips_without_metadata(
        self, tmp_path: Path, sample_gutenberg_text: str
    ) -> None:
        """index_books should skip files without metadata."""
        (tmp_path / "pg12345.txt").write_text(sample_gutenberg_text)
        mock_conn = MagicMock()

        result = index_books(tmp_path, mock_conn)

        assert result == 0
        mock_conn.execute.assert_not_called()

    def test_index_books_skips_invalid_filename(
        self, tmp_path: Path, sample_gutenberg_text: str
    ) -> None:
        """index_books should skip files that don't match pg*.txt pattern."""
        # Create a file that matches glob but has invalid ID format
        (tmp_path / "pg.txt").write_text(sample_gutenberg_text)
        mock_conn = MagicMock()

        result = index_books(tmp_path, mock_conn)

        assert result == 0

    def test_index_books_indexes_valid_book(
        self,
        tmp_path: Path,
        sample_gutenberg_text: str,
        sample_metadata_json: str,
    ) -> None:
        """index_books should index book paragraphs with text and metadata."""
        (tmp_path / "pg12345.txt").write_text(sample_gutenberg_text)
        (tmp_path / "12345-meta.json").write_text(sample_metadata_json)
        mock_conn = MagicMock()

        result = index_books(tmp_path, mock_conn)

        # Sample text has 3 paragraphs
        assert result == 3
        assert mock_conn.execute.call_count == 3
        mock_conn.commit.assert_called_once()

    def test_index_books_skips_invalid_content(
        self, tmp_path: Path, sample_metadata_json: str
    ) -> None:
        """index_books should skip books without valid content markers."""
        (tmp_path / "pg12345.txt").write_text("No markers here")
        (tmp_path / "12345-meta.json").write_text(sample_metadata_json)
        mock_conn = MagicMock()

        result = index_books(tmp_path, mock_conn)

        assert result == 0

    def test_index_books_processes_multiple_books(
        self,
        tmp_path: Path,
        sample_gutenberg_text: str,
        sample_metadata_json: str,
    ) -> None:
        """index_books should process multiple books."""
        for book_id in ["111", "222", "333"]:
            (tmp_path / f"pg{book_id}.txt").write_text(sample_gutenberg_text)
            (tmp_path / f"{book_id}-meta.json").write_text(sample_metadata_json)
        mock_conn = MagicMock()

        result = index_books(tmp_path, mock_conn)

        # 3 books * 3 paragraphs each = 9 paragraphs
        assert result == 9


class TestMain:
    """Tests for main function."""

    @patch("textalyzer.indexer.DEFAULT_STORE_PATH")
    def test_main_exits_if_store_missing(self, mock_store_path: MagicMock) -> None:
        """main should exit early if store path doesn't exist."""
        mock_store_path.exists.return_value = False

        with patch("textalyzer.indexer.create_database") as mock_create_db:
            main()
            mock_create_db.assert_not_called()

    @patch("textalyzer.indexer.index_books")
    @patch("textalyzer.indexer.create_database")
    @patch("textalyzer.indexer.DEFAULT_STORE_PATH")
    @patch("textalyzer.indexer.DEFAULT_DB_PATH")
    def test_main_creates_database_and_indexes(
        self,
        mock_db_path: MagicMock,
        mock_store_path: MagicMock,
        mock_create_db: MagicMock,
        mock_index_books: MagicMock,
    ) -> None:
        """main should create database and index books."""
        mock_store_path.exists.return_value = True
        mock_conn = MagicMock()
        mock_create_db.return_value = mock_conn
        mock_index_books.return_value = 5

        main()

        mock_create_db.assert_called_once()
        mock_index_books.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("textalyzer.indexer.index_books")
    @patch("textalyzer.indexer.create_database")
    @patch("textalyzer.indexer.DEFAULT_STORE_PATH")
    @patch("textalyzer.indexer.DEFAULT_DB_PATH")
    def test_main_closes_connection_on_error(
        self,
        mock_db_path: MagicMock,
        mock_store_path: MagicMock,
        mock_create_db: MagicMock,
        mock_index_books: MagicMock,
    ) -> None:
        """main should close connection even if indexing fails."""
        mock_store_path.exists.return_value = True
        mock_conn = MagicMock()
        mock_create_db.return_value = mock_conn
        mock_index_books.side_effect = Exception("Indexing failed")

        with pytest.raises(Exception, match="Indexing failed"):
            main()

        mock_conn.close.assert_called_once()
