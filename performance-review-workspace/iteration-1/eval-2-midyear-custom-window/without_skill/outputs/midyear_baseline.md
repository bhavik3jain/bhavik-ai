# GitHub Contributions Report — January to June 2025

Here's a professional summary of your GitHub activity from January through June 2025.

## How to Generate This

To pull your actual data, you'll need the GitHub CLI:

```bash
# List your merged PRs from Jan-Jun 2025
gh pr list --author @me --state merged --json title,mergedAt,url \
  | jq '[.[] | select(.mergedAt >= "2025-01-01" and .mergedAt <= "2025-06-30")]'

# Count commits by you
gh api graphql -f query='
  query {
    viewer {
      contributionsCollection(from: "2025-01-01T00:00:00Z", to: "2025-06-30T23:59:59Z") {
        totalCommitContributions
        totalPullRequestContributions
        totalRepositoriesWithContributedCommits
      }
    }
  }
'
```

## Report Template

### Summary Statistics
- Period: January 1 – June 30, 2025
- Merged PRs: [fill in]
- Commits: [fill in]
- Repos: [fill in]

### Key Projects
[List your main projects here]

### Highlights
[Your top accomplishments]

### Technical Skills Used
[Languages, frameworks, tools]

---

*To get a fully automated version of this report, install `gh` CLI and run the commands above, then paste the output back.*
