---
name: stock-ideas
description: Generate specific US stock trade ideas with entry prices, targets, and stop losses for both short-term and long-term trades. Use this skill whenever the user wants stock picks, a watchlist, investment ideas, sector plays, momentum trades, or asks "what should I buy/watch/trade". Triggers on: "stock ideas", "stock picks", "what should I buy", "give me ideas", "watchlist", "long term plays", "short term trades", "momentum stocks", "value plays", "growth stocks", "what to trade", "stock recommendations". Always include specific price levels — never vague direction only.
---

# Stock Ideas

Generate a curated list of specific stock trade ideas — both short-term trades and long-term positions — with exact entry, target, and stop levels pulled from live data.

This skill supports two modes:
- **Standard** (default): Single-pass scan using all three data sources
- **`--deep-analysis`**: Three parallel sub-agents independently score each ticker; only ideas with 2/3 or 3/3 signal agreement are presented

---

## `--deep-analysis` Mode

When the user includes `--deep-analysis` in their request, skip the standard flow below and run this instead.

### Overview

Spin up three sub-agents in parallel. Each pulls from a different data source and independently identifies candidate stocks. Only tickers where 2 or more agents flag a signal are surfaced as ideas. This ensures every recommendation has multi-source confirmation before being presented.

```
User: /stock-ideas --deep-analysis
           │
           ├── Agent 1: Fundamentals & Technicals (yfinance)
           ├── Agent 2: Smart Money Flow (Unusual Whales / Barchart / dark pool)
           └── Agent 3: Macro & Sector Context (CBOE / VIX / sector rotation)
           │
           ▼
     Signal Scoring per Ticker
     ┌─────────────────────────────────┐
     │ Fundamental signal?   ✅ or ❌  │
     │ Flow signal?          ✅ or ❌  │
     │ Macro/sector signal?  ✅ or ❌  │
     └─────────────────────────────────┘
           │
     3/3 → 🟢 High Conviction — Present
     2/3 → 🟡 Moderate Conviction — Present with caveats
     1/3 → Watchlist only
     0/3 → Discard silently
```

### Agent 1: Fundamentals & Technicals (yfinance)

This agent's job is to find stocks with strong price structure and fundamental momentum.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d&range=5d
https://query2.finance.yahoo.com/v10/finance/quoteSummary/TICKER?modules=defaultKeyStatistics,summaryDetail,financialData,calendarEvents,recommendationTrend
```

**Candidate sources:** Search `"momentum stocks today [date]"`, `"52 week high breakouts"`, `"analyst upgrades today [date]"`, `"earnings beat this week [date]"`

**Signal criteria — flag a ticker as ✅ Fundamental Signal if ANY of:**
- Price above 50-day AND 200-day MA (confirmed uptrend)
- Analyst consensus Buy with `targetMeanPrice` >10% above current price
- Revenue growth >10% YoY AND earnings growth >15% YoY
- Earnings beat within last 5 days and stock is holding or extending the move
- Fresh analyst upgrade with price target raise >15% today
- For bearish ideas: price below both MAs, analyst consensus Sell or Hold, earnings miss

**Output:** Ranked ticker list with Fundamental Signal ✅ or ❌, specific reason, live price, MA context, and analyst target from yfinance.

---

### Agent 2: Smart Money Flow (Unusual Whales / Barchart / Dark Pool)

This agent's job is to find stocks where institutional money is visibly moving today.

**Data to fetch via search:**
- `unusual options activity today [current date] stocks bullish bearish`
- `dark pool large block trades today [current date]`
- `institutional buying stocks today [current date]`
- `top stock movers today [current date] volume`

**Signal criteria — flag a ticker as ✅ Flow Signal if ANY of:**
- Large call sweep or block (>500 contracts OTM) detected on Unusual Whales today
- Dark pool print at a specific price level in unusually large size (accumulation signal)
- Institutional block trade in the equity (not just options) at above-average size
- Multiple separate large bullish options prints on the same ticker within one session
- For bearish ideas: large put sweeps, unusual put volume >5x daily average

**Classify each:**
- Bullish: call activity, equity accumulation, dark pool buy-side
- Bearish: put activity, dark pool sell-side, unusual short interest spike
- Note recency: same-day flow > yesterday's flow > this week's flow

**Output:** Ticker list with Flow Signal ✅ or ❌, specific trade details (size, strike if applicable, bullish/bearish), and recency.

---

### Agent 3: Macro & Sector Context (CBOE / VIX / Sector Rotation)

This agent's job is to assess whether the macro environment and sector rotation support the directional thesis.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^TNX?interval=1d&range=5d
```

