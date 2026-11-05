from __future__ import annotations

import pytest

from fetcher.github import API, API_RAW, RAW, candidates

REPO_README: list[tuple[str, dict[str, str]]] = [
    (f"{RAW}/owner/repo/HEAD/README.md", {}),
    (f"{API}/repos/owner/repo/readme", API_RAW),
]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner/repo",
        "https://github.com/owner/repo/",
        "https://github.com/owner/repo.git",
        "https://www.github.com/owner/repo",
    ],
)
def test_repo_page_tries_raw_readme_then_api(url: str) -> None:
    assert candidates(url) == REPO_README


def test_blob_keeps_the_whole_path() -> None:
    url = "https://github.com/owner/repo/blob/main/docs/guide/setup.md"
    assert candidates(url) == [(f"{RAW}/owner/repo/main/docs/guide/setup.md", {})]


def test_tree_with_subfolder_keeps_folder_and_ref() -> None:
    assert candidates("https://github.com/owner/repo/tree/dev/docs") == [
        (f"{RAW}/owner/repo/dev/docs/README.md", {}),
        (f"{API}/repos/owner/repo/readme/docs?ref=dev", API_RAW),
    ]


def test_tree_root_has_no_double_slash() -> None:
    raw_url, _ = candidates("https://github.com/owner/repo/tree/main")[0]
    assert raw_url == f"{RAW}/owner/repo/main/README.md"


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner/repo/issues/42",
        "https://github.com/owner/repo/pull/7",
        "https://github.com/jefferyharrell",
        "https://github.com/",
        "https://gist.github.com/owner/abc123",
        "https://raw.githubusercontent.com/owner/repo/main/README.md",
        "https://example.com/owner/repo",
    ],
)
def test_everything_else_takes_the_normal_path(url: str) -> None:
    assert candidates(url) == []
