"""Read-only GitHub fetching for PR and issue links.

Fetches title, description, comments and changed file names (with tiny truncated diff snippets).
Never fetches full code. Any failure returns None so the caller records a gap.
"""

import logging
import re
from dataclasses import dataclass, field

import httpx

log = logging.getLogger(__name__)

API = "https://api.github.com"
MAX_BODY = 4000
MAX_COMMENTS = 10
MAX_COMMENT_CHARS = 1000
MAX_FILES = 50
MAX_PATCH_FILES = 5
MAX_PATCH_CHARS = 400

_LINK_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)/(?P<kind>pull|issues)/(?P<num>\d+)"
)


@dataclass
class GitHubContent:
    url: str
    kind: str  # "pull" or "issue"
    title: str
    body: str
    comments: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    patches: dict[str, str] = field(default_factory=dict)


def _trunc(text: str | None, limit: int) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + " ...[truncated]"


def parse_link(url: str) -> tuple[str, str, str, int] | None:
    m = _LINK_RE.match(url.strip())
    if not m:
        return None
    return m["owner"], m["repo"], m["kind"], int(m["num"])


def fetch_github_content(url: str, token: str, client: httpx.Client | None = None) -> GitHubContent | None:
    """Return fetched content, or None if the link is unsupported or any request fails."""
    parsed = parse_link(url)
    if parsed is None:
        return None
    owner, repo, kind, num = parsed
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    own_client = client is None
    http = client or httpx.Client(timeout=10.0)
    base = f"{API}/repos/{owner}/{repo}"
    try:
        main_path = f"{base}/pulls/{num}" if kind == "pull" else f"{base}/issues/{num}"
        main = http.get(main_path, headers=headers)
        main.raise_for_status()
        data = main.json()
        comments_resp = http.get(
            f"{base}/issues/{num}/comments", params={"per_page": MAX_COMMENTS}, headers=headers
        )
        comments_resp.raise_for_status()
        comments = [
            _trunc(f"{c.get('user', {}).get('login', 'unknown')}: {c.get('body')}", MAX_COMMENT_CHARS)
            for c in comments_resp.json()[:MAX_COMMENTS]
        ]
        files: list[str] = []
        patches: dict[str, str] = {}
        if kind == "pull":
            files_resp = http.get(f"{base}/pulls/{num}/files", params={"per_page": MAX_FILES}, headers=headers)
            files_resp.raise_for_status()
            for i, f in enumerate(files_resp.json()[:MAX_FILES]):
                files.append(f["filename"])
                if i < MAX_PATCH_FILES and f.get("patch"):
                    patches[f["filename"]] = _trunc(f["patch"], MAX_PATCH_CHARS)
        return GitHubContent(
            url=url,
            kind="pull" if kind == "pull" else "issue",
            title=str(data.get("title", "")),
            body=_trunc(data.get("body"), MAX_BODY),
            comments=comments,
            files=files,
            patches=patches,
        )
    except Exception as exc:  # private, deleted, rate-limited, network, bad JSON
        log.warning("GitHub fetch failed for %s: %s", url, type(exc).__name__)
        return None
    finally:
        if own_client:
            http.close()
