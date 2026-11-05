# fetcher

Turn a URL into Markdown for an agent to read, or say loudly why not.

    fetcher URL

Step one so far: it asks the server for Markdown (`Accept: text/markdown`). Markdown or plain text goes to stdout, exit 0. Anything else exits 1, and an unreachable URL exits 2, with the reason on stderr.

`scripts/sieve.py` runs a pile of URLs through it and tallies what came back.
