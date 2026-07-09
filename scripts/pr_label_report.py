#!/usr/bin/env python3
"""Pull every PR carrying any of a set of labels across an entire GitHub
org (or user account) and render an HTML report.

Designed for large result sets (~5k+ matching PRs):
  * Uses the GitHub GraphQL API, so each request returns 100 PRs *with* their
    state (OPEN / CLOSED / MERGED) included -- no per-PR follow-up calls.
  * Runs one search per label, and fetches labels concurrently.
  * GitHub search is hard-capped at 1,000 results per query, so any query
    that exceeds the cap is automatically bisected by creation-date range.
  * Retries with backoff on rate limits and transient 5xx errors.

Auth: pass --token, or set GITHUB_TOKEN / GH_TOKEN, or be logged in to the
`gh` CLI (the script falls back to `gh auth token`).

Usage:
  python scripts/pr_label_report.py --org mycompany \
      --labels tagA tagB tagC \
      --output pr_report.html --json-out pr_report.json

--org accepts a bare login or a URL like github.com/mycompany, and works
for both organizations and personal accounts (detected automatically).
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

API_URL = "https://api.github.com/graphql"
SEARCH_CAP = 1000  # GitHub search never returns more than 1,000 results per query
PAGE_SIZE = 100

SEARCH_GQL = """
query($q: String!, $cursor: String) {
  search(query: $q, type: ISSUE, first: %d, after: $cursor) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number
        title
        url
        state
        isDraft
        createdAt
        closedAt
        mergedAt
        author { login }
        repository { nameWithOwner }
        labels(first: 30) { nodes { name } }
      }
    }
  }
}
""" % PAGE_SIZE

OWNER_GQL = """
query($login: String!) {
  repositoryOwner(login: $login) {
    __typename
    ... on User { createdAt }
    ... on Organization { createdAt }
  }
}
"""


def ssl_context() -> ssl.SSLContext:
    """Some Python installs (notably python.org macOS builds) lack a linked CA
    bundle; fall back to certifi's when the system store can't verify."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class GitHubGraphQL:
    def __init__(self, token: str):
        self.ctx = ssl_context()
        self.headers = {
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "pr-label-report",
        }

    def run(self, query: str, variables: dict) -> dict:
        body = json.dumps({"query": query, "variables": variables}).encode()
        delay = 2.0
        for attempt in range(6):
            try:
                req = urllib.request.Request(API_URL, data=body, headers=self.headers)
                with urllib.request.urlopen(req, timeout=60, context=self.ctx) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError as e:
                # 403/429 = rate limiting (primary or secondary), 5xx = transient
                if e.code in (403, 429, 502, 503, 504) and attempt < 5:
                    wait = float(e.headers.get("Retry-After") or delay)
                    print(f"  http {e.code}, retrying in {wait:.0f}s...", file=sys.stderr)
                    time.sleep(wait)
                    delay *= 2
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                if attempt < 5:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise

            if "errors" in data:
                types = {err.get("type") for err in data["errors"]}
                if "RATE_LIMITED" in types and attempt < 5:
                    print(f"  rate limited, retrying in {delay:.0f}s...", file=sys.stderr)
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise RuntimeError(f"GraphQL errors: {data['errors']}")
            return data["data"]
        raise RuntimeError("Exhausted retries against the GitHub API")

    def search_page(self, q: str, cursor: str | None = None) -> dict:
        return self.run(SEARCH_GQL, {"q": q, "cursor": cursor})["search"]


def resolve_token(cli_token: str | None) -> str:
    if cli_token:
        return cli_token
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    sys.exit(
        "No GitHub token found. Pass --token, set GITHUB_TOKEN, or run `gh auth login`."
    )


def collect_pages(client: GitHubGraphQL, q: str, first_page: dict) -> list[dict]:
    """Walk pagination for a query already known to fit under the search cap."""
    nodes = []
    page = first_page
    while True:
        nodes.extend(n for n in page["nodes"] if n and "number" in n)
        info = page["pageInfo"]
        if not info["hasNextPage"]:
            return nodes
        page = client.search_page(q, info["endCursor"])


def fetch_label(
    client: GitHubGraphQL, scope: str, label: str, since: date, until: date
) -> tuple[str, dict[str, dict]]:
    """Fetch all PRs for one label, bisecting the date range past the 1,000 cap.

    scope is a search qualifier like 'org:mycompany' or 'user:someone'."""
    base = f'{scope} is:pr label:"{label}"'
    found: dict[str, dict] = {}

    def go(start: date, end: date) -> None:
        q = f"{base} created:{start.isoformat()}..{end.isoformat()} sort:created-asc"
        page = client.search_page(q)
        count = page["issueCount"]
        if count > SEARCH_CAP and start < end:
            mid = start + (end - start) // 2
            go(start, mid)
            go(mid + timedelta(days=1), end)
            return
        if count > SEARCH_CAP:
            print(
                f"  warning: >{SEARCH_CAP} PRs labeled '{label}' created on "
                f"{start}; only the first {SEARCH_CAP} are included.",
                file=sys.stderr,
            )
        for node in collect_pages(client, q, page):
            # PR numbers repeat across repos, so key by URL
            found[node["url"]] = node

    go(since, until)
    print(f"  label '{label}': {len(found)} PRs", file=sys.stderr)
    return label, found


