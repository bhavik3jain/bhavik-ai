---
name: market-pulse
description: Daily US market overview and macro snapshot. Use this skill when the user wants to know what the market is doing, pre-market conditions, sector performance, macro backdrop, VIX/fear gauge, Fed calendar, or overall market sentiment. Triggers on: "market pulse", "what's the market doing", "market overview", "how's the market", "pre-market", "sector rotation", "macro conditions", "market today", "market sentiment". Always use this before generating trade ideas so you have proper market context.
---

# Market Pulse

Deliver a fast, actionable daily market snapshot. All data must be live — no estimates or stale figures.

This skill supports two modes:
- **Standard** (default): Single-pass market overview
- **`--deep-analysis`**: Three parallel sub-agents each assess the market independently; their findings are synthesized into a consensus bias with confidence scoring

---

## `--deep-analysis` Mode

When the user includes `--deep-analysis`, run three parallel sub-agents instead of the standard flow.

### Overview

Each agent looks at the market through a different lens. The synthesis step combines their assessments into a consensus bias score, highlighting where all three agree (high conviction) vs. where they diverge (mixed signals).

```
User: /market-pulse --deep-analysis
           │
           ├── Agent 1: Price & Internals (yfinance — indices, breadth, momentum)
           ├── Agent 2: Sentiment & Flow (Unusual Whales — put/call, dark pool, options flow)
           └── Agent 3: Macro & Volatility (CBOE / VIX / rates / sector rotation)
           │
           ▼
     Consensus Bias Scoring
     ┌──────────────────────────────────────┐
     │ Agent 1 bias: Bullish / Bearish / Neutral │
     │ Agent 2 bias: Bullish / Bearish / Neutral │
     │ Agent 3 bias: Bullish / Bearish / Neutral │
     └──────────────────────────────────────┘
           │
     3/3 Bullish  → 🟢 Strong Bullish — high conviction risk-on
     2/3 Bullish  → 🟡 Lean Bullish — confirm before sizing up
     Split        → ⚪ Mixed — choppy, reduce size, wait for clarity
     2/3 Bearish  → 🟡 Lean Bearish — defensive posture
     3/3 Bearish  → 🔴 Strong Bearish — high conviction risk-off
```

### Agent 1: Price & Internals (yfinance)

This agent assesses raw market price action and breadth.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^NDX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^RUT?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^DJI?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^TNX?interval=1d&range=5d
```

Also fetch all 11 sector ETFs (XLK, XLF, XLE, XLV, XLI, XLC, XLY, XLP, XLB, XLRE, XLU).

**Bullish signals:** SPY above 50-day MA, Nasdaq leading (growth risk-on), Russell 2000 outperforming (small cap participation = broad rally), >7 of 11 sectors positive, 10Y yield stable or falling.

**Bearish signals:** SPY below 50-day MA, Russell 2000 underperforming, <4 of 11 sectors positive, 10Y yield rising sharply (>5 bps/day), Nasdaq lagging defensives.

**Output:** Bullish / Bearish / Neutral with specific data points from yfinance.

---

### Agent 2: Sentiment & Flow (Unusual Whales / CBOE)

This agent assesses where smart money and retail sentiment are positioned.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX9D?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^VIX3M?interval=1d&range=5d
```

Also search:
- `"CBOE equity put call ratio today" [current date]`
- `"options flow today market direction" [current date]`
- `"dark pool sentiment today" [current date]`
- `"market breadth advancing declining" [current date]`

**Bullish signals:** Put/call ratio > 1.1 (contrarian — fear = buy), VIX9D falling vs VIX3M (near-term fear declining), net call flow positive across major indices, dark pool predominantly buy-side, advancing stocks > declining by 2:1+.

**Bearish signals:** Put/call ratio < 0.7 (complacency = sell signal), VIX9D spiking above VIX (near-term fear), heavy put sweeps on SPY/QQQ, dark pool sell-side dominant, declining stocks > advancing.

**Output:** Bullish / Bearish / Neutral with specific put/call ratio, VIX term structure data, and flow observations.

---

### Agent 3: Macro & Volatility (CBOE / VIX / Rates / Geopolitics)

