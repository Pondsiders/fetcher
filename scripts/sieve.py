"""Run a pile of URLs through fetcher and record which hole each one fell through.

Reads URLs on stdin, one per line. Writes TSV on stdout:
outcome, status, detail, words, url.
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

import httpx

from fetcher.fetch import NothingExtractedError, Saved, StatusError, fetch, media_type


def probe(url: str) -> tuple[str, str, str, str, str]:
    """Classify one URL."""
    try:
        page = fetch(url)
    except StatusError as e:
        return "error-status", str(e.status), media_type(e.content_type), "0", url
    except NothingExtractedError:
        return "empty", "200", "text/html", "0", url
    except httpx.HTTPError as e:
        return "unreachable", "-", type(e).__name__, "0", url
    if isinstance(page, Saved):
        return "saved", "200", page.content_type, str(page.size), url
    return page.via, "200", "", str(len(page.text.split())), url


def main() -> None:
    """Probe every URL on stdin, sixteen at a time."""
    urls = [line.strip() for line in sys.stdin if line.strip()]
    with ThreadPoolExecutor(max_workers=16) as pool:
        for row in pool.map(probe, urls):
            print("\t".join(row), flush=True)


if __name__ == "__main__":
    main()
