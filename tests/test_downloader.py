"""Tests for downloader module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from textalyzer.downloader import (
    download_metadata,
    download_text,
    extract_meta_tags,
    load_book_ids,
    main,
)


class TestLoadBookIds:
    """Tests for load_book_ids function."""

    def test_load_book_ids_returns_list(
        self, tmp_path: Path, sample_book_ids_content: str
    ) -> None:
        """load_book_ids should return a list of IDs."""
        book_ids_file = tmp_path / "book-ids.dat"
        book_ids_file.write_text(sample_book_ids_content)

        result = load_book_ids(book_ids_file)

        assert isinstance(result, list)
        assert result == ["12345", "67890", "11111"]

    def test_load_book_ids_skips_comments(self, tmp_path: Path) -> None:
        """load_book_ids should skip comment lines."""
        book_ids_file = tmp_path / "book-ids.dat"
        book_ids_file.write_text("# This is a comment\n12345\n# Another\n")

        result = load_book_ids(book_ids_file)

        assert result == ["12345"]

    def test_load_book_ids_skips_empty_lines(self, tmp_path: Path) -> None:
        """load_book_ids should skip empty lines."""
        book_ids_file = tmp_path / "book-ids.dat"
        book_ids_file.write_text("12345\n\n\n67890\n")

        result = load_book_ids(book_ids_file)

        assert result == ["12345", "67890"]

    def test_load_book_ids_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """load_book_ids should return empty list for missing file."""
        missing_file = tmp_path / "nonexistent.dat"

        result = load_book_ids(missing_file)

        assert result == []

    def test_load_book_ids_strips_whitespace(self, tmp_path: Path) -> None:
        """load_book_ids should strip whitespace from IDs."""
        book_ids_file = tmp_path / "book-ids.dat"
        book_ids_file.write_text("  12345  \n  67890\n")

        result = load_book_ids(book_ids_file)

        assert result == ["12345", "67890"]


class TestExtractMetaTags:
    """Tests for extract_meta_tags function."""

    def test_extract_meta_tags_returns_list(self, sample_html_with_meta: str) -> None:
        """extract_meta_tags should return a list of dicts."""
        result = extract_meta_tags(sample_html_with_meta)

        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_extract_meta_tags_finds_name_content(
        self, sample_html_with_meta: str
    ) -> None:
        """extract_meta_tags should find meta tags with name and content."""
        result = extract_meta_tags(sample_html_with_meta)

        title_tag = next((tag for tag in result if tag.get("name") == "title"), None)
        assert title_tag is not None
        assert title_tag["content"] == "Pride and Prejudice by Jane Austen"

    def test_extract_meta_tags_finds_charset(self, sample_html_with_meta: str) -> None:
        """extract_meta_tags should find meta tags with charset."""
        result = extract_meta_tags(sample_html_with_meta)

        charset_tag = next((tag for tag in result if "charset" in tag), None)
        assert charset_tag is not None
        assert charset_tag["charset"] == "utf-8"

    def test_extract_meta_tags_empty_html(self) -> None:
        """extract_meta_tags should return empty list for HTML without meta."""
        result = extract_meta_tags("<html><head></head><body></body></html>")

        assert result == []


class TestDownloadText:
    """Tests for download_text function."""

    def test_download_text_skips_existing_file(self, tmp_path: Path) -> None:
        """download_text should skip if file already exists."""
        existing_file = tmp_path / "pg12345.txt"
        existing_file.write_text("existing content")

        result = download_text("12345", tmp_path)

        assert result is False

    @patch("textalyzer.downloader.httpx.get")
    def test_download_text_success(self, mock_get: MagicMock, tmp_path: Path) -> None:
        """download_text should download and save file on success."""
        mock_response = MagicMock()
        mock_response.content = b"Book content here"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = download_text("12345", tmp_path)

        assert result is True
        assert (tmp_path / "pg12345.txt").exists()
        assert (tmp_path / "pg12345.txt").read_bytes() == b"Book content here"
        mock_get.assert_called_once()

    @patch("textalyzer.downloader.httpx.get")
    def test_download_text_http_error(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        """download_text should return False on HTTP error."""
        mock_get.side_effect = httpx.HTTPError("Connection failed")

        result = download_text("12345", tmp_path)

        assert result is False
        assert not (tmp_path / "pg12345.txt").exists()

    @patch("textalyzer.downloader.httpx.get")
    def test_download_text_uses_correct_url(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        """download_text should use correct URL template."""
        mock_response = MagicMock()
        mock_response.content = b"content"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        download_text("99999", tmp_path)

        call_args = mock_get.call_args
        assert "99999" in call_args[0][0]
        assert "gutenberg.org" in call_args[0][0]


class TestDownloadMetadata:
    """Tests for download_metadata function."""

    def test_download_metadata_skips_existing_file(self, tmp_path: Path) -> None:
        """download_metadata should skip if file already exists."""
        existing_file = tmp_path / "12345-meta.json"
        existing_file.write_text("{}")

        result = download_metadata("12345", tmp_path)

        assert result is False

    @patch("textalyzer.downloader.httpx.get")
    def test_download_metadata_success(
        self, mock_get: MagicMock, tmp_path: Path, sample_html_with_meta: str
    ) -> None:
        """download_metadata should download and save metadata on success."""
        mock_response = MagicMock()
        mock_response.text = sample_html_with_meta
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = download_metadata("12345", tmp_path)

        assert result is True
        meta_file = tmp_path / "12345-meta.json"
        assert meta_file.exists()

        saved_data = json.loads(meta_file.read_text())
        assert isinstance(saved_data, list)

    @patch("textalyzer.downloader.httpx.get")
    def test_download_metadata_http_error(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        """download_metadata should return False on HTTP error."""
        mock_get.side_effect = httpx.HTTPError("Connection failed")

        result = download_metadata("12345", tmp_path)

        assert result is False
        assert not (tmp_path / "12345-meta.json").exists()


class TestMain:
    """Tests for main function."""

    @patch("textalyzer.downloader.download_metadata")
    @patch("textalyzer.downloader.download_text")
    @patch("textalyzer.downloader.load_book_ids")
    @patch("textalyzer.downloader.DEFAULT_STORE_PATH", new_callable=lambda: Path)
    @patch("textalyzer.downloader.DEFAULT_BOOK_IDS_PATH", new_callable=lambda: Path)
    def test_main_with_no_book_ids(
        self,
        mock_book_ids_path: MagicMock,
        mock_store_path: MagicMock,
        mock_load_ids: MagicMock,
        mock_download_text: MagicMock,
        mock_download_meta: MagicMock,
        tmp_path: Path,
    ) -> None:
        """main should exit early when no book IDs found."""
        mock_load_ids.return_value = []

        main()

        mock_download_text.assert_not_called()
        mock_download_meta.assert_not_called()

    @patch("textalyzer.downloader.download_metadata")
    @patch("textalyzer.downloader.download_text")
    @patch("textalyzer.downloader.load_book_ids")
    @patch("textalyzer.downloader.DEFAULT_STORE_PATH")
    def test_main_processes_all_book_ids(
        self,
        mock_store_path: MagicMock,
        mock_load_ids: MagicMock,
        mock_download_text: MagicMock,
        mock_download_meta: MagicMock,
        tmp_path: Path,
    ) -> None:
        """main should process all book IDs."""
        mock_load_ids.return_value = ["111", "222", "333"]
        mock_store_path.mkdir = MagicMock()

        main()

        assert mock_download_text.call_count == 3
        assert mock_download_meta.call_count == 3
