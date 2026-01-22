"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_book_ids_content() -> str:
    """Sample book IDs file content (tab-separated CSV)."""
    return """# Comment line
12345\tBook One\tFiction\tSummary one
67890\tBook Two\tNon-fiction\tSummary two
# Another comment
11111\tBook Three\tMystery\tSummary three
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
    """Sample Project Gutenberg text with markers and multiple paragraphs."""
    return """The Project Gutenberg eBook of Test Book

*** START OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***

This is the first paragraph of the book.
It has multiple lines within the same paragraph.

This is the second paragraph.
It also spans multiple lines.

A third paragraph here with some more content
that continues on another line.

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
