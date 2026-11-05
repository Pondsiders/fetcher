# fetcher

Turn a URL into something an AI agent can read, or say loudly why not.

    fetcher URL

Text comes back on stdout as Markdown. Anything else (a PDF, an image, a zip) is saved to a temp folder and fetcher prints its path, so the agent can open the file with whatever tool suits it. A line on stderr always says what happened.

## The ladder

0. **GitHub repo, folder or file pages** fetch the raw README or file instead of the page around it. It tries `raw.githubusercontent.com` first, then the GitHub API, which allows 60 unauthenticated calls an hour. Issues, PRs and anything else on GitHub take the normal path.
1. **Ask for Markdown.** The request sends `Accept: text/markdown`, and some sites (Cloudflare's "Markdown for Agents," many docs sites, Hugging Face papers) answer with Markdown. That, and any other text (plain, JSON, XML), comes back as is.
2. **HTML** goes through [Trafilatura](https://trafilatura.readthedocs.io/), which pulls out the main content as Markdown with a short metadata header (title, author, date).
3. **Everything else** is saved to `$TMPDIR/fetcher/<hash>/<name>`, using the server's suggested filename or the URL's, with an extension that matches the content type. To keep a file, copy it somewhere.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Text on stdout, or a saved file's path on stdout |
| 1 | The server said no: an error status, or an HTML page with no content in it (usually one built by JavaScript) |
| 2 | Couldn't reach it: DNS, TLS, timeout |

## What it won't do

It doesn't run JavaScript, log in, or get past bot walls. A page that needs a real browser fails with exit 1 and says so.

## Install

    uv tool install git+https://github.com/Pondsiders/fetcher

`scripts/sieve.py` runs a pile of URLs through fetcher and tallies what came back, one TSV row per URL.