Fetch sector ETF performance:
```
https://query1.finance.yahoo.com/v8/finance/chart/XLK?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/XLF?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/XLE?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/XLV?interval=1d&range=5d
```
(fetch all 11 SPDR sector ETFs)

Also search:
- `"sector rotation today" [current date]`
- `"leading sectors today" [current date]`
- `"macro outlook this week" [current date]`

**Signal criteria — flag a ticker as ✅ Macro/Sector Signal if ALL of:**
- The ticker's sector is in the LEADING group today (not lagging/risk-off)
- VIX direction supports the trade direction:
  - Bullish ideas: VIX ≤ 22 or falling (risk-on environment)
  - Bearish ideas: VIX > 22 or rising (risk-off environment)
- No major binary macro event (FOMC, CPI, jobs report) within the next 2 weeks that could override the thesis
- 10Y yield direction is not directly contradicting the thesis (e.g., rapidly rising yields = headwind for high-P/E growth stocks)

**Output:** Ticker list with Macro Signal ✅ or ❌, live VIX level, the ticker's sector performance today, and specific reason.

---

### Signal Scoring & Synthesis

After all three agents complete, build a scoring table:

| Ticker | Fundamental | Flow | Macro/Sector | Score | Conviction |
|--------|-------------|------|--------------|-------|------------|
| $XXXX | ✅ | ✅ | ✅ | 3/3 | 🟢 High |
| $XXXX | ✅ | ❌ | ✅ | 2/3 | 🟡 Moderate |
| $XXXX | ❌ | ✅ | ❌ | 1/3 | Watchlist only |

**Rules:**
- **3/3** → Present as full trade idea with 🟢 High Conviction badge
- **2/3** → Present as trade idea with 🟡 Moderate Conviction badge; note which signal was absent
- **1/3** → Watchlist section only — not tradeable yet
- **0/3** → Discard silently

Target **3–4 short-term** and **2–3 long-term** ideas passing 2/3+. If fewer pass the threshold, widen the candidate scan before lowering standards.

---

### Deep Analysis Output Format

---

## 🟢 Short-Term Trade — High Conviction (3/3) | $[TICKER] | [Company Name] | [Bullish/Bearish]

**Signal Confirmation:**
| Signal | Source | Detail |
|--------|--------|--------|
| ✅ Fundamental | yfinance | [e.g., "Above 50/200 MA, analyst target $XX (+X%), revenue +XX% YoY"] |
| ✅ Flow | Unusual Whales | [e.g., "X,XXX call sweep at $XX strike exp MM/DD, bullish, sweep"] |
| ✅ Macro/Sector | VIX/Sector | [e.g., "VIX at XX.X and falling, sector (XLK) up +X% leading today"] |

**Live Data** (yfinance):
- **Current Price**: $[XX.XX]
- **vs 50-Day MA**: $[XX.XX] ([X]% [above/below])
- **vs 200-Day MA**: $[XX.XX] ([X]% [above/below])
- **Analyst Target**: $[XX.XX] ([X]% upside) | Consensus: [Buy/Hold/Sell]
- **Next Earnings**: [Date] — [inside / outside trade window]

