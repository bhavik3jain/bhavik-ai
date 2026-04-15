---
name: trade-setup
description: Deep dive analysis on a specific stock ticker with full trade setup — technical levels, options chain analysis, entry/exit/stop, and thesis. Use this skill whenever the user mentions a specific ticker and wants analysis, a trade plan, or asks "what do you think about $XYZ", "analyze $XYZ", "set up a trade on $XYZ", "is $XYZ a good buy", "options on $XYZ", or any request focused on a single stock. Always give a complete trade plan, not just commentary.
---

# Trade Setup

Do a complete analysis of a specific ticker and produce a full, ready-to-execute trade plan using live data. Treat this like a professional trading desk note — every number must be real.

This skill supports two modes:
- **Standard** (default): Single comprehensive analysis using all data sources
- **`--deep-analysis`**: Three parallel sub-agents each independently assess the ticker from a different angle; a recommendation is only made when 2/3 or 3/3 agents agree on direction

---

## `--deep-analysis` Mode

When the user includes `--deep-analysis`, run three parallel sub-agents on the specific ticker instead of the standard flow.

### Overview

Each agent looks at the same ticker through a completely different lens and arrives at an independent directional verdict. The synthesis step surfaces the consensus view and flags exactly where agents disagree — which is often the most important risk information.

```
User: /trade-setup $TICKER --deep-analysis
           │
           ├── Agent 1: Technical & Fundamental (yfinance — price, MAs, earnings, valuation)
           ├── Agent 2: Options Flow & Positioning (Unusual Whales — flow, IV, options chain)
           └── Agent 3: Macro & Sector Fit (CBOE/VIX — volatility regime, sector, macro risk)
           │
           ▼
     Per-Agent Verdict: Bullish / Bearish / Neutral
           │
     3/3 Bullish   → 🟢 Strong Bullish — high conviction long
     2/3 Bullish   → 🟡 Lean Bullish — trade with smaller size
     Split/Mixed   → ⚪ No Edge — do not trade, explain the conflict
     2/3 Bearish   → 🟡 Lean Bearish — short or puts with smaller size
     3/3 Bearish   → 🔴 Strong Bearish — high conviction short/put
```

### Agent 1: Technical & Fundamental Analysis (yfinance)

This agent assesses the stock's price structure, trend, valuation, and fundamental momentum.

**Data to fetch:**
```
https://query2.finance.yahoo.com/v10/finance/quoteSummary/TICKER?modules=defaultKeyStatistics,summaryDetail,financialData,calendarEvents,recommendationTrend,earningsTrend,upgradeDowngradeHistory
https://query1.finance.yahoo.com/v8/finance/chart/TICKER?interval=1d&range=6mo
```

**Bullish verdict criteria (flag if 3+ of these are true):**
- Price above 50-day AND 200-day MA
- Analyst consensus Buy (`recommendationMean` < 2.5) with `targetMeanPrice` >10% above current
- Revenue growth >10% YoY AND earnings growth >10% YoY
- Recent earnings beat (within 60 days) and stock is above the post-earnings price
- Valuation reasonable vs sector (not >2x sector P/E without growth justification)
- Upgrade or initiated coverage with Buy in last 30 days (`upgradeDowngradeHistory`)

**Bearish verdict criteria:**
- Price below 50-day AND 200-day MA
- Analyst consensus below 3.0 (Hold/Sell) or `targetMeanPrice` below current price
- Revenue growth slowing or negative YoY
- Recent earnings miss or guidance cut
- Valuation stretched with decelerating growth

**Output:** Bullish / Bearish / Neutral verdict, score (X of 6 criteria met), and the 3 most important data points supporting the verdict.

---

### Agent 2: Options Flow & Positioning (Unusual Whales / yfinance options chain)

