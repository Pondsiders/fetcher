"""GitHub pages whose real content is a Markdown file: fetch the file instead.

A repo page is mostly chrome around its README, and a blob page is chrome
around a file. Both are available raw, so ask for that.
"""

from __future__ import annotations

from urllib.parse import quote, urlsplit

RAW = "https://raw.githubusercontent.com"
API = "https://api.github.com"
API_RAW = {"Accept": "application/vnd.github.raw"}

Candidate = tuple[str, dict[str, str]]


def candidates(url: str) -> list[Candidate]:
    """Raw URLs to try, in order, for a GitHub repo, tree or blob page.

    Returns an empty list for anything else (issues, PRs, profiles...).
    """
    parts = urlsplit(url)
    if parts.hostname not in ("github.com", "www.github.com"):
        return []
    segs = [s for s in parts.path.split("/") if s]
    if len(segs) < 2:
        return []
    owner, repo = segs[0], segs[1].removesuffix(".git")

    if len(segs) == 2:
        return [
            (f"{RAW}/{owner}/{repo}/HEAD/README.md", {}),
            (f"{API}/repos/{owner}/{repo}/readme", API_RAW),
        ]
    if segs[2] == "blob" and len(segs) >= 5:
        return [(f"{RAW}/{owner}/{repo}/{'/'.join(segs[3:])}", {})]
    if segs[2] == "tree" and len(segs) >= 4:
        ref, subdir = segs[3], "/".join(segs[4:])
        prefix = f"{subdir}/" if subdir else ""
        return [
            (f"{RAW}/{owner}/{repo}/{ref}/{prefix}README.md", {}),
            (f"{API}/repos/{owner}/{repo}/readme/{subdir}?ref={quote(ref)}", API_RAW),
        ]
    return []
