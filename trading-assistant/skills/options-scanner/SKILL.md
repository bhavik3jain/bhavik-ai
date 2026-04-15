---
name: options-scanner
description: Find specific US options trade ideas with exact strikes, expirations, and premiums. Use this skill whenever the user asks about options trades, earnings plays, calls/puts, spreads, straddles, unusual options activity, IV crush plays, or any options strategy. Triggers on: "options play", "options ideas", "earnings trade", "call options", "put options", "IV play", "options strategy", "what options should I buy", "options scanner", "unusual activity", "credit spread", "iron condor", "covered call", "wheel strategy". Be specific — always give ticker, strike, expiration, and approximate cost.
---

# Options Scanner

Find and present specific, actionable options trades with real live data. Every recommendation must include exact contract details pulled from live sources — no estimated prices, no guesses.

This skill supports two modes:
- **Standard** (default): Single-pass scan using all three data sources sequentially
- **`--deep-analysis`**: Three parallel sub-agents independently score each ticker; only ideas with 2/3 or 3/3 signal agreement are presented

---

## `--deep-analysis` Mode

When the user includes `--deep-analysis` in their request, skip the standard flow below and run this instead.

### Overview

Spin up three sub-agents in parallel. Each agent pulls from a different data source and independently scores candidate tickers. Only tickers where 2 or more agents flag a signal are surfaced as trade ideas. This filters out noise and ensures every recommendation has multi-source confirmation.

```
User: /options-scanner --deep-analysis
           │
           ├── Agent 1: Fundamentals & Technicals (yfinance)
           ├── Agent 2: Smart Money Flow (Unusual Whales / Barchart)
           └── Agent 3: Volatility & Macro (CBOE / VIX / Sector)
           │
           ▼
     Signal Scoring per Ticker
     ┌─────────────────────────────────┐
     │ Fundamental signal?   ✅ or ❌  │
     │ Flow signal?          ✅ or ❌  │
     │ Volatility signal?    ✅ or ❌  │
     └─────────────────────────────────┘
           │
     3/3 → 🟢 High Conviction — Present
     2/3 → 🟡 Moderate Conviction — Present with caveats
     1/3 → Watchlist only (do not present as a trade)
     0/3 → Discard silently
```

### Agent 1: Fundamentals & Technicals (yfinance)

This agent's job is to find options candidates with strong fundamental and technical setups.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d&range=5d
https://query2.finance.yahoo.com/v10/finance/quoteSummary/TICKER?modules=defaultKeyStatistics,summaryDetail,financialData,calendarEvents,recommendationTrend
https://query1.finance.yahoo.com/v7/finance/options/TICKER
```

**Candidate sources:** Search `"momentum stocks today"`, `"52 week high breakouts"`, `"earnings this week [date]"`, `"analyst upgrades today [date]"`

**Signal criteria — flag a ticker as ✅ Fundamental Signal if ANY of:**
- Stock is above its 50-day AND 200-day MA (bullish technical structure)
- Analyst consensus is Buy with `targetMeanPrice` >10% above current price
- Revenue growth >10% YoY AND earnings growth >15% YoY (fundamental momentum)
- Stock beat earnings within last 5 days and is holding the post-earnings move
- Fresh analyst upgrade with price target raise >15% today

**Options validation from yfinance chain:**
- ATM contract OI > 500 (liquid enough to trade)
- Bid/ask spread < 20% of mid price
- Extract real bid/ask mid price for each candidate

**Output:** A ranked list of tickers with Fundamental Signal ✅ or ❌, including the specific reason for the signal and live yfinance price/IV data.

---

### Agent 2: Smart Money Flow (Unusual Whales / Barchart)

This agent's job is to find options candidates where institutional money is actively positioning today.

**Data to fetch via search:**
- `unusual options activity today [current date] site:unusualwhales.com OR barchart.com`
- `options flow sweep block trades [current date] bullish`
- `dark pool large trades today [current date]`
- `"unusual options" [current date] calls puts premium`

**Signal criteria — flag a ticker as ✅ Flow Signal if ANY of:**
- Sweep trade: large call/put order hitting multiple exchanges simultaneously (urgency signal)
- Block trade: single print >500 contracts at a strike that is OTM (directional conviction)
- Dark pool print: large size at a specific price level (accumulation signal)
- Call/put volume >5x the normal daily average on a specific strike
- Multiple separate large trades on the same ticker and direction within one session

**Classify each flow signal:**
- Bullish: call sweeps, OTM call blocks, large call volume
- Bearish: put sweeps, OTM put blocks, large put volume
- Ambiguous: mixed or near-ATM activity (note but don't classify strongly)

**Output:** A list of tickers with Flow Signal ✅ or ❌, including the specific trade details (strike, expiry, size, sweep/block, bullish/bearish classification).

---

### Agent 3: Volatility & Macro (CBOE / VIX / Sector)

This agent's job is to assess whether the volatility environment and macro setup favor the trade direction and strategy.

**Data to fetch:**
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^VIX9D?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^VXN?interval=1d&range=5d
```

