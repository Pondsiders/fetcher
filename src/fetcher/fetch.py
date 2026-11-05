"""Step one: ask the server for Markdown, and refuse anything else."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

ACCEPT = "text/markdown, text/plain;q=0.9, */*;q=0.1"
USER_AGENT = "fetcher/0.1 (+https://bonnie.tail8bd569.ts.net/Tools/fetcher)"
TEXT_TYPES = ("text/markdown", "text/x-markdown", "text/plain")


@dataclass(frozen=True)
class Fetched:
    """A page that arrived as text an agent can read as-is."""

    url: str
    content_type: str
    text: str
    markdown_tokens: str | None


class NotMarkdownError(Exception):
    """The server answered, but not with Markdown or plain text."""

    def __init__(self, url: str, status: int, content_type: str) -> None:
        """Record what came back instead."""
        self.url: str = url
        self.status: int = status
        self.content_type: str = content_type
        super().__init__(f"{url}: got {content_type or 'no content-type'} ({status})")


def media_type(content_type: str) -> str:
    """Strip parameters: 'text/html; charset=utf-8' -> 'text/html'."""
    return content_type.split(";", 1)[0].strip().lower()


def fetch(url: str, *, timeout: float = 20.0) -> Fetched:
    """Ask for Markdown and return it.

    Raises:
        NotMarkdownError: The server sent something else, or an error status.
        httpx.HTTPError: The request itself failed (DNS, TLS, timeout).
    """
    headers = {"Accept": ACCEPT, "User-Agent": USER_AGENT}
    with httpx.Client(
        follow_redirects=True, timeout=timeout, headers=headers
    ) as client:
        response = client.get(url)
    content_type = response.headers.get("content-type", "")
    if response.is_error or media_type(content_type) not in TEXT_TYPES:
        raise NotMarkdownError(str(response.url), response.status_code, content_type)
    return Fetched(
        url=str(response.url),
        content_type=media_type(content_type),
        text=response.text,
        markdown_tokens=response.headers.get("x-markdown-tokens"),
    )
