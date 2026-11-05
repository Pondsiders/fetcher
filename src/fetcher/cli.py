"""Command line: `fetcher URL` prints Markdown, or the path of a saved file."""

from __future__ import annotations

import sys

import httpx

from fetcher.fetch import NothingExtractedError, Saved, StatusError, fetch


def human(size: int) -> str:
    """1536 -> '1.5 KB'."""
    value = float(size)
    for unit in ("bytes", "KB", "MB"):
        if value < 1024 or unit == "MB":
            return f"{value:.0f} {unit}" if unit == "bytes" else f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError  # unreachable


def main() -> int:
    """Fetch one URL. Exit 0 on success, 1 if the server said no, 2 if unreachable."""
    if len(sys.argv) != 2:
        print("usage: fetcher URL", file=sys.stderr)
        return 2
    try:
        result = fetch(sys.argv[1])
    except (StatusError, NothingExtractedError) as e:
        print(f"fetcher: {e}", file=sys.stderr)
        return 1
    except httpx.HTTPError as e:
        print(f"fetcher: couldn't reach it: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if isinstance(result, Saved):
        kind = result.content_type or "unknown type"
        size = human(result.size)
        print(f"fetcher: saved {kind}, {size}, from {result.url}", file=sys.stderr)
        print(result.path)
        return 0
    print(f"fetcher: via {result.via} from {result.url}", file=sys.stderr)
    text = result.text
    _ = sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
