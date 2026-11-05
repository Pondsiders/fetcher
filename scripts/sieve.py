"""Run a pile of URLs through fetcher and record which hole each one fell through.

Reads URLs on stdin, one per line. Writes TSV on stdout:
outcome, status, media type, url.
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

import httpx

from fetcher.fetch import NotMarkdownError, fetch, media_type


def probe(url: str) -> tuple[str, str, str, str]:
    """Classify one URL."""
    try:
        page = fetch(url)
    except NotMarkdownError as e:
        outcome = "error-status" if e.status >= 400 else "refused"
        return outcome, str(e.status), media_type(e.content_type), url
    except httpx.HTTPError as e:
        return "unreachable", "-", type(e).__name__, url
    kind = "markdown" if page.content_type != "text/plain" else "plain"
    return kind, "200", page.content_type, url


def main() -> None:
    """Probe every URL on stdin, sixteen at a time."""
    urls = [line.strip() for line in sys.stdin if line.strip()]
    with ThreadPoolExecutor(max_workers=16) as pool:
        for row in pool.map(probe, urls):
            print("\t".join(row), flush=True)


if __name__ == "__main__":
    main()
