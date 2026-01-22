"""Tests for author_search module."""

from unittest.mock import MagicMock, patch

import httpx

from textalyzer.author_search import (
    extract_last_name,
    format_book_line,
    main,
    normalize_author_name,
    search_books_by_author,
)


class TestExtractLastName:
    """Tests for extract_last_name function."""

    def test_extract_simple_name(self) -> None:
        """extract_last_name should return last word of simple name."""
        assert extract_last_name("Jane Austen") == "Austen"

    def test_extract_name_with_initials(self) -> None:
        """extract_last_name should return last word for names with initials."""
        assert extract_last_name("P. G. Wodehouse") == "Wodehouse"

    def test_extract_name_with_middle_name(self) -> None:
        """extract_last_name should return last word for names with middle names."""
        assert extract_last_name("Arthur Conan Doyle") == "Doyle"

    def test_extract_single_name(self) -> None:
        """extract_last_name should return the name if only one word."""
        assert extract_last_name("Voltaire") == "Voltaire"

    def test_extract_name_with_multiple_initials(self) -> None:
        """extract_last_name should handle multiple initials."""
        assert extract_last_name("Dorothy L. Sayers") == "Sayers"


class TestNormalizeAuthorName:
    """Tests for normalize_author_name function."""

    def test_normalize_simple_name(self) -> None:
        """normalize_author_name should lowercase simple names."""
        result = normalize_author_name("Jane Austen")
        assert result == "jane austen"

    def test_normalize_last_first_format(self) -> None:
        """normalize_author_name should convert 'Last, First' format."""
        result = normalize_author_name("Austen, Jane")
        assert result == "jane austen"

    def test_normalize_handles_extra_spaces(self) -> None:
        """normalize_author_name should handle extra spaces."""
        result = normalize_author_name("Austen,  Jane ")
        assert result == "jane austen"

    def test_normalize_preserves_middle_names(self) -> None:
        """normalize_author_name should preserve middle names."""
        result = normalize_author_name("Doyle, Arthur Conan")
        assert result == "arthur conan doyle"

    def test_normalize_removes_periods_from_initials(self) -> None:
        """normalize_author_name should remove periods from initials."""
        result = normalize_author_name("E. M. Forster")
        assert result == "e m forster"

    def test_normalize_handles_initials_without_spaces(self) -> None:
        """normalize_author_name should handle initials without spaces."""
        result = normalize_author_name("Forster, E.M.")
        assert result == "e m forster"

    def test_normalize_initials_match_regardless_of_spacing(self) -> None:
        """normalize_author_name should normalize initials consistently."""
        spaced = normalize_author_name("E. M. Forster")
        unspaced = normalize_author_name("E.M. Forster")
        from_api = normalize_author_name("Forster, E.M.")
        assert spaced == unspaced == from_api

    def test_normalize_strips_parenthetical_suffix(self) -> None:
        """normalize_author_name should strip parenthetical suffixes."""
        result = normalize_author_name("Sayers, Dorothy L. (Dorothy Leigh)")
        assert result == "dorothy l sayers"

    def test_normalize_with_parenthetical_matches_without(self) -> None:
        """normalize_author_name should match with or without parenthetical."""
        with_parens = normalize_author_name("Sayers, Dorothy L. (Dorothy Leigh)")
        without_parens = normalize_author_name("Dorothy L. Sayers")
        assert with_parens == without_parens


