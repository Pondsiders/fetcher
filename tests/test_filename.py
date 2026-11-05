from __future__ import annotations

import pytest

from fetcher.fetch import filename


@pytest.mark.parametrize(
    ("url", "kind", "disposition", "expected"),
    [
        ("https://x.org/a/paper.pdf", "application/pdf", None, "paper.pdf"),
        ("https://arxiv.org/pdf/2502.11748", "application/pdf", None, "2502.11748.pdf"),
        ("https://x.org/photo.jpeg", "image/jpeg", None, "photo.jpeg"),
        (
            "https://x.org/dl?id=7",
            "application/pdf",
            'attachment; filename="r.pdf"',
            "r.pdf",
        ),
        (
            "https://x.org/dl",
            "application/pdf",
            "attachment; filename*=UTF-8''caf%C3%A9.pdf",
            "café.pdf",
        ),
        ("https://x.org/", "application/pdf", None, "download.pdf"),
        ("https://x.org/my%20file.pdf", "application/pdf", None, "my file.pdf"),
    ],
)
def test_filename(url: str, kind: str, disposition: str | None, expected: str) -> None:
    assert filename(url, kind, disposition) == expected


@pytest.mark.parametrize(
    "disposition",
    [
        'attachment; filename="../../etc/passwd"',
        'attachment; filename="/etc/passwd"',
        'attachment; filename="..\\..\\passwd"',
    ],
)
def test_server_cannot_escape_the_folder(disposition: str) -> None:
    name = filename("https://x.org/dl", "text/plain", disposition)
    assert "/" not in name
    assert "\\" not in name
    assert not name.startswith(".")
