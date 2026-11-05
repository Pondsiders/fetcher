"""Command line: `fetcher URL` prints Markdown or exits loud."""

from __future__ import annotations

import sys

import httpx

from fetcher.fetch import NotMarkdownError, fetch


def main() -> int:
    """Fetch one URL. Exit 0 with text, 1 if not Markdown, 2 if unreachable."""
    if len(sys.argv) != 2:
        print("usage: fetcher URL", file=sys.stderr)
        return 2
    try:
        page = fetch(sys.argv[1])
    except NotMarkdownError as e:
        print(f"fetcher: no Markdown here. {e}", file=sys.stderr)
        return 1
    except httpx.HTTPError as e:
        print(f"fetcher: couldn't reach it: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(f"fetcher: {page.content_type} from {page.url}", file=sys.stderr)
    _ = sys.stdout.write(page.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