This agent assesses what the options market and institutional flow are saying about the ticker.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v7/finance/options/TICKER
```

Also search:
- `"[TICKER] unusual options activity" last 7 days`
- `"[TICKER] options flow" [current date]`
- `"[TICKER] dark pool" OR "[TICKER] block trade" recent`
- `"[TICKER] short interest" OR "[TICKER] put call ratio"`

**Bullish verdict criteria (flag if 2+ of these are true):**
- Net call flow positive: more call volume than put volume at OTM strikes
- Large call sweep or block (>500 contracts) detected in last 5 days
- ATM IV low relative to recent range (cheap to buy calls — market not pricing a move)
- Dark pool prints at or above current price (accumulation signal)
- Put/call ratio on the specific ticker < 0.7 (calls outpacing puts = bullish positioning)
- Short interest declining (shorts covering = upward pressure)

**Bearish verdict criteria:**
- Net put flow dominant (put sweeps, OTM put blocks)
- IV elevated and skewed toward puts (market pricing downside)
- Dark pool prints below current price (distribution signal)
- Put/call ratio on ticker > 1.5 (heavy put positioning)
- Short interest rising significantly

**Output:** Bullish / Bearish / Neutral verdict, specific flow evidence (strike, expiry, size, sweep/block where available), live ATM IV from yfinance options chain, and OI/volume context.

---

### Agent 3: Macro & Sector Fit (CBOE / VIX / Sector / Macro)

This agent assesses whether the broader environment supports the intended trade direction.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^TNX?interval=1d&range=5d
```

Fetch the ticker's sector ETF (e.g., XLK for tech, XLF for financials, XLE for energy):
```
https://query1.finance.yahoo.com/v8/finance/chart/[SECTOR_ETF]?interval=1d&range=5d
```

Also search:
- `"[TICKER] sector performance today"`
- `"macro outlook" [current date]`
- `"[TICKER] upcoming events" catalyst earnings FDA`

**Bullish verdict criteria:**
- Ticker's sector ETF is up today and outperforming SPY (sector tailwind)
- VIX ≤ 20 or falling (risk-on environment favors longs)
- No major binary macro event (FOMC, CPI, jobs) within the next 2 weeks
- 10Y yield stable or falling (not a headwind for growth/duration names)
- No upcoming earnings within 2 weeks (unless earnings is the catalyst — then flag explicitly)

**Bearish verdict criteria:**
- Sector ETF underperforming or negative (sector headwind)
- VIX > 22 or rising (risk-off)
- Binary macro event within 2 weeks adds unquantifiable risk to a long
- Rising yields as specific headwind for this stock's valuation type

**Output:** Bullish / Bearish / Neutral verdict, live VIX level, sector ETF performance today, and specific macro risk events on the calendar.

---

### Consensus Synthesis & Output

After all three agents complete, build the verdict table:

**Agent Verdicts for $[TICKER]:**
| Agent | Lens | Verdict | Top Signal |
|-------|------|---------|-----------|
| Agent 1 — Technical/Fundamental | yfinance | [Bullish/Bearish/Neutral] | [Most important data point] |
| Agent 2 — Options Flow | Unusual Whales + yfinance | [Bullish/Bearish/Neutral] | [Most important signal] |
| Agent 3 — Macro/Sector | CBOE/VIX/Sector | [Bullish/Bearish/Neutral] | [Most important context] |
| **Consensus** | | **[Bias]** | **[Badge]** |

**Score → Action mapping:**
- 🟢 3/3 Bullish → Full trade plan — long stock or buy calls/spreads at full size
- 🟡 2/3 Bullish → Reduced-size trade plan — note which agent dissents and why
- ⚪ Split/Mixed → No trade recommendation — explain the conflict clearly; add to watchlist with resolution triggers
- 🟡 2/3 Bearish → Reduced-size bearish plan — short stock or buy puts/bear spreads
- 🔴 3/3 Bearish → Full bearish trade plan

**Where agents diverge** (most important section): If any two agents disagree, call it out explicitly:
- "Agent 1 is bullish on fundamentals but Agent 2 sees heavy put flow — this suggests institutional hedging against a position, not outright bearish conviction. Watch for flow reversal."
- "Agent 3 flags FOMC in 8 days as macro risk — this doesn't change the bullish thesis but means options buyers should use spreads to reduce vega exposure."

