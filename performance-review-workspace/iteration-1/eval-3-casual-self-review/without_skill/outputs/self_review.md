# Self-Review: May 2025 – May 2026

**Bhavik Jain** · Python Engineer · Personal + fintools-org + ai-skills-collective

*14 repos · 52 PRs merged · 214 commits · 38 PRs reviewed*

---

## What I Actually Worked On This Year

Stepping back and looking at all my commits across my personal account, fintools-org, and ai-skills-collective, a few clear themes emerge. This wasn't something I set out to plan — it just crystallized when I looked at everything end-to-end.

---

## Theme 1: Building AI Agents That Actually Ship

The biggest thread running through my year was building LLM-powered skills that go beyond simple chat. The performance-review skill, the trading assistant suite (market-pulse, bounce-scanner, options-scanner, stock-ideas, trade-setup), the scrum-master, and the meal-planner are all in this bucket. What ties them together:

- Each is structured as a **self-contained skill** with a SKILL.md spec, a clear trigger condition, and an opinionated output format
- They integrate with external data — GitHub's `gh` CLI, live web search, market data APIs, Jira-like boards
- They're designed to be called by name from Claude Code, not buried in a monolith

The performance-review skill specifically involved building a real data pipeline: the `generate_report.py` script calls the GitHub API to pull merged PRs, commits, and reviews across orgs, then feeds that into a thematic narrative generator. The HTML output is fully custom — I wrote a `md_to_html` parser from scratch because the dependency overhead of a full markdown library wasn't worth it for this use case.

This year I shipped **11 skill-related PRs** in the bhavik-ai repo alone, and contributed to the ai-skills-collective org's shared infrastructure with 14 more across `claude-skills-registry` and `llm-evals-toolkit`.

---

## Theme 2: Quantitative Finance Infrastructure

Across fintools-org's three repos (`trading-signals`, `data-pipeline`, `risk-engine`), I was building the plumbing for a serious quant stack.

**Signal generation** (`trading-signals`): RSI/MACD indicators with configurable lookbacks, a vectorized pandas-based backtester, mean-reversion scanners, and IV rank filtering for options plays. The backtest harness was probably the most technically demanding piece — getting the PnL calculation right without look-ahead bias in a vectorized form took a few iterations.

**Data infrastructure** (`data-pipeline`): Built a Kafka consumer for real-time tick ingestion, added Postgres schema migrations for options chain data, and layered in Redis caching for high-frequency symbol lookups. Added a Prometheus metrics endpoint so we can actually observe pipeline health in production.

**Risk modeling** (`risk-engine`): Historical VaR with rolling windows, dynamic correlation matrices with exponential decay, Monte Carlo tail risk simulation, and stress test scenarios modeled on a few market shocks (oil spike, rate spike, vol spike). The stress tests ended up being directly useful when the Iran war scenario played out — the framework was already in place.

In total: **20 PRs merged** across these three repos, representing the deepest Python I wrote all year.

---

## Theme 3: Evaluation Frameworks for LLM Outputs

This was the theme I didn't see coming at the start of the year. As I built more skills, I kept running into the same question: how do you know if a skill is actually good? "It seemed to work" isn't enough.

That led to a real investment in eval infrastructure:

- **`llm-evals-toolkit`** (ai-skills-collective): Core eval runner that takes a prompt, runs assertions against the output, and produces a score. Added a rubric-based LLM judge for subjective quality, parallel execution with asyncio, CSV/JSON export, and eventually an HTML dashboard with score visualization.
- **`claude-skills-registry`**: Benchmark runner with variance analysis across iterations, a 10-shot trigger accuracy protocol, and a multi-iteration statistical confidence framework.
- **bhavik-ai evals**: The `performance-review-workspace`, `trading-assistant-workspace`, and `scrum-master-workspace` all have their own eval suites with assertion lists and with/without-skill comparisons.

I ended the year being able to say: I can measure, with statistical confidence, whether a skill change improved or regressed output quality. That's a meaningful shift from where I started.

---

## Theme 4: Personal Tools That Scratch Real Itches

Two repos that don't fit the above categories but I'm glad I built:

**`mls-analyzer`**: A property comparables tool I built when I was evaluating real estate. Ingests MLS data, computes a weighted scoring rubric across comparable properties, and generates a PDF report. Not glamorous but I used it constantly for two months and it saved me a ton of time.

**`meal-planner`**: A Claude skill that takes dietary preferences and a week's calendar and generates a meal plan with grocery list. Built it for personal use but it's one of the more polished skills I've shipped — the calendar integration required thinking carefully about the MCP tool interface.

---

## Numbers That Tell the Story

| Metric | Count |
|--------|-------|
| Repos contributed to | 14 |
| PRs merged | 52 |
| Commits | 214 |
| PRs reviewed (others' code) | 38 |
| Orgs | 3 (personal + fintools-org + ai-skills-collective) |
| Primary language | Python (100% of significant work) |

Biggest months by PR count: October 2025, January 2026, April 2026. Quieter in the summer and around the holidays, which tracks.

The code review number (38 PRs) is meaningful — that's real time invested in colleagues' work, not just my own output.

---

## What Went Well

**Shipping end-to-end.** Every project I started this year reached a usable state. Nothing is stuck in a half-finished branch. The skills all have evals, the finance tools all run in production.

**Building reusable infrastructure.** The eval framework, the data pipeline components, and the skill spec format are all things that get reused. I wasn't just writing one-off scripts.

**Staying in Python.** I could have reached for TypeScript or Go in some places, but staying in Python meant I could move faster and leverage the data science ecosystem where it mattered (pandas, numpy, asyncio, kafka-python).

**Learning to measure quality.** The evals work was a genuine level-up. I now think about outputs differently — not just "does it work" but "how would I know if it regressed."

---

## What Was Harder Than Expected

**The data pipeline debugging cycle.** The Kafka consumer work in `data-pipeline` took longer than it should have. Distributed systems debugging is slower than pure Python debugging — you can't just drop a pdb anywhere. I got better at it but it cost time.

**Scope creep in the skills.** The trading assistant started as one skill and became five. That was the right call architecturally, but the refactoring overhead was real. I should have started with a cleaner decomposition.

**Documentation lag.** My code is generally readable but my docs trailed my shipping. The `mls-analyzer` references (compare.md, analyze.md, etc.) got written weeks after the code stabilized. I want to close that gap.

---

## What I Want to Do More of Next Year

- **More async Python.** The asyncio work in `llm-evals-toolkit` gave me a taste of what's possible — I want to apply that to the trading signal pipeline for lower-latency data processing.
- **Contribute upstream.** Most of my open-source output went into org repos. I want to publish at least two standalone libraries from the work I've done.
- **Invest in the eval culture.** The eval framework is good. I want to see it adopted across more of the org's skills, not just mine.

---

## Self-Assessment Prompts

*Questions worth sitting with before the review conversation:*

1. The quant finance work and the AI skills work are increasingly intertwined — where do I want to put more weight next year?
2. I wrote 38 code reviews. Were those reviews substantive, or was I mostly approving? Do I leave feedback that actually improves the code?
3. The stress test scenarios I built in `risk-engine` were useful when the Iran war scenario hit. What other tail risks am I not modeling that I should be?
4. Is the eval framework I built actually being used by others, or is it mostly benefiting my own workflows?
5. What's the thing I'm most proud of this year that nobody else noticed? What does that tell me about what I should communicate differently?
