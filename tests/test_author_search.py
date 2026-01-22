"""Tests for author_search module."""

from unittest.mock import MagicMock, patch

import httpx

from textalyzer.author_search import (
    author_matches,
    format_book_line,
    main,
    normalize_author_name,
    search_books_by_author,
)


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


class TestAuthorMatches:
    """Tests for author_matches function."""

    def test_exact_match(self) -> None:
        """author_matches should match identical names."""
        assert author_matches("Jane Austen", "Austen, Jane")

    def test_match_with_parenthetical(self) -> None:
        """author_matches should match when API has extra info in parentheses."""
        assert author_matches(
            "Dorothy L. Sayers", "Sayers, Dorothy L. (Dorothy Leigh)"
        )

    def test_no_match_different_author(self) -> None:
        """author_matches should not match different authors."""
        assert not author_matches("Jane Austen", "Dickens, Charles")

    def test_partial_name_no_match(self) -> None:
        """author_matches should not match if search has words not in API name."""
        assert not author_matches("Dorothy L. Sayers", "Sayers, W. C. Berwick")


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


class TestFormatBookLine:
    """Tests for format_book_line function."""

    def test_format_basic_book(self) -> None:
        """format_book_line should format book as tab-separated fields."""
        book = {
            "id": 1342,
            "title": "Pride and Prejudice",
            "authors": ["Austen"],
            "subjects": ["Romance", "Fiction"],
            "summaries": ["A classic novel about love and society."],
        }

        result = format_book_line(book)

        parts = result.split("\t")
        assert parts[0] == "1342"
        assert parts[1] == "Pride and Prejudice"
        assert parts[2] == "Romance"
        assert parts[3] == "A classic novel about love and society."

    def test_format_handles_empty_subjects(self) -> None:
        """format_book_line should handle empty subjects list."""
        book = {
            "id": 123,
            "title": "Test Book",
            "authors": ["Author"],
            "subjects": [],
            "summaries": ["A summary."],
        }

        result = format_book_line(book)

        parts = result.split("\t")
        assert parts[2] == ""

    def test_format_handles_empty_summaries(self) -> None:
        """format_book_line should handle empty summaries list."""
        book = {
            "id": 123,
            "title": "Test Book",
            "authors": ["Author"],
            "subjects": ["Fiction"],
            "summaries": [],
        }

        result = format_book_line(book)

        parts = result.split("\t")
        assert parts[3] == ""

    def test_format_handles_missing_fields(self) -> None:
        """format_book_line should handle missing subjects and summaries."""
        book = {"id": 123, "title": "Test Book", "authors": ["Author"]}

        result = format_book_line(book)

        parts = result.split("\t")
        assert parts[0] == "123"
        assert parts[1] == "Test Book"
        assert parts[2] == ""
        assert parts[3] == ""


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
            {
                "id": 1342,
                "title": "Pride and Prejudice",
                "authors": ["Austen"],
                "subjects": ["Romance"],
                "summaries": ["A classic."],
            },
            {
                "id": 161,
                "title": "Sense and Sensibility",
                "authors": ["Austen"],
                "subjects": ["Fiction"],
                "summaries": ["Another classic."],
            },
        ]

        with patch("sys.argv", ["prog", "Jane Austen"]):
            main()

        mock_search.assert_called_once_with("Jane Austen")
        captured = capsys.readouterr()
        assert "1342\tPride and Prejudice\tRomance\tA classic." in captured.out
        assert "161\tSense and Sensibility\tFiction\tAnother classic." in captured.out

    @patch("textalyzer.author_search.search_books_by_author")
    def test_main_handles_no_results(
        self,
        mock_search: MagicMock,
        capsys: MagicMock,
    ) -> None:
        """main should print nothing when no books are found."""
        mock_search.return_value = []

        with patch("sys.argv", ["prog", "Unknown Author"]):
            main()

        mock_search.assert_called_once_with("Unknown Author")
        captured = capsys.readouterr()
        assert captured.out == ""

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