---

### Deep Analysis Trade Plan Output

After the consensus verdict, present the full trade plan using the standard template below, prefixed with the conviction badge.

For 🟢 or 🔴 (3/3): Full-size trade plan.
For 🟡 (2/3): Same template but note "Reduced size recommended — [dissenting agent] sees [specific risk]."
For ⚪ (split): No trade plan — present a "Conditions for Entry" section instead:

**Conditions for Entry (⚪ Mixed Signal):**
- Enter bullish if: [specific condition that would resolve the conflicting signal]
- Enter bearish if: [specific condition]
- Do not enter until: [specific resolution trigger]
- Check again: [timeframe — e.g., "after earnings on MM/DD" or "if VIX drops below 20"]

---

## Standard Mode (Default — No `--deep-analysis` Flag)

### Step 1: Gather Live Data (Run ALL in Parallel)

#### A. yfinance — Price, Technicals & Fundamentals

```
https://query2.finance.yahoo.com/v10/finance/quoteSummary/TICKER?modules=defaultKeyStatistics,summaryDetail,financialData,calendarEvents,recommendationTrend,earningsTrend,upgradeDowngradeHistory
https://query1.finance.yahoo.com/v8/finance/chart/TICKER?interval=1d&range=3mo
```

**Extract:** `regularMarketPrice`, `regularMarketChangePercent`, `regularMarketVolume`, `averageDailyVolume10Day`, `fiftyDayAverage`, `twoHundredDayAverage`, `fiftyTwoWeekHigh`, `fiftyTwoWeekLow`, `trailingPE`, `forwardPE`, `priceToSalesTrailing12Months`, `revenueGrowth`, `earningsGrowth`, `grossMargins`, `operatingMargins`, `recommendationMean`, `targetMeanPrice`, `numberOfAnalystOpinions`, `earningsDate`, `upgradeDowngradeHistory`

#### B. yfinance — Live Options Chain

```
https://query1.finance.yahoo.com/v7/finance/options/TICKER
```

**Extract:** All expirations, ATM strike bid/ask/IV/OI/volume, straddle cost as % of stock price, most liquid strikes.

#### C. Unusual Whales — Options Flow & Institutional Activity

Search: `"[TICKER] unusual options activity" [current date or last 7 days]`, `"[TICKER] dark pool" recent`, `"[TICKER] analyst upgrade downgrade" [current date]`, `"[TICKER] news today"`

#### D. Market Context

```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
```
Search: `"[TICKER] sector performance today"`

### Step 2: Write the Trade Setup Report

---

## Trade Setup: $[TICKER] — [Company Name]
*[Date] | [Sector] | Market Cap: $[X.X]B*

### Snapshot (Live via yfinance)
| Metric | Value |
|--------|-------|
| Current Price | $[XX.XX] |
| Today's Change | [+/-X.XX]% |
| 52-Week Range | $[XX.XX] – $[XX.XX] |
| Volume vs 10-Day Avg | [X.X]x ([above/below] average) |
| vs 50-Day MA | $[XX.XX] ([+/-X.X]% [above/below]) |
| vs 200-Day MA | $[XX.XX] ([+/-X.X]% [above/below]) |
| Next Earnings | [Date] (in [X] weeks) |
| Analyst Target | $[XX.XX] ([X]% upside) — [Buy/Hold/Sell] ([X] analysts) |
| IV (ATM, near-term) | [XX]% — [High/Normal/Low] |

### Technical Picture
[2–3 sentences on chart setup from yfinance MA/price history data]

**Key Levels:**
- Strong Support: $[XX.XX] and $[XX.XX]
- Strong Resistance: $[XX.XX] and $[XX.XX]
- Breakout Level: $[XX.XX] | Breakdown Level: $[XX.XX]

### Fundamental Picture
[2–3 sentences on business from yfinance financial data]