class TestSearchBooksByAuthor:
    """Tests for search_books_by_author function."""

    @patch("textalyzer.author_search.httpx.get")
    def test_search_returns_matching_books(self, mock_get: MagicMock) -> None:
        """search_books_by_author should return books matching the author."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 2,
            "next": None,
            "results": [
                {
                    "id": 1342,
                    "title": "Pride and Prejudice",
                    "authors": [{"name": "Austen, Jane"}],
                },
                {
                    "id": 1400,
                    "title": "Great Expectations",
                    "authors": [{"name": "Dickens, Charles"}],
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = search_books_by_author("Jane Austen")

        assert len(result) == 1
        assert result[0]["id"] == 1342
        assert result[0]["title"] == "Pride and Prejudice"

    @patch("textalyzer.author_search.httpx.get")
    def test_search_handles_pagination(self, mock_get: MagicMock) -> None:
        """search_books_by_author should follow pagination links."""
        # First page
        response1 = MagicMock()
        response1.json.return_value = {
            "count": 2,
            "next": "https://gutendex.com/books?page=2",
            "results": [
                {
                    "id": 1342,
                    "title": "Pride and Prejudice",
                    "authors": [{"name": "Austen, Jane"}],
                },
            ],
        }
        response1.raise_for_status = MagicMock()

        # Second page
        response2 = MagicMock()
        response2.json.return_value = {
            "count": 2,
            "next": None,
            "results": [
                {
                    "id": 161,
                    "title": "Sense and Sensibility",
                    "authors": [{"name": "Austen, Jane"}],
                },
            ],
        }
        response2.raise_for_status = MagicMock()

        mock_get.side_effect = [response1, response2]

        result = search_books_by_author("Jane Austen")

        assert len(result) == 2
        assert mock_get.call_count == 2

    @patch("textalyzer.author_search.httpx.get")
    def test_search_handles_http_error(self, mock_get: MagicMock) -> None:
        """search_books_by_author should handle HTTP errors gracefully."""
        mock_get.side_effect = httpx.HTTPError("Connection failed")

        result = search_books_by_author("Jane Austen")

        assert result == []

    @patch("textalyzer.author_search.httpx.get")
    def test_search_returns_empty_for_no_matches(self, mock_get: MagicMock) -> None:
        """search_books_by_author should return empty list when no matches."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 0,
            "next": None,
            "results": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = search_books_by_author("Nonexistent Author")

        assert result == []

    @patch("textalyzer.author_search.httpx.get")
    def test_search_deduplicates_by_title_keeping_highest_id(
        self, mock_get: MagicMock
    ) -> None:
        """search_books_by_author should dedupe titles, keeping highest ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 3,
            "next": None,
            "results": [
                {
                    "id": 100,
                    "title": "Pride and Prejudice",
                    "authors": [{"name": "Austen, Jane"}],
                },
                {
                    "id": 500,
                    "title": "Pride and Prejudice",
                    "authors": [{"name": "Austen, Jane"}],
                },
                {
                    "id": 200,
                    "title": "Pride and Prejudice",
                    "authors": [{"name": "Austen, Jane"}],
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = search_books_by_author("Jane Austen")

        assert len(result) == 1
        assert result[0]["id"] == 500


class TestFormatBookLine:
    """Tests for format_book_line function."""

    def test_format_basic_book(self) -> None:
        """format_book_line should format book ID with title comment."""
        book = {"id": 1342, "title": "Pride and Prejudice", "authors": ["Austen"]}

        result = format_book_line(book)

        assert result == "1342  # Pride and Prejudice"

    def test_format_truncates_long_titles(self) -> None:
        """format_book_line should truncate titles longer than 50 chars."""
        long_title = "A" * 100
        book = {"id": 123, "title": long_title, "authors": ["Author"]}

        result = format_book_line(book)

        assert "A" * 50 in result
        assert "A" * 51 not in result
        assert result.startswith("123  # ")


class TestMain:
    """Tests for main function."""

    @patch("textalyzer.author_search.search_books_by_author")
    def test_main_prints_results(
        self,
        mock_search: MagicMock,
        capsys: MagicMock,
    ) -> None:
        """main should search for author and print results to stdout."""
        mock_search.return_value = [
            {"id": 1342, "title": "Pride and Prejudice", "authors": ["Austen"]},
            {"id": 161, "title": "Sense and Sensibility", "authors": ["Austen"]},
        ]

        with patch("sys.argv", ["prog", "Jane Austen"]):
            main()

        mock_search.assert_called_once_with("Jane Austen")
        captured = capsys.readouterr()
        assert "# Search: Jane Austen" in captured.out
        assert "1342  # Pride and Prejudice" in captured.out
        assert "161  # Sense and Sensibility" in captured.out

    @patch("textalyzer.author_search.search_books_by_author")
    def test_main_handles_no_results(
        self,
        mock_search: MagicMock,
        capsys: MagicMock,
    ) -> None:
        """main should print search comment even when no books are found."""
        mock_search.return_value = []

        with patch("sys.argv", ["prog", "Unknown Author"]):
            main()

        mock_search.assert_called_once_with("Unknown Author")
        captured = capsys.readouterr()
        assert captured.out == "# Search: Unknown Author\n"

    @patch("textalyzer.author_search.search_books_by_author")
    def test_main_debug_flag(
        self,
        mock_search: MagicMock,
    ) -> None:
        """main should enable debug logging with --debug flag."""
        import logging

        mock_search.return_value = []

        with patch("sys.argv", ["prog", "Jane Austen", "--debug"]):
            main()

        assert logging.getLogger().level == logging.DEBUG


class TestSearchBooksByAuthorMaxPages:
    """Tests for max pages safety limit."""

    @patch("textalyzer.author_search.httpx.get")
    def test_search_stops_at_max_pages(self, mock_get: MagicMock) -> None:
        """search_books_by_author should stop after max pages."""
        # Create a response that always has a next page
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 10000,
            "next": "https://gutendex.com/books/?page=2",
            "results": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = search_books_by_author("Test Author")

        # Should stop at 100 pages (safety limit)
        assert mock_get.call_count == 100
        assert result == []