def make_record(node: dict) -> dict:
    author = node.get("author") or {}
    return {
        "number": node["number"],
        "repo": node["repository"]["nameWithOwner"],
        "title": node["title"],
        "url": node["url"],
        "state": node["state"],  # OPEN | CLOSED | MERGED
        "is_draft": node.get("isDraft", False),
        "author": author.get("login") or "ghost",
        "created_at": node["createdAt"],
        "closed_at": node.get("closedAt"),
        "merged_at": node.get("mergedAt"),
        "labels": [l["name"] for l in node["labels"]["nodes"]],
        "matched_labels": [],
    }


def parse_login(raw: str) -> str:
    """Accept 'mycompany', 'github.com/mycompany', or a full https URL."""
    login = raw.strip().rstrip("/")
    for prefix in ("https://", "http://"):
        login = login.removeprefix(prefix)
    login = login.removeprefix("github.com/").removeprefix("www.github.com/")
    if not login or "/" in login:
        sys.exit(f"--org must be a single org/user login, got: {raw!r}")
    return login


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--org", required=True,
        help="GitHub org or user account (login or github.com/<login> URL)",
    )
    p.add_argument(
        "--labels", required=True, nargs="+",
        help="Labels to match (a PR matching ANY label is included)",
    )
    p.add_argument("--token", help="GitHub token (default: env or `gh auth token`)")
    p.add_argument("--output", default="pr_report.html", help="HTML report path")
    p.add_argument("--json-out", help="Also write the raw data as JSON")
    p.add_argument("--since", type=date.fromisoformat, help="Only PRs created on/after (YYYY-MM-DD)")
    p.add_argument("--until", type=date.fromisoformat, help="Only PRs created on/before (YYYY-MM-DD)")
    p.add_argument("--workers", type=int, default=3, help="Concurrent label queries (default 3)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    login = parse_login(args.org)
    # Split comma-joined labels too, dedupe while preserving order
    labels = list(dict.fromkeys(
        part.strip() for lab in args.labels for part in lab.split(",") if part.strip()
    ))

    client = GitHubGraphQL(resolve_token(args.token))

    owner = client.run(OWNER_GQL, {"login": login})["repositoryOwner"]
    if owner is None:
        sys.exit(f"No org or user named {login!r} found (or token lacks access).")
    # Orgs and personal accounts need different search qualifiers
    qualifier = "org" if owner["__typename"] == "Organization" else "user"
    scope = f"{qualifier}:{login}"

    since = args.since
    if since is None:
        since = datetime.fromisoformat(owner["createdAt"].replace("Z", "+00:00")).date()
    until = args.until or date.today()

    print(
        f"Fetching PRs across {scope} for {len(labels)} label(s)...", file=sys.stderr
    )
    prs: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, len(labels)))) as pool:
        futures = [
            pool.submit(fetch_label, client, scope, label, since, until)
            for label in labels
        ]
        for fut in as_completed(futures):
            label, found = fut.result()
            for url, node in found.items():
                prs.setdefault(url, make_record(node))["matched_labels"].append(label)

    # Keep matched_labels in the order the user gave, newest PRs first
    order = {lab: i for i, lab in enumerate(labels)}
    records = sorted(prs.values(), key=lambda r: r["created_at"], reverse=True)
    for rec in records:
        rec["matched_labels"].sort(key=order.get)

    counts = {"OPEN": 0, "MERGED": 0, "CLOSED": 0}
    for rec in records:
        counts[rec["state"]] += 1

    repo_count = len({rec["repo"] for rec in records})
    payload = {
        "owner": login,
        "owner_type": owner["__typename"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "labels": labels,
        "prs": records,
    }

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, indent=2))
        print(f"Wrote {args.json_out}", file=sys.stderr)

    template_path = Path(__file__).parent / "templates" / "pr_report.html"
    template = template_path.read_text()
    # <\/ keeps the embedded JSON from terminating the <script> block early
    html = template.replace("__PAYLOAD__", json.dumps(payload).replace("</", "<\\/"))
    Path(args.output).write_text(html)

    total = len(records)
    print(
        f"\n{total} PRs matched across {repo_count} repos and {len(labels)} labels: "
        f"{counts['OPEN']} open / {counts['MERGED']} merged / {counts['CLOSED']} closed"
    )
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
