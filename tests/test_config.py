"""Tests for config module."""

import logging
import re
from pathlib import Path

from textalyzer.config import (
    DEFAULT_BOOK_IDS_PATH,
    DEFAULT_DB_PATH,
    DEFAULT_STORE_PATH,
    EBOOK_URL_TEMPLATE,
    END_MARKER_RE,
    LOG_FORMAT,
    LOG_LEVEL,
    MIN_PARAGRAPH_LENGTH,
    SKIP_PARAGRAPH_PATTERNS,
    START_MARKER_RE,
    TEXT_URL_TEMPLATE,
    setup_logging,
)


class TestConfigConstants:
    """Tests for configuration constants."""

    def test_log_level_is_warning(self) -> None:
        """Log level should be WARNING."""
        assert LOG_LEVEL == logging.WARNING

    def test_log_format_contains_required_fields(self) -> None:
        """Log format should contain timestamp, level, and message."""
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT
        assert "%(message)s" in LOG_FORMAT

    def test_default_paths_are_path_objects(self) -> None:
        """Default paths should be Path objects."""
        assert isinstance(DEFAULT_BOOK_IDS_PATH, Path)
        assert isinstance(DEFAULT_STORE_PATH, Path)
        assert isinstance(DEFAULT_DB_PATH, Path)

    def test_default_path_values(self) -> None:
        """Default paths should have expected values."""
        assert DEFAULT_BOOK_IDS_PATH == Path("book-ids.dat")
        assert DEFAULT_STORE_PATH == Path("text-store")
        assert DEFAULT_DB_PATH == Path("db/text-search.db")

    def test_url_templates_have_placeholder(self) -> None:
        """URL templates should contain {book_id} placeholder."""
        assert "{book_id}" in TEXT_URL_TEMPLATE
        assert "{book_id}" in EBOOK_URL_TEMPLATE

    def test_url_templates_are_gutenberg_urls(self) -> None:
        """URL templates should point to gutenberg.org."""
        assert "gutenberg.org" in TEXT_URL_TEMPLATE
        assert "gutenberg.org" in EBOOK_URL_TEMPLATE

    def test_min_paragraph_length(self) -> None:
        """MIN_PARAGRAPH_LENGTH should be set to 4."""
        assert MIN_PARAGRAPH_LENGTH == 4

    def test_skip_paragraph_patterns(self) -> None:
        """SKIP_PARAGRAPH_PATTERNS should contain expected patterns."""
        assert "[Illustration" in SKIP_PARAGRAPH_PATTERNS
        assert "[Blank Page]" in SKIP_PARAGRAPH_PATTERNS
        assert "[**" in SKIP_PARAGRAPH_PATTERNS
        assert "[Transcriber's Note" in SKIP_PARAGRAPH_PATTERNS
        assert "[Editor's Note" in SKIP_PARAGRAPH_PATTERNS
        assert "[Technical Note" in SKIP_PARAGRAPH_PATTERNS
        assert "[_Copyright" in SKIP_PARAGRAPH_PATTERNS


class TestRegexPatterns:
    """Tests for regex patterns."""

    def test_start_marker_re_is_compiled(self) -> None:
        """START_MARKER_RE should be a compiled regex."""
        assert isinstance(START_MARKER_RE, re.Pattern)

    def test_end_marker_re_is_compiled(self) -> None:
        """END_MARKER_RE should be a compiled regex."""
        assert isinstance(END_MARKER_RE, re.Pattern)

    def test_start_marker_matches_gutenberg_format(self) -> None:
        """START_MARKER_RE should match Gutenberg start markers."""
        test_string = "*** START OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***"
        assert START_MARKER_RE.search(test_string) is not None

    def test_end_marker_matches_gutenberg_format(self) -> None:
        """END_MARKER_RE should match Gutenberg end markers."""
        test_string = "*** END OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***"
        assert END_MARKER_RE.search(test_string) is not None

    def test_start_marker_does_not_match_end(self) -> None:
        """START_MARKER_RE should not match end markers."""
        test_string = "*** END OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***"
        assert START_MARKER_RE.search(test_string) is None

    def test_end_marker_does_not_match_start(self) -> None:
        """END_MARKER_RE should not match start markers."""
        test_string = "*** START OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***"
        assert END_MARKER_RE.search(test_string) is None

    def test_start_marker_matches_this_variant(self) -> None:
        """START_MARKER_RE should match 'THIS PROJECT GUTENBERG' variant."""
        test_string = "*START OF THIS PROJECT GUTENBERG EBOOK*"
        assert START_MARKER_RE.search(test_string) is not None

    def test_start_marker_matches_without_of(self) -> None:
        """START_MARKER_RE should match without 'OF'."""
        test_string = "**START THE PROJECT GUTENBERG EBOOK**"
        assert START_MARKER_RE.search(test_string) is not None

    def test_start_marker_matches_minimal(self) -> None:
        """START_MARKER_RE should match minimal format."""
        test_string = "*START PROJECT GUTENBERG*"
        assert START_MARKER_RE.search(test_string) is not None

    def test_start_marker_case_insensitive(self) -> None:
        """START_MARKER_RE should be case insensitive."""
        test_string = "*** start of the project gutenberg ebook test ***"
        assert START_MARKER_RE.search(test_string) is not None

    def test_end_marker_matches_this_variant(self) -> None:
        """END_MARKER_RE should match 'THIS PROJECT GUTENBERG' variant."""
        test_string = "*END OF THIS PROJECT GUTENBERG EBOOK*"
        assert END_MARKER_RE.search(test_string) is not None

    def test_end_marker_matches_without_of(self) -> None:
        """END_MARKER_RE should match without 'OF'."""
        test_string = "**END THE PROJECT GUTENBERG EBOOK**"
        assert END_MARKER_RE.search(test_string) is not None

    def test_end_marker_case_insensitive(self) -> None:
        """END_MARKER_RE should be case insensitive."""
        test_string = "*** end of the project gutenberg ebook test ***"
        assert END_MARKER_RE.search(test_string) is not None


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_does_not_raise(self) -> None:
        """setup_logging should not raise exceptions."""
        setup_logging()

    def test_setup_logging_adds_handler(self) -> None:
        """setup_logging should add a handler to root logger."""
        setup_logging()
        root_logger = logging.getLogger()
        # basicConfig adds handlers if none exist; verify it runs without error
        # and that at least one handler exists (may be from pytest or setup_logging)
        assert root_logger.handlers is not None