Also search:
- `"CBOE put call ratio today" [current date]`
- `"sector performance today" leading lagging [current date]`
- `"earnings calendar this week" [current date]`
- `"VIX term structure" OR "volatility regime" [current date]`

**Signal criteria — flag a ticker as ✅ Volatility Signal if ALL of the following apply:**
- VIX environment matches the proposed strategy:
  - For debit/buying plays: VIX ≤ 20 (cheap premium) OR VIX falling (risk-on)
  - For credit/selling plays: VIX ≥ 20 (elevated premium to collect)
- Ticker's sector is NOT in the lagging/risk-off category today (don't fight sector headwinds)
- No binary macro event (FOMC, CPI, jobs report) falls within the trade's expiration window that would create unquantifiable risk
- If an earnings event falls before expiration: only ✅ if that earnings is intentionally part of the thesis (straddle/strangle play) — otherwise ❌

**Output:** A list of tickers with Volatility Signal ✅ or ❌, plus the current VIX level, put/call ratio, and the specific reason for each signal.

---

### Signal Scoring & Synthesis

After all three agents complete, score each ticker:

| Ticker | Fundamental | Flow | Volatility | Score | Conviction |
|--------|-------------|------|------------|-------|------------|
| $XXXX | ✅ | ✅ | ✅ | 3/3 | 🟢 High |
| $XXXX | ✅ | ❌ | ✅ | 2/3 | 🟡 Moderate |
| $XXXX | ✅ | ❌ | ❌ | 1/3 | Watchlist only |
| $XXXX | ❌ | ❌ | ❌ | 0/3 | Discard |

**Rules:**
- **3/3** → Present as a full trade idea with 🟢 High Conviction badge
- **2/3** → Present as a trade idea with 🟡 Moderate Conviction badge, note which signal was absent and why
- **1/3** → Add to watchlist section only — do not present as a tradeable idea
- **0/3** → Discard silently

Aim to surface **3–5 trade ideas** (mix of 3/3 and 2/3). If fewer than 3 ideas pass the 2/3 threshold, expand the candidate scan before lowering standards.

---

### Deep Analysis Output Format

Present each passing trade using the standard template below, prefixed with the conviction badge and signal table.

---

### 🟢 Trade [#] — High Conviction (3/3) | $[TICKER] | [Bullish/Bearish/Neutral]

**Signal Confirmation:**
| Signal | Source | Detail |
|--------|--------|--------|
| ✅ Fundamental | yfinance | [e.g., "Above 50/200 MA, analyst target $XX (+X%), earnings growth +XX%"] |
| ✅ Flow | Unusual Whales | [e.g., "$XXX call sweep, X,XXX contracts, exp MM/DD, bullish"] |
| ✅ Volatility | CBOE/VIX | [e.g., "VIX at XX.X (falling), sector leading, no binary events before expiry"] |

**Strategy**: [e.g., Bull Call Spread]

**Contract**: $[TICKER] $[Strike]C / $[Strike]C exp [MM/DD/YY]

**Live Data** (yfinance):
- Stock price: $[XX.XX]
- Bid / Ask: $[X.XX] / $[X.XX] → Entry at mid: ~$[X.XX]
- Cost per contract: ~$[XXX]
- Open interest: [X,XXX] | Volume today: [XXX]
- Contract IV: [XX]%
- Next earnings: [Date] ([before/after] expiration)

