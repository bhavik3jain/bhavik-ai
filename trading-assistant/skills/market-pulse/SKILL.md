---
name: market-pulse
description: Daily US market overview and macro snapshot. Use this skill when the user wants to know what the market is doing, pre-market conditions, sector performance, macro backdrop, VIX/fear gauge, Fed calendar, or overall market sentiment. Triggers on: "market pulse", "what's the market doing", "market overview", "how's the market", "pre-market", "sector rotation", "macro conditions", "market today", "market sentiment". Always use this before generating trade ideas so you have proper market context.
---

# Market Pulse

Deliver a fast, actionable daily market snapshot. The goal is to give the user everything they need to understand the current market environment in 2-3 minutes of reading.

## Step 1: Fetch Live Data

Search and fetch the following before writing anything:

**Indices** (search for current prices/% change):
- SPY / S&P 500
- QQQ / Nasdaq 100
- IWM / Russell 2000
- DIA / Dow Jones

**Market Internals**:
- VIX (fear index) — is it above/below 20? Above 25 is elevated fear
- Put/Call ratio
- 10-year Treasury yield (^TNX)

**Sectors** — search for today's top/bottom performing S&P sectors:
- XLK (Tech), XLF (Financials), XLE (Energy), XLV (Healthcare)
- XLI (Industrials), XLC (Comms), XLY (Consumer Disc), XLP (Consumer Staples)

**Key News** — web search for:
- "stock market news today [current date]"
- Any Fed speakers or FOMC events this week
- Major earnings reports today/this week

## Step 2: Write the Market Pulse Report

Use this exact structure:

---

## Market Pulse — [Date]

### Indices
| Index | Price | Change | % Change |
|-------|-------|--------|----------|
| S&P 500 (SPY) | ... | ... | ...% |
| Nasdaq (QQQ) | ... | ... | ...% |
| Russell 2000 (IWM) | ... | ... | ...% |
| Dow (DIA) | ... | ... | ...% |

### Market Internals
- **VIX**: [value] — [Low/Moderate/Elevated/Extreme] fear ([interpretation])
- **10Y Treasury**: [yield]% — [Rising/Falling/Stable] ([impact on growth stocks])
- **Market Trend**: [Bullish/Bearish/Neutral/Choppy] based on internals

### Sector Snapshot
**Leading** (buy side): [top 2-3 sectors with % gains]
**Lagging** (avoid/short side): [bottom 2-3 sectors with % losses]

### Key Catalysts Today
- [Bullet 1: Most important news item with market impact]
- [Bullet 2: Second most important]
- [Bullet 3: Earnings/economic data]

### Fed & Macro Watch
- [Fed speakers today, FOMC dates, rate expectations]
- [Any macro data: CPI, jobs, GDP releases this week]

### Market Bias
**Overall**: [Bullish / Bearish / Neutral] — [1-2 sentence thesis explaining why]

**Best setups today**: [Long / Short / Mixed] — [which sectors/themes are working]

---

## Step 3: Flag Actionable Themes

After the report, add a "Today's Themes" section — 2-3 bullet points on what's driving price action and what that means for trade ideas:

**Today's Themes:**
- [Theme 1]: e.g., "Tech selling off on rate fears → consider puts on QQQ or defensive rotation into XLP"
- [Theme 2]: e.g., "Energy ripping on oil supply cut → momentum longs in XOM, CVX, OXY"
- [Theme 3]: e.g., "VIX spike → elevated premiums make selling options attractive"

These themes should directly set up ideas for `/options-scanner` or `/stock-ideas` if the user wants to go deeper.
