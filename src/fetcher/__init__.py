"""Turn a URL into something an agent can read, or say loudly why not."""

from __future__ import annotations

from fetcher.fetch import Fetched, NothingExtractedError, Saved, StatusError, fetch

__all__ = ["Fetched", "NothingExtractedError", "Saved", "StatusError", "fetch"]
