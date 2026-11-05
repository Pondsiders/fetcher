"""Turn a URL into something an agent can read, one rung at a time.

0. A GitHub repo, tree or blob page: fetch the raw file instead, if it exists.
1. Ask the server for Markdown. Markdown or any other text comes back as is.
2. HTML goes through Trafilatura, which pulls the content out as Markdown.
3. Anything else (PDFs, images, archives) is saved to a temp folder, and
   the caller gets the path.

Error statuses, and HTML pages with nothing in them, fail loud.
"""

from __future__ import annotations

import hashlib
import mimetypes
import tempfile
from dataclasses import dataclass
from email.message import Message
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import unquote, urlsplit

import httpx
import trafilatura

from fetcher.github import candidates as github_candidates

ACCEPT = "text/markdown, text/plain;q=0.9, text/html;q=0.8, */*;q=0.1"
USER_AGENT = "fetcher/0.1"
MARKDOWN_TYPES = ("text/markdown", "text/x-markdown")
HTML_TYPES = ("text/html", "application/xhtml+xml")
TEXT_APPLICATION_TYPES = ("application/json", "application/xml")
DOWNLOADS = Path(tempfile.gettempdir()) / "fetcher"

Via = Literal["github", "markdown", "plain", "trafilatura"]


@dataclass(frozen=True)
class Fetched:
    """A page as text an agent can read, and which rung produced it."""

    url: str
    via: Via
    text: str


@dataclass(frozen=True)
class Saved:
    """A non-text response, written to disk."""

    url: str
    content_type: str
    path: Path
    size: int


class StatusError(Exception):
    """The server answered with an error status."""

    def __init__(self, url: str, status: int, content_type: str) -> None:
        """Record what came back."""
        self.url: str = url
        self.status: int = status
        self.content_type: str = content_type
        super().__init__(f"{url}: HTTP {status} ({content_type or 'no content-type'})")


class NothingExtractedError(Exception):
    """The server sent HTML, but there was no content in it to extract."""

    def __init__(self, url: str) -> None:
        """Record which page came up empty."""
        self.url: str = url
        super().__init__(f"{url}: HTML with no extractable content (JS page?)")


def media_type(content_type: str) -> str:
    """Strip parameters: 'text/html; charset=utf-8' -> 'text/html'."""
    return content_type.split(";", 1)[0].strip().lower()


def is_text(kind: str) -> bool:
    """True for types an agent can read as they are: text/*, JSON, XML."""
    return (
        kind.startswith("text/")
        or kind in TEXT_APPLICATION_TYPES
        or kind.endswith(("+json", "+xml"))
    )


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


def filename(url: str, kind: str, disposition: str | None) -> str:
    """Pick a safe local name: the server's suggestion, else the URL's last part.

    Adds an extension matching the content type if the name lacks one.
    """
    name = None
    if disposition:
        msg = Message()
        msg["content-disposition"] = disposition
        name = msg.get_filename()
    if not name:
        name = PurePosixPath(unquote(urlsplit(url).path)).name
    name = PurePosixPath(name.replace("\\", "/")).name.lstrip(".")[:120] or "download"
    extensions = mimetypes.guess_all_extensions(kind)
    if extensions and not name.lower().endswith(tuple(extensions)):
        name += mimetypes.guess_extension(kind) or extensions[0]
    return name


def save(response: httpx.Response, url: str, kind: str) -> Saved:
    """Stream a response body to DOWNLOADS/<url hash>/<name>."""
    folder = DOWNLOADS / hashlib.sha256(url.encode()).hexdigest()[:12]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename(url, kind, response.headers.get("content-disposition"))
    with path.open("wb") as f:
        for chunk in response.iter_bytes():
            _ = f.write(chunk)
    return Saved(url, kind, path, path.stat().st_size)


def fetch(url: str, *, timeout: float = 20.0) -> Fetched | Saved:
    """Fetch a URL: text comes back as Markdown, anything else as a saved file.

    Raises:
        StatusError: The server answered with an error status.
        NothingExtractedError: HTML came back, but with no content in it.
        httpx.HTTPError: The request itself failed (DNS, TLS, timeout).
    """
    headers = {"Accept": ACCEPT, "User-Agent": USER_AGENT}
    with httpx.Client(
        follow_redirects=True, timeout=timeout, headers=headers
    ) as client:
        for raw_url, extra in github_candidates(url):
            raw = client.get(raw_url, headers=extra)
            if raw.is_success:
                return Fetched(raw_url, "github", raw.text)

        with client.stream("GET", url) as response:
            final_url = str(response.url)
            content_type = response.headers.get("content-type", "")
            kind = media_type(content_type)
            if response.is_error:
                raise StatusError(final_url, response.status_code, content_type)
            if kind not in HTML_TYPES and not is_text(kind):
                return save(response, final_url, kind)
            _ = response.read()

    if kind in MARKDOWN_TYPES:
        return Fetched(final_url, "markdown", response.text)
    if kind in HTML_TYPES:
        text = extract(response.content, final_url)
        if not text or not text.strip():
            raise NothingExtractedError(final_url)
        return Fetched(final_url, "trafilatura", text)
    return Fetched(final_url, "plain", response.text)
