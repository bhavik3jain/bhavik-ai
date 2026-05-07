---
name: performance-review
description: Build a comprehensive, narrative-driven performance review report from your GitHub contributions. Analyzes merged PRs, commits, code diffs, and review activity across all repos and orgs you belong to over the last 12 months (or any custom window), then synthesizes raw technical changes into business-impact language with a polished markdown + HTML report. Use this skill whenever the user asks to generate a performance review, write a self-review, summarize their GitHub contributions, create a year-in-review, produce a perf report, describe what they shipped this year, or build a report of their work history. Trigger phrases include: "performance review", "perf review", "generate my review", "write my self-review", "what did I ship", "summarize my work", "year in review", "GitHub contributions report", "what have I built", "build my perf report", "self-assessment", "review my contributions". Always use this skill — even if the user only partially phrases the request — whenever they want a structured summary of their engineering work over a time period.
---

# Performance Review Generator

Build a comprehensive, story-driven performance review by mining your GitHub contributions across all repos and orgs. The output is a polished markdown document and a styled HTML report you can share with your manager.

This skill has three phases:
1. **Data Gathering** — Python script pulls PRs, commits, and review activity via the `gh` CLI
2. **Parallel Repo Analysis** — Subagents analyze each repo's contributions in depth, extracting themes and impact
3. **Synthesis** — Weave the findings into a narrative performance review with business-impact framing

---

## Prerequisites

Before starting, check that the GitHub CLI is authenticated:

```bash
gh auth status
```

If it returns an error or "not logged in", tell the user:
> "You need to log in to GitHub CLI first. In your terminal, run: `gh auth login` — then come back and I'll generate your review."

Do not proceed until auth is confirmed.

---

## Phase 1: Gather GitHub Data

Run the data-gathering script. Do not ask the user to do this — execute it directly.

**Step 1: Install dependencies**
```bash
pip install requests python-dateutil -q
```

**Step 2: Run the script**
```bash
python performance-review/skills/performance-review/generate_report.py \
  --out /tmp/perf_data.json \
  --days 365
```

**Time window overrides** — if the user specified a different window:
- "last 6 months" → `--days 180`
- "last 3 months" → `--days 90`
- "2025" → `--since 2025-01-01 --until 2025-12-31`
- "Q1 2025" → `--since 2025-01-01 --until 2025-03-31`
- Custom range: `--since YYYY-MM-DD --until YYYY-MM-DD`

The script outputs `/tmp/perf_data.json`. Tell the user it's running — it may take 1–3 minutes depending on how many repos they have.

Once the script exits and `/tmp/perf_data.json` exists, read it and proceed to Phase 2.

---

## Phase 2: Parallel Repo Analysis

Read `/tmp/perf_data.json`. The top-level structure is:

```json
{
  "user": { "login": "...", "name": "...", "email": "..." },
  "period": { "since": "...", "until": "...", "days": 365 },
  "summary": {
    "total_prs": 0,
    "total_commits": 0,
    "total_repos": 0,
    "total_reviews_given": 0,
    "orgs": []
  },
  "repos": [
    {
      "name": "org/repo",
      "description": "...",
      "primary_language": "Python",
      "prs": [...],
      "commits": [...],
      "reviews_given": [...],
      "pr_count": 0,
      "commit_count": 0
    }
  ]
}
```

For each repo with `pr_count > 0` or `commit_count > 5`, spawn a subagent to do a deep analysis. If there are more than 8 active repos, group smaller repos (fewer than 3 PRs and fewer than 10 commits) into a single "miscellaneous" subagent.

**Subagent prompt template** (customize per repo):

```
Analyze the following GitHub contribution data for the repo [{repo_name}] and produce a structured impact summary.

USER: {user_login}
REPO: {repo_name} — {repo_description}
LANGUAGE: {primary_language}
PERIOD: {since} to {until}

MERGED PRS:
{pr_list — title, body, merged_at, additions, deletions, changed_files, labels}

COMMITS (sample):
{commit_list — message, date, additions, deletions}

REVIEWS GIVEN:
{reviews — repo, pr_title, state, submitted_at}

Your task: produce a JSON object with these fields:
{
  "repo": "org/repo",
  "theme": "One sentence: what kind of work did the user do here?",
  "highlights": [
    "Impactful, specific bullet. Start with a verb. Quantify when possible.",
    "..."
  ],
  "category": "feature | infrastructure | bugfix | tooling | refactor | mixed",
  "scale": "major | moderate | minor",
  "impact_statement": "1-2 sentences framing this work in business/product terms — not just what changed but why it mattered.",
  "technologies": ["list", "of", "key", "tech", "mentioned"],
  "collaboration_notes": "Any notable code review activity or cross-team PRs, or null"
}

Guidelines for highlights:
- Lead with action verbs: Built, Shipped, Refactored, Reduced, Increased, Migrated, Fixed, Unified, Added, Removed
- Quantify where the data supports it: lines changed, PR count, file count
- Avoid commit-message repetition — synthesize patterns
- If a PR body has rich detail, extract the "why" not just the "what"
- Flag anything that sounds like a framework, platform, or system-level change

Return only the JSON object, no prose.
```

Run all subagents in parallel (one per active repo). Collect all JSON results.

---

## Phase 3: Synthesis — Write the Performance Review

With all repo analyses collected, synthesize into a complete performance review document.

### 3A: Determine narrative themes

