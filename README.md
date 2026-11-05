# fetcher

Turn a URL into Markdown for an agent to read, or say loudly why not.

    fetcher URL

It climbs a short ladder:

1. Ask the server for Markdown (`Accept: text/markdown`). Markdown or plain text comes back as is.
2. If the server sends HTML, Trafilatura extracts the content as Markdown, with a metadata header (title, author, date).
3. Anything else fails loud: error statuses, PDFs, and HTML pages with nothing in them (usually JavaScript shells).

Text goes to stdout and exits 0. A page it can't convert exits 1, an unreachable URL exits 2, and the reason is on stderr either way. Stderr also says which rung the text came from.

`scripts/sieve.py` runs a pile of URLs through it and tallies what came back.
