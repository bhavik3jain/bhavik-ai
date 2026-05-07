#!/usr/bin/env python3
"""
Performance Review Data Gatherer + HTML Generator

Two modes:
  1. Data gathering:  pulls GitHub contribution data via `gh` CLI → JSON
  2. HTML generation: converts a markdown review doc → styled HTML report

Usage (data gathering):
    python generate_report.py --out /tmp/perf_data.json --days 365
    python generate_report.py --out /tmp/perf_data.json --since 2025-01-01 --until 2025-12-31

Usage (HTML generation):
    python generate_report.py \
        --html-from performance-review-2025.md \
        --html-out performance-review-2025.html \
        --user-name "Bhavik Jain" \
        --period "Jan 2025 – Jan 2026" \
        --stats "12 repos · 47 PRs merged · 183 commits"
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_gh(args: list[str], check: bool = True) -> str:
    """Run a `gh` CLI command and return stdout."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        print(f"[gh error] gh {' '.join(args)}\n{result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def gh_json(args: list[str]) -> list | dict | None:
    """Run a gh command that returns JSON."""
    raw = run_gh(args, check=False)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_date(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return dt_str


# ---------------------------------------------------------------------------
# Auth check
# ---------------------------------------------------------------------------

def check_auth() -> bool:
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    return result.returncode == 0


# ---------------------------------------------------------------------------
# User info
# ---------------------------------------------------------------------------

def get_user() -> dict:
    data = gh_json(["api", "user"])
    if not data:
        print("[error] Could not fetch GitHub user info.", file=sys.stderr)
        sys.exit(1)
    return {
        "login": data.get("login", ""),
        "name": data.get("name") or data.get("login", ""),
        "email": data.get("email") or "",
        "avatar_url": data.get("avatar_url", ""),
        "html_url": data.get("html_url", ""),
    }


# ---------------------------------------------------------------------------
# Orgs
# ---------------------------------------------------------------------------

def get_orgs(user_login: str) -> list[str]:
    data = gh_json(["api", "user/orgs", "--paginate"])
    if not data:
        return []
    return [org["login"] for org in data if isinstance(data, list)]


# ---------------------------------------------------------------------------
# Repos contributed to
# ---------------------------------------------------------------------------

def get_contributed_repos(user_login: str, since: datetime, until: datetime) -> list[dict]:
    """
    Find repos with merged PRs or commits by the user in the window.
    We query merged PRs authored by user across all accessible repos.
    """
    since_str = iso(since)
    until_str = iso(until)

    # Search for PRs authored by user in the window
    query = f"is:pr is:merged author:{user_login} merged:{since_str[:10]}..{until_str[:10]}"
    print(f"  Searching PRs: {query}", flush=True)

    data = gh_json([
        "search", "prs",
        "--json", "repository,title,number,mergedAt,additions,deletions,changedFiles,body,labels,url",
        "--limit", "200",
        "-q", query,
    ])

    if not data:
        data = []

    # Also search for commits (via search API)
    # Group everything by repo
    repos_map: dict[str, dict] = {}

    for pr in (data if isinstance(data, list) else []):
        repo_info = pr.get("repository", {})
        repo_full = repo_info.get("nameWithOwner", "")
        if not repo_full:
            continue
        if repo_full not in repos_map:
            repos_map[repo_full] = {
                "name": repo_full,
                "description": repo_info.get("description", "") or "",
                "primary_language": repo_info.get("primaryLanguage", {}).get("name", "") if repo_info.get("primaryLanguage") else "",
                "prs": [],
                "commits": [],
                "reviews_given": [],
                "pr_count": 0,
                "commit_count": 0,
            }
        repos_map[repo_full]["prs"].append({
            "title": pr.get("title", ""),
            "number": pr.get("number"),
            "merged_at": pr.get("mergedAt", ""),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changedFiles", 0),
            "body": (pr.get("body") or "")[:1000],  # cap body length
            "labels": [lb.get("name", "") for lb in (pr.get("labels") or [])],
            "url": pr.get("url", ""),
        })
        repos_map[repo_full]["pr_count"] += 1

    return list(repos_map.values())


# ---------------------------------------------------------------------------
# Commits per repo
# ---------------------------------------------------------------------------

def get_commits_for_repo(repo_full: str, user_login: str, since: datetime, until: datetime) -> list[dict]:
    since_str = iso(since)
    until_str = iso(until)

    data = gh_json([
        "api",
        f"repos/{repo_full}/commits",
        "-f", f"author={user_login}",
        "-f", f"since={since_str}",
        "-f", f"until={until_str}",
        "-F", "per_page=100",
        "--paginate",
    ])

    if not data or not isinstance(data, list):
        return []

    commits = []
    for c in data[:50]:  # cap at 50 commits per repo to keep JSON manageable
        commit_data = c.get("commit", {})
        stats = c.get("stats", {})
        commits.append({
            "sha": c.get("sha", "")[:8],
            "message": commit_data.get("message", "").split("\n")[0][:120],
            "date": commit_data.get("author", {}).get("date", ""),
            "additions": stats.get("additions", 0),
            "deletions": stats.get("deletions", 0),
        })
    return commits


# ---------------------------------------------------------------------------
# Reviews given
# ---------------------------------------------------------------------------

def get_reviews_given(user_login: str, since: datetime, until: datetime) -> list[dict]:
    """Find PRs where the user left reviews (not their own PRs)."""
    since_str = iso(since)
    until_str = iso(until)
    query = f"is:pr reviewed-by:{user_login} -author:{user_login} updated:{since_str[:10]}..{until_str[:10]}"

    data = gh_json([
        "search", "prs",
        "--json", "repository,title,number,url,state",
        "--limit", "100",
        "-q", query,
    ])

    if not data or not isinstance(data, list):
        return []

    reviews = []
    for pr in data:
        repo_info = pr.get("repository", {})
        reviews.append({
            "repo": repo_info.get("nameWithOwner", ""),
            "pr_title": pr.get("title", ""),
            "pr_number": pr.get("number"),
            "state": pr.get("state", ""),
            "url": pr.get("url", ""),
        })
    return reviews


# ---------------------------------------------------------------------------
# Main data gathering
# ---------------------------------------------------------------------------

def gather_data(out_path: str, since: datetime, until: datetime) -> None:
    print("[1/5] Checking GitHub auth...", flush=True)
    if not check_auth():
        print("ERROR: GitHub CLI not authenticated. Run: gh auth login", file=sys.stderr)
        sys.exit(1)

    print("[2/5] Fetching user profile...", flush=True)
    user = get_user()
    print(f"      User: {user['name']} ({user['login']})", flush=True)

    print("[3/5] Finding contributed repos...", flush=True)
    repos = get_contributed_repos(user["login"], since, until)
    print(f"      Found {len(repos)} repos with merged PRs", flush=True)

    print("[4/5] Fetching commits per repo...", flush=True)
    for i, repo in enumerate(repos):
        print(f"      [{i+1}/{len(repos)}] {repo['name']}...", flush=True)
        commits = get_commits_for_repo(repo["name"], user["login"], since, until)
        repo["commits"] = commits
        repo["commit_count"] = len(commits)

    print("[5/5] Fetching code reviews given...", flush=True)
    reviews_given = get_reviews_given(user["login"], since, until)
    print(f"      Found {len(reviews_given)} PRs reviewed by {user['login']}", flush=True)

    # Attach reviews_given to relevant repos
    reviews_by_repo: dict[str, list] = {}
    for r in reviews_given:
        reviews_by_repo.setdefault(r["repo"], []).append(r)

    for repo in repos:
        repo["reviews_given"] = reviews_by_repo.get(repo["name"], [])

    # Also add repos where user only gave reviews (no PRs of their own)
    for repo_name, reviews in reviews_by_repo.items():
        if not any(r["name"] == repo_name for r in repos):
            repos.append({
                "name": repo_name,
                "description": "",
                "primary_language": "",
                "prs": [],
                "commits": [],
                "reviews_given": reviews,
                "pr_count": 0,
                "commit_count": 0,
            })

    total_prs = sum(r["pr_count"] for r in repos)
    total_commits = sum(r["commit_count"] for r in repos)
    orgs = list({r["name"].split("/")[0] for r in repos if "/" in r["name"]})

    output = {
        "user": user,
        "period": {
            "since": iso(since),
            "until": iso(until),
            "days": (until - since).days,
            "since_display": fmt_date(iso(since)),
            "until_display": fmt_date(iso(until)),
        },
        "summary": {
            "total_prs": total_prs,
            "total_commits": total_commits,
            "total_repos": len(repos),
            "total_reviews_given": len(reviews_given),
            "orgs": orgs,
        },
        "repos": repos,
    }

    Path(out_path).write_text(json.dumps(output, indent=2))
    print(f"\nDone. Data saved to {out_path}")
    print(f"  {total_prs} merged PRs · {total_commits} commits · {len(repos)} repos")


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def generate_html(
    md_path: str,
    html_path: str,
    user_name: str,
    period: str,
    stats: str,
) -> None:
    md_content = Path(md_path).read_text()

    # Convert markdown to HTML (basic conversion — headings, bullets, bold)
    html_body = md_to_html(md_content)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Performance Review — {user_name}</title>
<style>
  :root {{
    --bg: #f8f9fa;
    --surface: #ffffff;
    --border: #e2e8f0;
    --accent: #4f46e5;
    --accent-light: #eef2ff;
    --text: #1a202c;
    --muted: #64748b;
    --heading: #0f172a;
    --tag-bg: #f1f5f9;
    --tag-text: #475569;
    --bullet-accent: #818cf8;
    --section-bg: #fafbff;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    font-size: 15px;
  }}

  .hero {{
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    padding: 48px 32px;
    text-align: center;
  }}

  .hero h1 {{
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
  }}

  .hero .subtitle {{
    font-size: 1.05rem;
    opacity: 0.85;
    margin-bottom: 24px;
  }}

  .stats-bar {{
    display: flex;
    justify-content: center;
    gap: 32px;
    flex-wrap: wrap;
    margin-top: 8px;
  }}

  .stat-chip {{
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 999px;
    padding: 6px 18px;
    font-size: 0.85rem;
    font-weight: 500;
    backdrop-filter: blur(4px);
  }}

  .container {{
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }}

  .toc {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 40px;
  }}

  .toc h2 {{
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 14px;
  }}

  .toc ul {{
    list-style: none;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 24px;
  }}

  .toc ul li a {{
    color: var(--accent);
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
  }}

  .toc ul li a:hover {{ text-decoration: underline; }}

  section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px 36px;
    margin-bottom: 24px;
  }}

  section:first-of-type {{ margin-top: 0; }}

  h1.doc-title {{ display: none; }} /* hidden — shown in hero */

  h2 {{
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--heading);
    border-bottom: 2px solid var(--accent-light);
    padding-bottom: 10px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}

  h2::before {{
    content: "";
    display: inline-block;
    width: 4px;
    height: 20px;
    background: var(--accent);
    border-radius: 2px;
    flex-shrink: 0;
  }}

  h3 {{
    font-size: 1rem;
    font-weight: 700;
    color: var(--heading);
    margin: 24px 0 10px;
  }}

  h4 {{
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 18px 0 8px;
  }}

  p {{
    margin-bottom: 14px;
    color: var(--text);
  }}

  ul, ol {{
    padding-left: 0;
    margin-bottom: 16px;
    list-style: none;
  }}

  ul li {{
    position: relative;
    padding-left: 20px;
    margin-bottom: 8px;
    color: var(--text);
    line-height: 1.65;
  }}

  ul li::before {{
    content: "▸";
    position: absolute;
    left: 0;
    color: var(--bullet-accent);
    font-size: 0.8em;
    top: 3px;
  }}

  ol {{
    counter-reset: ol-counter;
  }}

  ol li {{
    counter-increment: ol-counter;
    position: relative;
    padding-left: 28px;
    margin-bottom: 10px;
    line-height: 1.65;
  }}

  ol li::before {{
    content: counter(ol-counter) ".";
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: 700;
    font-size: 0.9em;
  }}

  strong {{ color: var(--heading); font-weight: 600; }}

  em {{ color: var(--muted); font-style: italic; }}

  code {{
    background: var(--tag-bg);
    color: var(--accent);
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.85em;
    font-family: "SF Mono", "Fira Code", monospace;
  }}

  pre {{
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 18px 22px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 0.85em;
    margin: 16px 0;
  }}

  pre code {{ background: none; color: inherit; padding: 0; }}

  hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 28px 0;
  }}

  .exec-summary ul li {{
    background: var(--accent-light);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px 10px 18px;
    margin-bottom: 10px;
  }}

  .exec-summary ul li::before {{
    content: "★";
    color: var(--accent);
    top: 10px;
  }}

  .prompts-section ol li {{
    background: var(--section-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px 12px 40px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin: 16px 0;
  }}

  th {{
    background: var(--tag-bg);
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}

  td {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }}

  tr:last-child td {{ border-bottom: none; }}

  .footer {{
    text-align: center;
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 40px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
  }}

  @media print {{
    body {{ background: white; }}
    .hero {{ background: #4f46e5 !important; -webkit-print-color-adjust: exact; }}
    section {{ break-inside: avoid; }}
  }}

  @media (max-width: 600px) {{
    .hero {{ padding: 32px 20px; }}
    .hero h1 {{ font-size: 1.5rem; }}
    section {{ padding: 24px 20px; }}
    .toc ul {{ grid-template-columns: 1fr; }}
    .stats-bar {{ gap: 12px; }}
  }}
</style>
</head>
<body>

<div class="hero">
  <h1>Performance Review</h1>
  <div class="subtitle">{user_name} &nbsp;·&nbsp; {period}</div>
  <div class="stats-bar">
    {''.join(f'<span class="stat-chip">{s.strip()}</span>' for s in stats.split('·'))}
  </div>
</div>

<div class="container">
{html_body}

  <div class="footer">
    Generated by the performance-review skill &nbsp;·&nbsp; {datetime.now().strftime("%B %d, %Y")}
  </div>
</div>

</body>
</html>"""

    Path(html_path).write_text(html)
    print(f"HTML report saved to {html_path}")


def md_to_html(md: str) -> str:
    """
    Convert markdown to semantic HTML sections.
    Handles: h1/h2/h3/h4, bold, italic, bullet lists, ordered lists,
    horizontal rules, code blocks, inline code, paragraphs.
    """
    import re

    lines = md.split("\n")
    output_parts: list[str] = []

    in_section = False
    in_ul = False
    in_ol = False
    in_pre = False
    pre_lines: list[str] = []
    section_class = ""
    first_h1_seen = False

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul:
            output_parts.append("</ul>")
            in_ul = False
        if in_ol:
            output_parts.append("</ol>")
            in_ol = False

    def open_section(cls=""):
        nonlocal in_section, section_class
        if in_section:
            output_parts.append("</section>")
        output_parts.append(f'<section class="{cls}">' if cls else "<section>")
        in_section = True
        section_class = cls

    def inline(text: str) -> str:
        # Bold **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic *text*
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Inline code `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith("```"):
            if in_pre:
                output_parts.append("<pre><code>" + "\n".join(pre_lines) + "</code></pre>")
                pre_lines = []
                in_pre = False
            else:
                flush_list()
                in_pre = True
            i += 1
            continue

        if in_pre:
            pre_lines.append(line)
            i += 1
            continue

        # H1
        if line.startswith("# ") and not line.startswith("## "):
            flush_list()
            if not first_h1_seen:
                first_h1_seen = True
                # Skip the h1 — shown in hero
                i += 1
                continue

        # H2 — starts a new section
        if line.startswith("## "):
            flush_list()
            heading_text = line[3:].strip()
            slug = re.sub(r'[^a-z0-9]+', '-', heading_text.lower()).strip('-')

            cls = ""
            if "executive" in heading_text.lower():
                cls = "exec-summary"
            elif "self-assessment" in heading_text.lower() or "prompt" in heading_text.lower():
                cls = "prompts-section"

            open_section(cls)
            output_parts.append(f'<h2 id="{slug}">{inline(heading_text)}</h2>')
            i += 1
            continue

        # H3
        if line.startswith("### "):
            flush_list()
            output_parts.append(f'<h3>{inline(line[4:].strip())}</h3>')
            i += 1
            continue

        # H4
        if line.startswith("#### "):
            flush_list()
            output_parts.append(f'<h4>{inline(line[5:].strip())}</h4>')
            i += 1
            continue

        # HR
        if line.strip() in ("---", "***", "___"):
            flush_list()
            output_parts.append("<hr>")
            i += 1
            continue

        # Ordered list item
        if re.match(r'^\d+\. ', line):
            if in_ul:
                flush_list()
            if not in_ol:
                output_parts.append("<ol>")
                in_ol = True
            content = re.sub(r'^\d+\. ', '', line)
            output_parts.append(f"<li>{inline(content)}</li>")
            i += 1
            continue

        # Bullet list item
        if line.startswith("- ") or line.startswith("* "):
            if in_ol:
                flush_list()
            if not in_ul:
                output_parts.append("<ul>")
                in_ul = True
            content = line[2:]
            output_parts.append(f"<li>{inline(content)}</li>")
            i += 1
            continue

        # Empty line
        if line.strip() == "":
            flush_list()
            i += 1
            continue

        # Paragraph
        flush_list()
        if not in_section:
            open_section()
        output_parts.append(f"<p>{inline(line)}</p>")
        i += 1

    flush_list()
    if in_section:
        output_parts.append("</section>")

    return "\n".join(output_parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Performance Review data gatherer + HTML generator")

    # Data gathering mode
    parser.add_argument("--out", help="Output JSON path for gathered data")
    parser.add_argument("--days", type=int, default=365, help="Number of days to look back")
    parser.add_argument("--since", help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--until", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--limit-repos", type=int, default=0, help="Cap number of repos analyzed (0 = no limit)")

    # HTML generation mode
    parser.add_argument("--html-from", help="Markdown file to convert to HTML")
    parser.add_argument("--html-out", help="Output HTML file path")
    parser.add_argument("--user-name", default="", help="User's full name for HTML header")
    parser.add_argument("--period", default="", help="Period string for HTML header")
    parser.add_argument("--stats", default="", help="Stats string for HTML chips")

    args = parser.parse_args()

    # HTML generation mode
    if args.html_from:
        if not args.html_out:
            print("Error: --html-out required with --html-from", file=sys.stderr)
            sys.exit(1)
        generate_html(
            md_path=args.html_from,
            html_path=args.html_out,
            user_name=args.user_name,
            period=args.period,
            stats=args.stats,
        )
        return

    # Data gathering mode
    if not args.out:
        print("Error: --out required for data gathering mode", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(tz=timezone.utc)

    if args.until:
        until = datetime.fromisoformat(args.until).replace(tzinfo=timezone.utc)
    else:
        until = now

    if args.since:
        since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    else:
        since = until - timedelta(days=args.days)

    print(f"Period: {since.strftime('%Y-%m-%d')} → {until.strftime('%Y-%m-%d')} ({(until-since).days} days)")
    gather_data(args.out, since, until)


if __name__ == "__main__":
    main()