**Max Profit**: $[XXX] | **Max Loss**: $[XXX] | **Breakeven**: $[XX.XX]

**Thesis**: [2–3 sentences synthesizing all three signal sources into a unified trade rationale]

**Exit Plan**:
- Take profit: [50–75% of max profit / specific price target]
- Stop loss: [25–50% of premium paid]
- Time stop: Exit by [date] if thesis isn't playing out

**Risk Level**: [Low / Medium / High]

---

### 🟡 Trade [#] — Moderate Conviction (2/3) | $[TICKER] | [Bullish/Bearish/Neutral]

**Signal Confirmation:**
| Signal | Source | Detail |
|--------|--------|--------|
| ✅ [Signal name] | [Source] | [Detail] |
| ✅ [Signal name] | [Source] | [Detail] |
| ❌ [Signal name] | [Source] | [Why absent — e.g., "No unusual flow detected today; watching for confirmation"] |

[Same trade template as above]

**Note on missing signal**: [1 sentence on what would upgrade this to 3/3 and what would invalidate it]

---

### Deep Analysis Watchlist (1/3 Signals)

| Ticker | Live Price | Signal Present | Missing | Watch For |
|--------|-----------|----------------|---------|-----------|
| $XXXX | $[XX.XX] | [Which signal ✅] | [Which signals ❌] | [Specific trigger to upgrade to trade] |

---

## Standard Mode (Default — No `--deep-analysis` Flag)

### Step 1: Pull Live Market Data (Run ALL in Parallel)

#### A. yfinance — Live Quotes, Options Chains & IV

Fetch live VIX and S&P 500 data:
```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?interval=1d&range=5d
```

For each candidate ticker, fetch the full options chain:
```
https://query1.finance.yahoo.com/v7/finance/options/TICKER
```

Fetch fundamentals and next earnings date:
```
https://query2.finance.yahoo.com/v10/finance/quoteSummary/TICKER?modules=defaultKeyStatistics,calendarEvents,financialData
```

**Extract from yfinance:**
- `regularMarketPrice` — exact current stock price
- `impliedVolatility` per contract — real IV, not estimated
- `bid` and `ask` per contract — use mid ((bid+ask)/2) as entry price
- `openInterest` and `volume` — filter out illiquid contracts (OI < 200 = skip)
- `earningsDate` from calendarEvents — flag if earnings fall before expiration
- `fiftyDayAverage`, `twoHundredDayAverage` — technical context

#### B. Unusual Whales / Barchart — Smart Money Options Flow

- Search: `unusual options activity today [current date] site:unusualwhales.com OR barchart.com`
- Search: `options flow large block trades [current date]`
- Search: `"unusual options" [current date] sweep bullish bearish`

**Extract:** Ticker, strike, expiration, call/put, premium, bullish/bearish flag, sweep vs block.

#### C. CBOE — VIX Level & Put/Call Ratio

```
https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d
https://query1.finance.yahoo.com/v8/finance/chart/^VXN?interval=1d&range=5d
```

Also search: `"CBOE put call ratio today" OR "equity put call ratio [current date]"`

### Step 2: Determine Options Environment

| VIX Level | Environment | Strategy Bias |
|-----------|-------------|---------------|
| < 15 | Low vol | Buy calls/puts, debit spreads — premium is cheap |
| 15–20 | Normal | Balanced — spreads and directional plays both work |
| 20–25 | Elevated | Favor credit spreads; single-leg buys need strong conviction |
| 25–35 | High fear | Sell premium — iron condors, cash-secured puts, credit spreads |
| > 35 | Extreme fear | Sell puts on quality names; avoid buying premium |

### Step 3: Scan for Trade Ideas Across 5 Categories

**Category 1 — Unusual Flow Plays**: Large aggressive block trades today; validate OI > 500 and bid/ask spread < 20% of mid.

**Category 2 — Earnings Plays**: Stocks reporting within 3–5 days; compare ATM straddle cost vs historical post-earnings move to determine buy vs sell IV.

**Category 3 — Momentum Breakout**: Stocks at key technical levels from news/Finviz; use yfinance for most liquid strike/expiry.

**Category 4 — High IV Rank Premium Selling**: IV Rank > 60%, NOT within 2 weeks of earnings; sell OTM puts or call spreads.