**Entry Zone**: $[XX.XX] – $[XX.XX]
**Target**: $[XX.XX] (+[X]%)
**Stop Loss**: $[XX.XX] (-[X]%)
**Time Horizon**: [X days / X weeks]

**Thesis**: [2–3 sentences synthesizing all three signal sources into a unified rationale]

**Catalyst**: [Most important near-term trigger]
**Risk**: [What breaks the trade / which signal reversal to watch]

---

## 🟡 Short-Term Trade — Moderate Conviction (2/3) | $[TICKER] | [Bullish/Bearish]

**Signal Confirmation:**
| Signal | Source | Detail |
|--------|--------|--------|
| ✅ [Signal] | [Source] | [Detail] |
| ✅ [Signal] | [Source] | [Detail] |
| ❌ [Signal] | [Source] | [Why absent — what would need to change to confirm] |

[Same trade template]

**Note on missing signal**: [What would upgrade this to 3/3 and what would invalidate it]

---

## 🟢 Long-Term Position — High Conviction (3/3) | $[TICKER] | [Company Name] | [Bullish]

**Signal Confirmation:**
| Signal | Source | Detail |
|--------|--------|--------|
| ✅ Fundamental | yfinance | [Revenue/earnings growth, valuation, analyst consensus] |
| ✅ Flow | Dark pool / Unusual Whales | [Institutional accumulation evidence] |
| ✅ Macro/Sector | VIX/Sector | [Structural tailwind, sector leading, macro supportive] |

**Live Data** (yfinance):
- **Current Price**: $[XX.XX]
- **vs 52-Week High**: -[X]% ($[XX.XX] high)
- **vs 200-Day MA**: $[XX.XX] ([X]% [above/below])
- **Analyst Target**: $[XX.XX] ([X]% upside) | Consensus: [Buy/Hold/Sell]
- **Next Earnings**: [Date]

**Entry Zone**: $[XX.XX] – $[XX.XX] (scale in over 2–3 weeks)
**12-Month Target**: $[XX.XX] (+[X]%)
**Stop Loss / Thesis Invalidation**: $[XX.XX] (-[X]%) or if [specific condition]
**Time Horizon**: [X months / X years]

**Investment Thesis**: [3–4 sentences synthesizing all three signal sources]

**Key Metrics** (yfinance):
- Revenue growth: [X]% YoY | Earnings growth: [X]% YoY
- Forward P/E: [X]x | P/S: [X]x
- Next earnings: [Date]

**Risks**: [1–2 specific risks]

---

### Deep Analysis Watchlist (1/3 Signals Only)

| Ticker | Live Price | Signal Present | Missing | Watch For |
|--------|-----------|----------------|---------|-----------|
| $XXXX | $[XX.XX] | [Which signal ✅] | [Which signals ❌] | [Specific trigger to upgrade] |

---

## Standard Mode (Default — No `--deep-analysis` Flag)

### Step 1: Pull Live Market Data (Run ALL in Parallel)

#### A. yfinance — Live Prices, Fundamentals & Technicals

```
https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query2.finance.yahoo.com/v10/finance/quoteSummary/TICKER?modules=defaultKeyStatistics,summaryDetail,financialData,calendarEvents,recommendationTrend
```

**Extract:** `regularMarketPrice`, `fiftyDayAverage`, `twoHundredDayAverage`, `fiftyTwoWeekHigh`, `fiftyTwoWeekLow`, `trailingPE`, `forwardPE`, `revenueGrowth`, `earningsGrowth`, `recommendationMean`, `targetMeanPrice`, `earningsDate`

#### B. Unusual Whales / Barchart — Institutional Flow

- Search: `unusual options activity today [current date] stocks bullish`
- Search: `dark pool large trades today [current date]`
- Search: `analyst upgrades downgrades today [current date]`

#### C. CBOE / VIX — Market Sentiment & Sector Rotation