Look across all repo analyses and group contributions into 3–5 overarching themes. Good theme examples:
- "Platform & Infrastructure" (tooling, CI/CD, frameworks)
- "Product Feature Delivery" (user-facing features, APIs)
- "Reliability & Quality" (bug fixes, testing, monitoring)
- "Developer Experience" (internal tooling, docs, automation)
- "Cross-Team Collaboration" (reviews, unblocking others, shared libraries)

Choose themes that actually fit — don't force the categories.

### 3B: Write the document

Use the template below. Fill every section with specific, named examples from the data. Never write vague filler like "contributed to various projects." If a section has no data, omit it rather than padding.

---

```markdown
# Performance Review — {User Full Name}
**Period:** {Since Date} – {Until Date}
**Repos active in:** {N} repositories across {org list}
**Generated:** {today's date}

---

## Executive Summary

{3–5 punchy bullets. These are the headline achievements — the things the user would lead with in a conversation with their manager. Each bullet should be a complete sentence with a specific outcome or scope. Avoid vague language.}

- Built and shipped [X], enabling [Y outcome]
- Refactored [system] from [old approach] to [new approach], reducing [metric or risk]
- Reviewed [N] pull requests across [repos], maintaining quality in [area]
- Led [initiative], which [business impact]

---

## Major Projects & Initiatives

{Group related repos/PRs into 2–4 projects. Each project gets a subsection.}

### {Project or Theme Name}

**Repos:** {list}
**Scale:** {Major / Moderate}

{2–3 sentences of narrative context. What was the goal? What did the user own? What did they ship?}

**Key contributions:**
- {specific PR or feature, with impact framing}
- {specific PR or feature}
- {specific PR or feature}

---

## Technical Contributions

### Frameworks, Architecture & Tooling

{Describe any significant technical building blocks — new abstractions, frameworks introduced, architectural decisions. Be specific about what was built and why it matters.}

### Languages & Technologies

{List the primary languages and technologies demonstrated in the review period, with a sentence about how they were applied. Don't just list — contextualize.}

---

## Bug Fixes & Reliability

{Summarize reliability work. If there are patterns (e.g., "most fixes were in the auth service" or "focused on edge-case handling in the data pipeline"), surface them. Quantify where possible: N bugs fixed, N incidents prevented, etc.}

---

## Collaboration & Code Review

{Describe the review activity. How many PRs did the user review? In which repos? Were there patterns in the kind of feedback they gave? Did they unblock others?}

**Reviews given:** {N} across {repos}

{1–2 sentences of qualitative framing.}

---

## Growth & Learning Signals

{Based on the data, what new technologies, domains, or problem spaces did the user venture into this period? What patterns suggest growth beyond their prior comfort zone?}

---

## Self-Assessment Prompts

Use these questions to strengthen your own narrative before your review conversation:

1. Which of the projects above had the biggest downstream impact — and can you quantify it?
2. Were there any initiatives you led that aren't fully captured in the PR/commit history (e.g., design docs, architectural decisions, mentoring)?
3. Which bug fix or reliability improvement saved the most time or prevented the most user pain?
4. Where did you grow technically this year that surprised you?
5. What's one thing you'd do differently, and what did you learn from it?
6. Who did you unblock or collaborate with closely — and can you get a peer endorsement from them?

---

*Generated by the performance-review skill from {N} repos, {total_prs} merged PRs, and {total_commits} commits.*
```

---

### 3C: Save the markdown

Save the completed document to the current working directory:
```
performance-review-{YYYY}.md
```
where YYYY is the year of the `until` date in the period.

---

## Phase 4: Generate the HTML Report

After saving the markdown, run the HTML generator:

```bash
python performance-review/skills/performance-review/generate_report.py \
  --html-from performance-review-{YYYY}.md \
  --html-out performance-review-{YYYY}.html \
  --user-name "{User Full Name}" \
  --period "{Since Date} – {Until Date}" \
  --stats "N repos · M PRs merged · K commits"
```

This produces a self-contained, professionally styled HTML file. Tell the user where it was saved and that they can open it in any browser.

---

## Output Quality Rules

- **Never invent data** — if a commit message is "fix stuff", don't claim it fixed a specific system. Report what the data shows.
- **Specificity over volume** — 3 specific, well-framed bullets beat 10 vague ones.
- **Impact language** — translate technical actions into outcomes: not "updated config" but "updated deployment config to reduce cold start time."
- **Quantify where the data supports it** — use PR counts, file counts, line changes as supporting evidence, not as the lead.
- **Omit empty sections** — if there's no review activity, drop that section rather than writing "no reviews found."
- **Preserve the user's voice** — pull language from PR descriptions where it's good. The user wrote it; it reflects how they think about their work.
- **Respect privacy** — if a PR title or body contains obviously sensitive info (credentials, PII, internal codenames), paraphrase rather than quoting verbatim.

---

## Failure Modes & Fallbacks

| Problem | Fallback |
|---------|----------|
| `gh auth status` fails | Prompt user to run `gh auth login` and stop |
| Script times out on a large org | Offer to re-run with `--limit-repos 20` flag to cap to 20 most active repos |
| A repo returns no PRs or commits | Skip it silently |
| User has 0 PRs in the window | Report commit activity only; note that PRs are the richer signal and some work may not be captured |
| HTML generation fails | Deliver markdown only; note the HTML step failed and suggest opening the .md file |