**Category 5 — Post-Earnings Cheap Premium**: Reported within 1–3 days, IV collapsed, stock holding move; debit spreads are cheap.

### Step 4: Validate Each Trade with Live yfinance Data

1. Fetch options chain: `https://query1.finance.yahoo.com/v7/finance/options/TICKER`
2. Extract real bid/ask → use mid price as entry
3. Confirm OI > 200 (prefer > 1,000 for weeklies)
4. Check IV on the specific contract
5. Confirm earnings date vs expiration

**If yfinance fetch fails**: Fall back to web search and flag: "Live data unavailable — pricing is estimated."

### Step 5: Present Trade Ideas

Present **4–5 specific options trades**:

---

### Trade [#]: [Bullish/Bearish/Neutral] — $[TICKER] | [Company Name]

**Strategy**: [e.g., Long Call / Bull Call Spread / Short Put / Earnings Straddle / Iron Condor]

**Contract**: $[TICKER] $[Strike][C/P] exp [MM/DD/YY]
- *For spreads*: Buy $[Strike]C / Sell $[Strike]C exp [MM/DD/YY]

**Live Data** (yfinance):
- Stock price: $[XX.XX]
- Bid / Ask: $[X.XX] / $[X.XX] → Entry at mid: ~$[X.XX]
- Cost per contract: ~$[XXX] (100 shares)
- Open interest: [X,XXX] | Volume today: [XXX]
- Contract IV: [XX]%
- Next earnings: [Date] ([before/after] this expiration)

**Max Profit**: $[XXX] | **Max Loss**: $[XXX] | **Breakeven at expiry**: $[XX.XX]

**Thesis** (2–3 sentences): [Why this trade makes sense RIGHT NOW. What the catalyst is. What the live data confirms.]

**Flow Signal** (if applicable): [Unusual Whales / Barchart block trade details]

**Exit Plan**:
- Take profit: [50–75% of max profit for spreads / specific $ target for long options]
- Stop loss: [25–50% loss on premium paid]
- Time stop: Exit by [specific date] if thesis isn't playing out

**Risk Level**: [Low / Medium / High]

---

### Step 6: Options Environment Summary

### Options Environment — [Date]

**Live Data** (yfinance + CBOE):
- **VIX**: [XX.X] ([↑/↓ X% today]) — [Low/Normal/Elevated/High fear]
- **Put/Call Ratio**: [X.XX] — [fearful / neutral / complacent]
- **VXN (Nasdaq vol)**: [XX.X]
- **Strategy Bias**: [Buying debit spreads / Selling premium / Balanced]

**Best strategies right now**: [1–2 sentences]

**Watch out for**: [Upcoming binary events that could disrupt open positions]

---

## Data Quality Rules (Both Modes)

- **Use real yfinance numbers** — never carry over yesterday's levels or estimate
- **Flag failed fetches** explicitly — note pricing is estimated if live data unavailable
- **Liquidity check**: OI < 200 or bid/ask spread > 30% of mid = flag as illiquid
- **Earnings flag**: Always check — flag any trade where earnings fall before expiration
- **Mid price rule**: Always use (bid + ask) / 2 as entry estimate, not ask price

## Options Strategy Quick Reference

| Scenario | Strategy |
|----------|----------|
| Strong bullish conviction, low IV | Long call |
| Bullish, IV normal or high | Bull call spread |
| Mildly bullish | Bull put spread (sell put spread) |
| Strong bearish conviction, low IV | Long put |
| Bearish, IV normal or high | Bear put spread |
| Mildly bearish | Bear call spread |
| Big move expected, direction unclear | Long straddle / strangle |
| Small move expected, range-bound | Iron condor / short strangle |
| Bullish long-term, want income | Cash-secured put or covered call |
| Before earnings, IV elevated | Sell straddle/strangle or iron condor |
| After earnings, IV collapsed | Buy debit spreads cheaply |

## Important Notes

- Always specify **monthly or weekly** expiration clearly
- For earnings plays, state explicitly whether the trade is **before** or **after** the report
- Flag binary events (FDA, court ruling, Fed meeting) within the expiration window
- Options can expire worthless — size to risk no more than **1–2% of portfolio per trade**
- Unusual Whales flow is a signal, not a guarantee — always pair with your own thesis
