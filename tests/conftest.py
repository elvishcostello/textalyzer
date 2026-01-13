"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_book_ids_content() -> str:
    """Sample book IDs file content."""
    return """# Comment line
12345
67890
# Another comment
11111
"""


@pytest.fixture
def sample_html_with_meta() -> str:
    """Sample HTML with meta tags."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="title" content="Pride and Prejudice by Jane Austen">
        <meta name="author" content="Jane Austen">
        <meta charset="utf-8">
    </head>
    <body></body>
    </html>
    """


@pytest.fixture
def sample_gutenberg_text() -> str:
    """Sample Project Gutenberg text with markers."""
    return """The Project Gutenberg eBook of Test Book

*** START OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***

This is the actual content of the book.
It has multiple lines.
And some more text here.

*** END OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***

End of the Project Gutenberg eBook
"""


@pytest.fixture
def sample_metadata_json() -> str:
    """Sample metadata JSON content."""
    return """[
    {"name": "title", "content": "Pride and Prejudice by Jane Austen"},
    {"name": "author", "content": "Jane Austen"},
    {"charset": "utf-8"}
]"""
