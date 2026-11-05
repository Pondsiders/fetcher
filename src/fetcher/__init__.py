"""Turn a URL into Markdown for an agent to read, or say loudly why not."""

from __future__ import annotations

from fetcher.fetch import Fetched, NotMarkdownError, fetch

__all__ = ["Fetched", "NotMarkdownError", "fetch"]
