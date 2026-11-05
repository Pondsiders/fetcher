"""Turn a URL into Markdown, one rung at a time.

1. Ask the server for Markdown. If it sends Markdown or plain text, done.
2. If it sends HTML, have Trafilatura pull the content out as Markdown.
3. Anything else, or an HTML page with nothing in it, fails loud.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx
import trafilatura

ACCEPT = "text/markdown, text/plain;q=0.9, text/html;q=0.8, */*;q=0.1"
USER_AGENT = "fetcher/0.1 (+https://bonnie.tail8bd569.ts.net/Tools/fetcher)"
MARKDOWN_TYPES = ("text/markdown", "text/x-markdown")
HTML_TYPES = ("text/html", "application/xhtml+xml")

Via = Literal["markdown", "plain", "trafilatura"]


@dataclass(frozen=True)
class Fetched:
    """A page as text an agent can read, and which rung produced it."""

    url: str
    via: Via
    text: str


class NotMarkdownError(Exception):
    """The server answered with an error, or a type we don't convert."""

    def __init__(self, url: str, status: int, content_type: str) -> None:
        """Record what came back instead."""
        self.url: str = url
        self.status: int = status
        self.content_type: str = content_type
        super().__init__(f"{url}: got {content_type or 'no content-type'} ({status})")


class NothingExtractedError(Exception):
    """The server sent HTML, but there was no content in it to extract."""

    def __init__(self, url: str) -> None:
        """Record which page came up empty."""
        self.url: str = url
        super().__init__(f"{url}: HTML with no extractable content (JS page?)")


def media_type(content_type: str) -> str:
    """Strip parameters: 'text/html; charset=utf-8' -> 'text/html'."""
    return content_type.split(";", 1)[0].strip().lower()


def extract(html: bytes, url: str) -> str | None:
    """Pull the main content out of an HTML page as Markdown."""
    return trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        with_metadata=True,
        include_comments=False,
        include_tables=True,
        include_links=True,
        include_formatting=True,
        favor_recall=True,
    )


def fetch(url: str, *, timeout: float = 20.0) -> Fetched:
    """Fetch a URL and return it as Markdown.

    Raises:
        NotMarkdownError: Error status, or a content type we don't convert.
        NothingExtractedError: HTML came back, but with no content in it.
        httpx.HTTPError: The request itself failed (DNS, TLS, timeout).
    """
    headers = {"Accept": ACCEPT, "User-Agent": USER_AGENT}
    with httpx.Client(
        follow_redirects=True, timeout=timeout, headers=headers
    ) as client:
        response = client.get(url)
    final_url = str(response.url)
    content_type = response.headers.get("content-type", "")
    kind = media_type(content_type)

    if response.is_error:
        raise NotMarkdownError(final_url, response.status_code, content_type)
    if kind in MARKDOWN_TYPES:
        return Fetched(final_url, "markdown", response.text)
    if kind == "text/plain":
        return Fetched(final_url, "plain", response.text)
    if kind in HTML_TYPES:
        text = extract(response.content, final_url)
        if not text or not text.strip():
            raise NothingExtractedError(final_url)
        return Fetched(final_url, "trafilatura", text)
    raise NotMarkdownError(final_url, response.status_code, content_type)