**Key Stats:** Revenue growth [X]% | Earnings growth [X]% | Gross margin [X]% | Operating margin [X]% | Trailing P/E [X]x | Forward P/E [X]x | P/S [X]x | Analyst target $[XX.XX] ([X]% upside)

### Recent Analyst Actions (yfinance upgradeDowngradeHistory)
| Date | Firm | Action | Rating Change | Target |
|------|------|--------|---------------|--------|
| [Date] | [Firm] | [Upgrade/Downgrade/Initiated] | [From → To] | $[XX] |

### Catalyst Map
| Catalyst | Date | Impact |
|----------|------|--------|
| Earnings | [yfinance calendarEvents date] | [Bullish/Bearish/Binary] |
| [Event 2] | [Date] | [Impact] |

### News & Flow
- **Recent news**: [Top 2–3 headlines and implications]
- **Unusual flow**: [Block trades — ticker, strike, expiry, size, bullish/bearish]
- **Institutional activity**: [Dark pool, insider activity]

---

## Stock Trade Plan

### Directional View: [Bullish / Bearish / Neutral with Conditions]

**Thesis** (3–4 sentences): [Clear rationale using live data]

**Entry:** Ideal $[XX.XX]–$[XX.XX] | Aggressive (chase): above $[XX.XX] | Patient (pullback): $[XX.XX]

**Targets:** T1 $[XX.XX] (+[X]%) → partial | T2 $[XX.XX] (+[X]%) → full thesis | Extended $[XX.XX] (+[X]%)

**Stop:** $[XX.XX] (-[X]%) — close if below this | Thesis stop: exit if [specific condition]

**Time Horizon:** [X days / weeks / months]

---

## Options Trade Plan

### Live Options Data (yfinance)
- ATM Call: $[XX.XX] strike — bid $[X.XX] / ask $[X.XX] → mid $[X.XX]
- ATM Put: $[XX.XX] strike — bid $[X.XX] / ask $[X.XX] → mid $[X.XX]
- **Implied move (straddle)**: $[X.XX] ([X]% of stock price)
- **Most liquid expiry**: [MM/DD/YY] (OI: [X,XXX] at ATM)

### Recommended Strategy: [e.g., Bull Call Spread]
**Why**: [1–2 sentences on why this fits current IV and directional view]

#### Primary Play:
$[TICKER] $[Strike][C/P] exp [MM/DD/YY] — Bid/Ask $[X.XX]/$[X.XX] → mid ~$[X.XX] | Cost ~$[XXX] | OI [X,XXX] | IV [XX]%
- Target exit: ~$[X.XX] (+[X]%) | Stop: ~$[X.XX] (-[X]%)

#### Alternative (Spread):
Buy $[Strike]C / Sell $[Strike]C exp [MM/DD/YY] — Net debit ~$[X.XX] | Max profit $[XXX] | Max loss $[XXX] | Breakeven $[XX.XX]

**IV level [XX]%**: [High → spreads / Low → single leg]
**Earnings in [X] weeks**: [Flag if within 2 weeks]
**Liquidity**: OI [X,XXX] — [liquid / thinly traded]

---

## Risk Assessment

**Bull case** ([X]%): $[XX.XX] — [what needs to happen]
**Base case** ([X]%): $[XX.XX] — [most likely]
**Bear case** ([X]%): $[XX.XX] — [what goes wrong]

**Top risks**: 1) [Specific] 2) [Specific] 3) [Macro if relevant]

---

> **Bottom line**: [1–2 sentences — bullish/bearish and why using live data]. [Recommended action]. [Most important thing to watch.]

---

## Data Quality Rules (Both Modes)

- **Every price and metric from live yfinance fetches** — no estimates, no prior session carryover
- **Options premiums use mid price** (bid + ask) / 2 from live chain
- **Flag illiquid options**: OI < 200 → suggest more liquid alternative
- **Earnings flag**: Earnings before expiration → flag prominently — changes entire risk profile
- **If any fetch fails**: Note explicitly and fall back to search with source attribution
- Keep tone like a sharp trading desk note — direct, specific, no fluff