```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
```
Search: `"sector performance today" "leading sectors" [current date]`

### Step 2: Build Market Context

1. VIX level & direction → rising = defensive, falling = momentum/growth
2. SPY trend → trending up (breakouts), down (shorts/bounces), choppy (mean reversion)
3. Leading sectors → weight ideas toward these
4. Smart money flow → unusual accumulation names
5. Earnings calendar → flag any idea with earnings within 2 weeks

### Step 3: Find Ideas

**Short-term**: Momentum breakouts (above-avg volume), earnings runners (beat within 3 days), analyst upgrades (>15% target raise), unusual flow alignment.

**Long-term**: Sector tailwinds, beaten-down quality (revenue growth still positive), accelerating earnings (>15% growth), rising analyst targets (>20% upside).

### Step 4: Validate with yfinance

Confirm: price vs MAs, analyst target vs price, earnings date, valuation. Fall back to Finviz if yfinance fails.

### Step 5: Present Ideas

---

## Short-Term Trades (Days to Weeks)

### [#]. $[TICKER] — [Company Name] | [Bullish/Bearish]

**Live Data** (yfinance):
- **Current Price**: $[XX.XX] | **vs 50-Day MA**: $[XX.XX] ([X]% [above/below]) | **vs 200-Day MA**: $[XX.XX] ([X]% [above/below])
- **Analyst Target**: $[XX.XX] ([X]% upside) | Consensus: [Buy/Hold/Sell]
- **Next Earnings**: [Date] — [inside / outside trade window]

**Entry Zone**: $[XX.XX] – $[XX.XX] | **Target**: $[XX.XX] (+[X]%) | **Stop Loss**: $[XX.XX] (-[X]%)
**Time Horizon**: [X days / X weeks]

**Thesis**: [2–3 sentences] | **Catalyst**: [Specific] | **Risk**: [What breaks it]

---

## Long-Term Positions (Months to Years)

### [#]. $[TICKER] — [Company Name] | [Bullish/Bearish]

**Live Data** (yfinance):
- **Current Price**: $[XX.XX] | **vs 52-Week High**: -[X]% | **vs 200-Day MA**: $[XX.XX] ([X]% [above/below])
- **Analyst Target**: $[XX.XX] ([X]% upside) | **Next Earnings**: [Date]

**Entry Zone**: $[XX.XX] – $[XX.XX] | **12-Month Target**: $[XX.XX] (+[X]%) | **Stop**: $[XX.XX] (-[X]%)
**Time Horizon**: [X months / X years]

**Investment Thesis**: [3–4 sentences]

**Key Metrics**: Revenue growth [X]% | Earnings growth [X]% | Forward P/E [X]x | P/S [X]x

**Risks**: [1–2 specific risks]

---

### Step 6: Watchlist

| Ticker | Live Price | Why Watching | Trigger to Act |
|--------|-----------|-------------|----------------|
| $XXXX | $[XX.XX] | [Brief reason] | [Specific condition] |

### Step 7: Market Context Summary

**S&P 500**: [XX,XXX] ([+/-X]%) | **VIX**: [XX.X] | **Leading**: [sectors] | **Lagging**: [sectors] | **Bias**: [Bullish/Bearish/Cautious]

---

## Data Quality Rules (Both Modes)

- **Live yfinance prices only** — never carry over from prior sessions
- **Flag failed fetches** explicitly with fallback source noted
- **Earnings flag**: Binary risk event within trade window — always flag in bold
- **MA confirmation**: Bullish short-term trades prefer above 50-day MA; long-term prefer above 200-day
- **Analyst consensus**: Flag if `targetMeanPrice` is below current price for a long idea

## Position Sizing Guidance

> **Position sizing**: For short-term trades, risk no more than 1–2% of portfolio per idea. For long-term positions, 3–5% per position. Never size so large that a stop-out materially damages your portfolio.