This agent assesses the macro environment and whether it supports risk-taking.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^TNX?interval=1d&range=5d
```

Also search:
- `"Fed speakers today" OR "FOMC" [current date]`
- `"CPI inflation data" OR "jobs report" [current date]`
- `"geopolitical risk" "market impact" [current date]`
- `"earnings season outlook" [current date]`

**Bullish signals:** VIX < 20 and falling, no major macro binary events this week, earnings season showing positive beats, geopolitical risks de-escalating, Fed language dovish or neutral.

**Bearish signals:** VIX > 25 or rising, major macro event this week (CPI, FOMC, jobs), earnings misses accumulating, geopolitical escalation, Fed hawkish surprise.

**Output:** Bullish / Bearish / Neutral with specific macro data points and upcoming risk events.

---

### Consensus Synthesis & Output

After all three agents complete:

**Consensus Bias Table:**
| Agent | Lens | Bias | Key Signal |
|-------|------|------|-----------|
| Agent 1 — Price/Internals | yfinance | [Bullish/Bearish/Neutral] | [Top data point] |
| Agent 2 — Sentiment/Flow | Unusual Whales/CBOE | [Bullish/Bearish/Neutral] | [Top data point] |
| Agent 3 — Macro/Volatility | VIX/Rates | [Bullish/Bearish/Neutral] | [Top data point] |
| **Consensus** | | **[Bias]** | **[Score badge]** |

**Score → Badge mapping:**
- 3/3 Bullish → 🟢 Strong Bullish
- 2/3 Bullish → 🟡 Lean Bullish
- 1/3 Bullish, 1/3 Bearish, 1/3 Neutral → ⚪ Mixed
- 2/3 Bearish → 🟡 Lean Bearish
- 3/3 Bearish → 🔴 Strong Bearish

**Where agents diverge:** Explicitly call out any split between agents and what it means — e.g., "Price action is bullish (Agent 1) but sentiment is bearish (Agent 2), suggesting a potential distribution phase — reduce size and wait for confirmation."

**Actionable implications by badge:**
- 🟢 Strong Bullish → Full-size momentum longs, buy breakouts, sell puts
- 🟡 Lean Bullish → 50–75% size, favor quality setups, use defined risk (spreads)
- ⚪ Mixed → 25–50% size max, iron condors/range plays, wait for clearer signal
- 🟡 Lean Bearish → Reduce longs, add hedges, buy dips selectively only on extreme oversold
- 🔴 Strong Bearish → Short/put bias, raise cash, sell calls on bounces

---

## Standard Mode (Default — No `--deep-analysis` Flag)

### Step 1: Fetch Live Data (Run ALL in Parallel)

#### A. yfinance — Live Index Quotes

```
https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^NDX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^RUT?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^DJI?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^TNX?interval=1d&range=5d
```

Fetch all 11 sector ETFs: XLK, XLF, XLE, XLV, XLI, XLC, XLY, XLP, XLB, XLRE, XLU.

**Extract:** `regularMarketPrice`, `regularMarketChangePercent`, intraday range, VIX level and direction.

#### B. Unusual Whales / CBOE — Sentiment Data

Search: `"put call ratio today" [current date]`, `"market breadth today" [current date]`, `"CBOE equity put call ratio" current`

Fetch VIX term structure:
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX9D?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^VIX3M?interval=1d&range=5d
```

#### C. News & Catalysts

Search: `"stock market news today" [current date]`, `"Fed speakers today" [current date]`, `"earnings today" [current date]`, `"economic data today" [current date]`

### Step 2: Write the Market Pulse Report

---

## Market Pulse — [Date]

### Indices (Live via yfinance)
| Index | Price | Change | % Change |
|-------|-------|--------|----------|
| S&P 500 (^GSPC) | $[X,XXX] | [+/-X.XX] | [+/-X.XX]% |
| Nasdaq 100 (^NDX) | $[XX,XXX] | [+/-X.XX] | [+/-X.XX]% |
| Russell 2000 (^RUT) | $[X,XXX] | [+/-X.XX] | [+/-X.XX]% |
| Dow Jones (^DJI) | $[XX,XXX] | [+/-X.XX] | [+/-X.XX]% |

### Market Internals (Live)
- **VIX**: [XX.X] ([+/-X]% today) — [Low / Normal / Elevated / High Fear / Extreme]
- **VIX9D vs VIX**: [XX.X] vs [XX.X] — [near-term fear higher/lower than 30-day avg]
- **10Y Treasury**: [X.XX]% ([+/-X bps]) — [Rising = growth headwind / Falling = tailwind]
- **Put/Call Ratio**: [X.XX] — [fearful / neutral / complacent]
- **Market Trend**: [Bullish / Bearish / Neutral / Choppy]

### Sector Snapshot (Live via yfinance)
**Leading:** [Sector (ETF) +X.X%], [Sector (ETF) +X.X%], [Sector (ETF) +X.X%]
**Lagging:** [Sector (ETF) -X.X%], [Sector (ETF) -X.X%], [Sector (ETF) -X.X%]

### Key Catalysts Today
- [Most important news item and market impact]
- [Second most important — earnings, economic data, geopolitical]
- [Any Fed speakers or macro data]

### Fed & Macro Watch
- [Fed speakers today / this week + rate expectations]
- [Macro data releases this week: CPI, jobs, GDP, PMI]

### Market Bias
**Overall**: [Bullish / Bearish / Neutral] — [1–2 sentence thesis]
**Best setups today**: [Long / Short / Mixed] — [Which sectors/themes are working]

---

### Step 3: Flag Actionable Themes

**Today's Themes:**
- [Theme 1 with specific trade direction implication]
- [Theme 2 with specific trade direction implication]
- [Theme 3 with specific trade direction implication]

These set up ideas for `/options-scanner` or `/stock-ideas`.

---

## Data Quality Rules (Both Modes)

- **All index/sector prices from live yfinance fetches** — not search results or prior knowledge
- **Flag market hours**: Note if data is pre-market, intraday, or after-hours
- **If a yfinance fetch fails**: Note it explicitly and fall back to web search with source attribution
